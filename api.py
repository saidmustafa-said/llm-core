from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time
from typing import Dict, Any, Optional
from src.config_manager import ConfigManager
from main import process_request, create_session, get_session_history, get_session_messages
from src.logger_setup import session_logger, get_logger, get_health_check_logger
from src.flow_manager import FlowManager

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


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware for request logging"""
    request_id = str(uuid.uuid4())

    # Handle health check requests differently
    if request.url.path == "/health":
        logger = get_health_check_logger()
        logger.info(f"Health check request received")
        response = await call_next(request)
        logger.info(f"Health check response: {response.status_code}")
        return response

    # Skip logging initialization for /session endpoint
    if request.url.path == "/session":
        return await call_next(request)

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

    # Get the logger without reinitializing the session
    logger = get_logger()

    # Only initialize session if we don't have a logger yet
    if not logger.handlers:
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


@app.post("/message")
async def process_message(request: Request):
    """Process a user message and return a response"""
    logger = get_logger()
    body = await request.json()

    user_id = body.get("user_id")
    session_id = body.get("session_id")
    message = body.get("message")
    latitude = body.get("latitude")
    longitude = body.get("longitude")
    search_radius = body.get("search_radius")
    # Default to 4 if not provided
    num_candidates = body.get("num_candidates", 4)

    logger.info(
        f"Processing message for user {user_id}, session {session_id}")

    try:
        response = process_request(
            user_id,
            session_id,
            message,
            latitude,
            longitude,
            search_radius,
            config_manager.get_state_manager(),
            config_manager.get_history_manager(),
            num_candidates
        )

        return {
            "response": response.get("response", ""),
            "status": response.get("status", "unknown"),
            "continuation": response.get("continuation", False),
            "top_candidates": response.get("top_candidates", {})
        }
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}")


@app.post("/session")
async def create_new_session(request: Request):
    """Create a new session for a user"""
    body = await request.json()
    user_id = body.get("user_id")

    # Create a new session_id
    session_id = create_session(
        user_id, config_manager.get_state_manager())

    # Initialize logging for this new session
    session_logger.start_session(user_id, session_id)
    logger = get_logger()
    logger.info(f"Created new session {session_id} for user {user_id}")

    return {"session_id": session_id}


@app.get("/session/{user_id}/{session_id}/history")
async def get_history(user_id: str, session_id: str):
    """Get the conversation history for a session"""
    # Get the logger without reinitializing the session
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
    # Get the logger without reinitializing the session
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


@app.post("/delete")
async def delete_session(request: Request):
    """Delete a session by marking its files as removed"""
    logger = get_logger()
    body = await request.json()

    user_id = body.get("user_id")
    session_id = body.get("session_id")

    if not user_id or not session_id:
        raise HTTPException(
            status_code=400,
            detail="Both user_id and session_id are required"
        )

    logger.info(f"Deleting session {session_id} for user {user_id}")

    try:
        # Get the flow manager from config
        flow_manager = FlowManager(
            config_manager.get_state_manager(),
            config_manager.get_history_manager()
        )

        # Delete the session
        result = flow_manager.delete_session(user_id, session_id)

        if result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=result["message"]
            )

        return result
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting session: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
