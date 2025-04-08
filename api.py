# api.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uuid
import time
from src.config_manager import ConfigManager
from main import process_request, create_session, get_session_history, get_session_messages
from src.logger_setup import session_logger, get_logger

# Initialize FastAPI app
app = FastAPI(
    title="Location Advice API",
    description="API for location-based advice and recommendations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize config manager
config_manager = ConfigManager()


class UserMessageRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User message")
    latitude: float = Field(..., description="User latitude")
    longitude: float = Field(..., description="User longitude")
    search_radius: int = Field(..., description="Search radius in meters")


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

    # Extract user ID and session ID from request if available
    user_id = "unknown"
    session_id = request_id  # Default to request_id if session_id not found
    if request.method == "POST":
        try:
            body = await request.json()
            user_id = body.get("user_id", "unknown")
            # Use session_id from request body if available
            if "session_id" in body:
                session_id = body.get("session_id")
        except:
            pass

    # Initialize session logging
    session_logger.start_session(user_id, session_id)
    logger = get_logger()

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
    """Process a user message and return a response"""
    logger = get_logger()
    logger.info(
        f"Processing message for user {request.user_id}, session {request.session_id}")

    try:
        response = process_request(
            request.user_id,
            request.session_id,
            request.message,
            request.latitude,
            request.longitude,
            request.search_radius,
            config_manager.get_state_manager(),
            config_manager.get_history_manager()
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
    """Create a new session for a user"""
    # Create a new session_id
    session_id = create_session(
        request.user_id, config_manager.get_state_manager())

    # Initialize logging for this new session
    session_logger.start_session(request.user_id, session_id)
    logger = get_logger()
    logger.info(f"Created new session {session_id} for user {request.user_id}")

    return SessionResponse(session_id=session_id)


@app.get("/session/{user_id}/{session_id}/history")
async def get_history(user_id: str, session_id: str):
    """Get the conversation history for a session"""
    # Initialize session logging for this existing session
    session_logger.start_session(user_id, session_id)
    logger = get_logger()
    logger.info(f"Getting history for user {user_id}, session {session_id}")

    try:
        history = get_session_history(
            user_id, session_id, config_manager.get_history_manager())
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting history: {str(e)}")


@app.get("/session/{user_id}/{session_id}/messages")
async def get_messages(user_id: str, session_id: str):
    """Get the raw messages for a session"""
    logger = get_logger()
    logger.info(f"Getting messages for user {user_id}, session {session_id}")

    try:
        messages = get_session_messages(
            user_id, session_id, config_manager.get_history_manager())
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting messages: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
