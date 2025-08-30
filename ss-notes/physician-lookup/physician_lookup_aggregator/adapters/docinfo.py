import re
import time
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from .base import BaseAdapter

class DocInfoAdapter(BaseAdapter):
    """
    Best-effort HTML scraper for DocInfo.org search results.
    There is no public API; selectors may change. Adjust as needed.
    """
    name = "docinfo"

    def search(self, first: str, last: str, middle: str = "", state: str = "") -> List[Dict[str, Any]]:
        session = self.session or requests.Session()
        q = f"{first} {middle} {last}".strip()
        url = "https://www.docinfo.org/search/"
        # Typical pattern: GET with ?q=, but site may use POST or dynamic scripts.
        # We'll try a GET first and fall back to server-side search.
        params = {"q": q}
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            # fallback: plain GET
            resp = session.get(url, timeout=30)

        results: List[Dict[str, Any]] = []
        soup = BeautifulSoup(resp.text, "html.parser")

        # Heuristic parsing: result cards with name and profile links
        cards = soup.select("a[href*='/doctor/'], div.result, div.card a[href]")
        seen = set()
        for el in cards:
            href = el.get("href", "")
            text = el.get_text(" ", strip=True)
            if "/doctor/" in href and href not in seen:
                seen.add(href)
                full_name = text.split(" - ")[0].strip() if " - " in text else text
                profile_url = href if href.startswith("http") else f"https://www.docinfo.org{href}"
                results.append({
                    "source": self.name,
                    "full_name": full_name,
                    "degree": "",
                    "states": "",
                    "license_number": "",
                    "status": "",
                    "profile_url": profile_url,
                    "board_name": "FSMB DocInfo"
                })

        # If we found nothing, try a slower parse of all links
        if not results:
            for a in soup.find_all("a", href=True):
                if "/doctor/" in a["href"]:
                    profile_url = a["href"] if a["href"].startswith("http") else f"https://www.docinfo.org{a['href']}"
                    full_name = a.get_text(" ", strip=True)
                    if profile_url not in seen:
                        seen.add(profile_url)
                        results.append({
                            "source": self.name,
                            "full_name": full_name,
                            "degree": "",
                            "states": "",
                            "license_number": "",
                            "status": "",
                            "profile_url": profile_url,
                            "board_name": "FSMB DocInfo"
                        })

        return results
