from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class UserMessageRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User message")
    latitude: float = Field(40.971255, description="User latitude")
    longitude: float = Field(28.793878, description="User longitude")
    search_radius: int = Field(1000, description="Search radius in meters")


class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")


class SessionResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")


class MessageResponse(BaseModel):
    response: str = Field(..., description="Assistant response")
    status: str = Field(..., description="Status of the response")
    continuation: bool = Field(
        False, description="Whether this is a continuation of a previous response")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Optional parameters for the next request")


class SessionHistoryResponse(BaseModel):
    history: List[Dict[str, Any]] = Field(
        ..., description="List of conversation history entries")


class SessionMessagesResponse(BaseModel):
    messages: List[Dict[str, Any]] = Field(
        ..., description="List of raw messages")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Service status")
