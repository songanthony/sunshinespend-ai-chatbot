import argparse
import json
import pandas as pd
import requests

from adapters.docinfo import DocInfoAdapter
from adapters.florida import FloridaAdapter
from adapters.texas import TexasAdapter

ADAPTERS = {
    "docinfo": DocInfoAdapter,
    "FL": FloridaAdapter,
    "TX": TexasAdapter,
}

def run_search(first: str, last: str, middle: str, states: list, out_path: str):
    session = requests.Session()
    rows = []

    # Always do DocInfo first to help narrow matches
    docinfo = DocInfoAdapter(session)
    for item in docinfo.search(first=first, last=last, middle=middle):
        rows.append(item)

    # Per-state adapters (only stubs included by default)
    for st in states:
        cls = ADAPTERS.get(st.strip().upper())
        if not cls:
            continue
        adapter = cls(session)
        for item in adapter.search(first=first, last=last, middle=middle, state=st):
            rows.append(item)

    if not rows:
        print("No results found. Try adjusting your name inputs or add state adapters.")
        return

    # Normalize & save
    df = pd.DataFrame(rows)
    # Ensure columns exist
    for col in ["source","full_name","degree","states","license_number","status","profile_url","board_name"]:
        if col not in df.columns:
            df[col] = ""

    df = df[["source","full_name","degree","states","license_number","status","profile_url","board_name"]]
    if out_path.lower().endswith(".csv"):
        df.to_csv(out_path, index=False)
    else:
        df.to_excel(out_path, index=False)
    print(f"Saved: {out_path}")

def main():
    parser = argparse.ArgumentParser(description="Physician license aggregator (starter)")
    parser.add_argument("--first", required=True, help="First name (case-insensitive)")
    parser.add_argument("--last", required=True, help="Last name (case-insensitive)")
    parser.add_argument("--middle", default="", help="Middle name or initial")
    parser.add_argument("--states", default="", help="Comma-separated state codes to include (e.g., 'FL,TX')")
    parser.add_argument("--out", default="results.xlsx", help="Output file (.xlsx or .csv)")
    args = parser.parse_args()

    states = [s for s in args.states.split(",") if s.strip()] if args.states else []
    run_search(args.first, args.last, args.middle, states, args.out)

if __name__ == "__main__":
    main()
