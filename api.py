from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from src.llamarequest import llm_api
from src.poi_filter import get_poi_data
from src.get_top_candidates import find_top_candidates
from src.get_location_advice import get_location_advice

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

    result = llm_api(data.prompt)

    search_subcategory = result['subcategories']['findings']
    search_tag = result['tags']['existed']

    candidates = get_poi_data(
        data.latitude, data.longitude, data.radius, search_subcategory)

    top_candidates = find_top_candidates(
        candidates, data.latitude, data.longitude, data.radius, data.num_results)

    location_advice = get_location_advice(top_candidates, data.prompt)

    return QueryResponse(
        location_advice=location_advice,
        candidates=top_candidates
    )
