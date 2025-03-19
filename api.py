from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from src.llamarequest import llm_api
from src.poi_filter import get_poi_data
from src.get_top_candidates import find_top_candidates
from src.get_location_advice import get_location_advice
from fastapi.responses import JSONResponse

# Initialize FastAPI app with custom title and description
app = FastAPI(
    title="Location Query API",
    description="This API helps you query locations based on a given prompt and geographical data.",
    version="1.0.0",
    docs_url="/docs",  # Custom URL for the Swagger documentation
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom error handler for 404 Not Found


@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "API request was successful, but the endpoint was not found."},
    )


class QueryRequest(BaseModel):
    prompt: str
    latitude: float
    longitude: float
    radius: int
    num_results: int = 5


class QueryResponse(BaseModel):
    location_advice: str
    candidates: Dict[str, List[Dict[str, Any]]]


@app.post("/query", response_model=QueryResponse)
async def query_location(data: QueryRequest):
    """
    Processes user input prompt, location data (latitude, longitude), and search radius to find the best locations and provide advice.
    """

    print("Received Request:")
    print("Prompt:", data.prompt)
    print("Latitude:", data.latitude)
    print("Longitude:", data.longitude)
    print("Radius:", data.radius)
    print("Num Results:", data.num_results)

    result = llm_api(data.prompt)

    search_subcategory = result['subcategories']['findings']
    search_tag = result['tags']['existed']

    candidates = get_poi_data(
        data.latitude, data.longitude, data.radius, search_subcategory)

    top_candidates = find_top_candidates(
        candidates, data.latitude, data.longitude, data.radius, data.num_results)

    location_advice = get_location_advice(top_candidates, data.prompt)

    print("Generated Location Advice:", location_advice)

    return QueryResponse(
        location_advice=location_advice,
        candidates=top_candidates
    )
