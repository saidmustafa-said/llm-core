from functools import wraps
import logging
import re
import json
import time
from src.data_types import POIData, TopCandidates, LLMResponse
from typing import Dict


def validate_poi_data(poi: Dict) -> POIData:
    required_keys = {'latitude', 'longitude', 'subcategory'}
    if not required_keys.issubset(poi.keys()):
        missing = required_keys - poi.keys()
        raise ValueError(f"Invalid POI data, missing keys: {missing}")
    return POIData(poi)


def validate_top_candidates(candidates: Dict) -> TopCandidates:
    valid_modes = {'drive', 'walk', 'default'}
    return TopCandidates({
        mode: [validate_poi_data(poi) for poi in candidates.get(mode, [])]
        for mode in valid_modes
    })


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        # print(f"{func.__name__} süresi: {end_time - start_time:.6f} saniye")
        return result
    return wrapper


# utils.py

logging.basicConfig(level=logging.INFO)


def count_tokens(text: str) -> int:
    tokens = text.split()
    punctuation_count = sum(1 for char in text if char in '.,;:!?()[]{}"\'')
    return len(tokens) + punctuation_count


def extract_json_from_text(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0).strip())
            except json.JSONDecodeError:
                logging.error("Regex JSON extraction failed.")
    return {}
