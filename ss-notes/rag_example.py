#!/usr/bin/env python3
"""
Iterative Self-RAG loop with multiple retrievers:
- physicians
- hospitals
"""

import psycopg2
from openai import OpenAI

# ----------------------------
# CONFIG
# ----------------------------
DB_NAME = "rag_teamX"   # <-- change
DB_USER = "teamX" # <-- change
DB_PASS = "YOUR_TEAM_POSTGRE_PSWD"   # <-- change
DB_HOST = "localhost"
DB_PORT = "5432"

client = OpenAI()

# ----------------------------
# EMBEDDING HELPER
# ----------------------------
def embed_text(text: str):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-large"  # matches vector(3072)
    )
    return response.data[0].embedding

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
def chat(messages):
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages,
        max_tokens=300
    )
    return response.choices[0].message.content

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

