#!/usr/bin/env python3
"""
Iterative Self-RAG loop with multiple retrievers:
- physicians # may need an update in your team environment
- hospitals  # needs to be created
Proxy-aware version using urllib + localhost:8088
"""

import os, json, urllib.request
import psycopg2

# ----------------------------
# CONFIG
# ----------------------------
DB_NAME = "rag_teamX"   # <-- change
DB_USER = "teamX"       # <-- change
DB_PASS = "YOUR_TEAM_POSTGRE_PSWD"   # <-- change
DB_HOST = "localhost"
DB_PORT = "5432"

OPENAI_PROXY = os.getenv("OPENAI_PROXY_URL", "http://127.0.0.1:8088")
TEAM_ID      = os.getenv("TEAM_ID", "team0X") # <-- change

# ----------------------------
# PROXY HELPERS
# ----------------------------
def _post_openai(endpoint: str, payload: dict):
    """Helper to POST JSON payloads to proxy."""
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if TEAM_ID:
        headers["X-Team"] = TEAM_ID

    req = urllib.request.Request(
        f"{OPENAI_PROXY}{endpoint}",
        data=data,
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

# ----------------------------
# EMBEDDING HELPER
# ----------------------------
def embed_text(text: str, model="text-embedding-3-large"):
    payload = {"model": model, "input": text}
    data = _post_openai("/v1/embeddings", payload)
    return (data.get("data") or [{}])[0].get("embedding", [])

# ----------------------------
# GENERIC SEMANTIC SEARCH
# ----------------------------
def semantic_search(table: str, user_query: str, top_k: int = 3):
    """Search a given table (physicians or hospitals)"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    query_embedding = embed_text(user_query)

    if table == "physicians":
        cur.execute(
            """
            SELECT id, name, specialty, city, state, profile,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM physicians
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, top_k)
        )
    elif table == "hospitals":
        cur.execute(
            """
            SELECT id, name, city, state, description,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM hospitals
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, top_k)
        )
    else:
        raise ValueError(f"Unknown table: {table}")

    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

# ----------------------------
# CHATGPT MESSAGE HELPER
# ----------------------------
def chat(messages, model="gpt-4.1", max_tokens=300):
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    data = _post_openai("/v1/chat/completions", payload)
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

# ----------------------------
# MAIN SELF-RAG LOOP
# ----------------------------
def run_self_rag(user_query: str):
    messages = [
        {"role": "system", "content": """
You are a healthcare lookup assistant with access to:
- Physicians database
- Hospitals database

Rules:
- If you need database context, respond ONLY with:
  NEED_RETRIEVAL: <table> | <search query>
- Valid tables are: physicians, hospitals
- You may request multiple retrievals in sequence.
- When satisfied, respond with:
  FINAL_ANSWER: <grounded answer with citations>
"""}
    ]
    messages.append({"role": "user", "content": user_query})

    while True:
        reply = chat(messages)
        print("\nChatGPT Reply:")
        print("=" * 60)
        print(reply)

        if reply.startswith("NEED_RETRIEVAL:"):
            try:
                _, payload = reply.split(":", 1)
                table, search_query = payload.strip().split("|", 1)
                table = table.strip()
                search_query = search_query.strip()

                print(f"\n[System] Running semantic search on '{table}' for: {search_query}")
                matches = semantic_search(table, search_query, top_k=3)

                # Format retrieved results differently for each table
                if table == "physicians":
                    context = "\n\n".join([
                        f"[{table.upper()} ID:{row[0]}] {row[1]} ({row[2]}, {row[3]}, {row[4]}): {row[5]}"
                        for row in matches
                    ])
                elif table == "hospitals":
                    context = "\n\n".join([
                        f"[{table.upper()} ID:{row[0]}] {row[1]} ({row[2]}, {row[3]}): {row[4]}"
                        for row in matches
                    ])
                else:
                    context = "No results."

                followup = f"Retrieved results for {table}:\n\n{context}"
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content": followup})
                continue
            except Exception as e:
                print(f"[System] Parse error: {e}")
                break

        elif reply.startswith("FINAL_ANSWER:"):
            print("\nFinal Answer:")
            print("=" * 60)
            print(reply.replace("FINAL_ANSWER:", "").strip())
            break
        else:
            print("\n[System] Unexpected response. Stopping.")
            break

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    user_query = "Which hospital in Georgia is best for arrhythmia, and which doctor there could I see?"
    run_self_rag(user_query)