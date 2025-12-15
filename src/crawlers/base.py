from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseCrawler(ABC):
    @abstractmethod
    def fetch_latest(self, limit: int = 5) -> List[Dict[str, Any]]:
        pass
