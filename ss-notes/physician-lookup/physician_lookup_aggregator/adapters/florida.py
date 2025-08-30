from typing import List, Dict, Any
from .base import BaseAdapter

class FloridaAdapter(BaseAdapter):
    """
    Outline for automating FL DOH MQA search with Playwright (human-in-the-loop may be required if CAPTCHA appears).
    """
    name = "florida"

    def search(self, first: str, last: str, middle: str = "", state: str = "") -> List[Dict[str, Any]]:
        # Pseudocode / outline:
        # - Use Playwright to open https://mqa-internet.doh.state.fl.us/mqasearchservices/home
        # - Select "License Verification"
        # - Fill first and last name fields, submit
        # - Parse table rows for license number, status, profession, and detail page URLs
        # - Return normalized results
        # In this starter, we return an empty list to avoid brittle automation by default.
        return []
