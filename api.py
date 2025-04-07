# api.py

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uuid
import time
from src.config_manager import ConfigManager
from main import process_request, create_session, get_session_history, get_session_messages
from src.logger_setup import logger_instance

logger_instance.initialize_logging_context("system", "startup")
# Initialize FastAPI app
app = FastAPI(
    title="Location Advice API",
    description="API for location-based advice and recommendations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize config manager
config_manager = ConfigManager()

# Request and response models


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


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware for request logging"""
    request_id = str(uuid.uuid4())

    # Extract user ID from request if available
    user_id = "unknown"
    if request.method == "POST":
        try:
            body = await request.json()
            user_id = body.get("user_id", "unknown")
        except:
            pass

    # Set logging context first
    logger_instance.initialize_logging_context(user_id, request_id)

    # Then get the logger
    logger = logger_instance.get_logger()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    # Process request
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Log response
    logger.info(f"Response: {response.status_code} ({process_time:.3f}s)")

    return response


@app.post("/message", response_model=MessageResponse)
async def process_message(request: UserMessageRequest):
    """
    Process a user message and return a response
    """
    logger = logger_instance.get_logger()
    logger.info(
        f"Processing message for user {request.user_id}, session {request.session_id}")

    # Get state and history managers from config
    state_manager = config_manager.get_state_manager()
    history_manager = config_manager.get_history_manager()

    try:
        # Process the request
        response = process_request(
            request.user_id,
            request.session_id,
            request.message,
            request.latitude,
            request.longitude,
            request.search_radius,
            state_manager,
            history_manager
        )

        return MessageResponse(
            response=response.get("response", ""),
            status=response.get("status", "unknown"),
            continuation=response.get("continuation", False),
            parameters=response.get("parameters")
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}")


@app.post("/session", response_model=SessionResponse)
async def create_new_session(request: CreateSessionRequest):
    """
    Create a new session for a user
    """
    logger = logger_instance.get_logger()
    logger.info(f"Creating new session for user {request.user_id}")

    # Get state manager from config
    state_manager = config_manager.get_state_manager()

    try:
        # Create new session
        session_id = create_session(request.user_id, state_manager)
        return SessionResponse(session_id=session_id)
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error creating session: {str(e)}")


@app.get("/session/{user_id}/{session_id}/history")
async def get_history(user_id: str, session_id: str):
    """
    Get the conversation history for a session
    """
    logger = logger_instance.get_logger()
    logger.info(f"Getting history for user {user_id}, session {session_id}")

    # Get history manager from config
    history_manager = config_manager.get_history_manager()

    try:
        # Get session history
        history = get_session_history(user_id, session_id, history_manager)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting history: {str(e)}")


@app.get("/session/{user_id}/{session_id}/messages")
async def get_messages(user_id: str, session_id: str):
    """
    Get the raw messages for a session
    """
    logger = logger_instance.get_logger()
    logger.info(f"Getting messages for user {user_id}, session {session_id}")

    # Get history manager from config
    history_manager = config_manager.get_history_manager()

    try:
        # Get session messages
        messages = get_session_messages(user_id, session_id, history_manager)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting messages: {str(e)}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}
