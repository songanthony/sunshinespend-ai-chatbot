# Physician License Lookup Aggregator (Starter Kit)

This starter project gives you a **single command** to search physician licensing info **nationwide** by querying a central aggregator (FSMB DocInfo) and (optionally) specific state boards via pluggable adapters.

> ⚠️ **Important**: Each site has its own Terms of Use and anti-bot measures. Use responsibly. Some boards require manual searches, CAPTCHAs, or do not permit scraping. This toolkit is for **internal evaluation**; adapt it to your organization’s compliance policies.

## What it does
- Searches **DocInfo.org** (FSMB) for a physician by name and *parses* top matches (name, degree, states of licensure, profile link).
- Generates a tidy CSV/XLSX with results.
- Provides **adapters** you can implement per-state when a reliable workflow is feasible.
- Lets you pass a list of states to target (e.g., only CA, FL, TX).

## Quick start

1) **Install dependencies** (ideally in a virtualenv):
```bash
pip install -r requirements.txt
python -m playwright install
```

2) **Run a name search** (DocInfo aggregator only):
```bash
python app.py --first "john" --last "smith" --out results.xlsx
```

3) **Include (sample) state adapters** (still experimental):
```bash
python app.py --first "john" --last "smith" --states "FL,TX" --out results.xlsx
```

The output file lists results per adapter, with normalized columns.

## Architecture

- `app.py` – CLI entry point. Coordinates searches across adapters and saves output.
- `adapters/docinfo.py` – Functional scraper for DocInfo.org (best effort). No official API.
- `adapters/florida.py` – **Stub** showing how to automate FL MQA portal with Playwright.
- `adapters/texas.py` – **Stub** showing a Playwright flow outline for TX TMB.
- `adapters/base.py` – Base adapter class, common utilities.
- `data/state_urls.json` – JSON with each state’s primary verification URL.

## Caveats / Next steps
- **HTML changes** on source sites can break parsers; adjust selectors as needed.
- Some states enforce **CAPTCHAs or session tokens**; these stubs show the general approach, but you may need to add human-in-the-loop steps.
- For production, add: retries, rate limiting, proxy rotation, robust logging, and result validation.
- Consider using the **NPI Registry API** to pre‑narrow candidates by name/ZIP/specialty before hitting verification sites.

## Legal & Ethical
Use this only where permitted. You’re responsible for compliance with website terms, privacy rules, and credentialing/verification policies.
