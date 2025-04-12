from typing import List, Dict, Protocol
from src.data_types import POIData, TopCandidates


class ITopCandidatesFinder(Protocol):
    """Interface for finding top candidates"""

    def find_top_candidates(self, candidates: List[POIData], user_lat: float, user_lon: float,
                            radius_m: int, n: int = 4) -> TopCandidates:
        """
        Find the top n candidates from a list of POIs based on various criteria.

        Args:
            candidates: List of POI data to filter
            user_lat: User's latitude
            user_lon: User's longitude
            radius_m: Search radius in meters
            n: Number of top candidates to return (default: 4)

        Returns:
            TopCandidates object containing lists of POIs for different modes
        """
        ...
