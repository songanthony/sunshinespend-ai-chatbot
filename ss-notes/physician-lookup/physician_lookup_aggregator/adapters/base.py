import abc
from typing import List, Dict, Any

class BaseAdapter(abc.ABC):
    name: str = "base"
    supports_batch: bool = False

    def __init__(self, session):
        self.session = session

    @abc.abstractmethod
    def search(self, first: str, last: str, middle: str = "", state: str = "") -> List[Dict[str, Any]]:
        """Return a list of normalized results.
        Normalized schema:
          - source: adapter name
          - full_name
          - degree (MD/DO/etc) if available
          - states (list or comma-separated string)
          - license_number (if available)
          - status (Active/Inactive/etc) if available
          - profile_url (direct link to board profile if available)
          - board_name (if relevant)
        """
        raise NotImplementedError
