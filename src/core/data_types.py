# data_types.py
from typing import TypedDict, List, Dict, Optional, Union, Any


class LocationAdviceResponse(TypedDict):
    """
    Represents the structured response from the location advice functionality.
    """
    response: str
    continuation: bool
    recommendations: List[Dict[str, str]]
    error: Optional[str]
    token_counts: Dict[str, int]
    conversation_id: str


class LLMResponse(TypedDict):
    clarification: Optional[Union[str, Dict[str, str]]]
    categories: List[str]
    tags: Dict[str, List[str]]
    error: Optional[str]


class POIData(TypedDict):
    name: Optional[str]
    latitude: float
    longitude: float
    subcategory: str
    address: Optional[str]
    score: Optional[float]
    drive_route_distance_m: Optional[float]
    walk_route_distance_m: Optional[float]


class TopCandidates(TypedDict):
    drive: List[POIData]
    walk: List[POIData]


class Message(TypedDict):
    prompt: Dict[str, Any]  # Contains visible and hidden fields
    processes: Dict[str, Any]  # Contains hidden process information
    response: Dict[str, Any]  # Contains visible and hidden response fields


class Conversation(TypedDict):
    session_id: str
    created_at: int
    messages: List[Message]


class LLMRequest(TypedDict):
    model: str
    messages: List[Dict[str, str]]
    functions: List[Dict]
    function_call: str
    max_tokens: int
    temperature: float
