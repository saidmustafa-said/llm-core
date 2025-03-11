from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

# Importing updated functions
from src.llamarequest import llm_api
from src.poi_filter import get_poi_data
from src.get_top_candidates import find_top_candidates
from src.get_location_advice import get_location_advice

# Initialize FastAPI app
app = FastAPI()

# Request model


class QueryRequest(BaseModel):
    prompt: str
    latitude: float
    longitude: float
    radius: int
    num_results: int = 5  # Default to 5 results


# Response model


class QueryResponse(BaseModel):
    location_advice: str
    candidates: Dict[str, List[Dict[str, Any]]]


@app.post("/query", response_model=QueryResponse)
async def query_location(data: QueryRequest):
    """
    Processes user input prompt, location data (latitude, longitude), and search radius to find the best locations and provide advice.
    """
    # Step 1: Extract tags from prompt
    result = llm_api(data.prompt)
    if not result or not result.get('existed_tags'):
        return {"message": "No tags found for the given prompt."}

    search_tag = result['existed_tags'][0]

    # Step 2: Fetch candidate POIs
    candidates = get_poi_data(
        data.latitude, data.longitude, data.radius, search_tag)

    # Step 3: Find top candidates
    top_candidates = find_top_candidates(
        candidates, data.latitude, data.longitude, data.radius, search_tag, data.num_results)

    # Step 4: Generate location advice using LLM
    location_advice = get_location_advice(top_candidates, data.prompt)

    return QueryResponse(
        location_advice=location_advice,
        candidates=top_candidates
    )
