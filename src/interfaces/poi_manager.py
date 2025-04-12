from typing import List, Protocol
from src.data_types import POIData


class IPOIManager(Protocol):
    """Interface for POI Manager"""

    def get_poi_by_subcategories(self, user_lat: float, user_lon: float, radius_m: int,
                                 search_subcategories: List[str]) -> List[POIData]:
        """Get POI data filtered by subcategories"""
        ...

    def get_available_categories(self, user_lat: float, user_lon: float, radius_m: int) -> str:
        """Get available categories and subcategories as a formatted string"""
        ...
