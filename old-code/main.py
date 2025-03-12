# from fastapi import FastAPI
# from pydantic import BaseModel
# import json
# from typing import List, Dict, Any

# # Var olan kodları buraya ekleyebilirsin
# from working_script import llm_api, find_top_candidates, format_top_candidates, get_location_advice

# # FastAPI uygulamasını başlat
# app = FastAPI()

# # API için giriş modeli


# class QueryRequest(BaseModel):
#     prompt: str
#     latitude: float
#     longitude: float
#     radius: int
#     num_results: int = 5  # Varsayılan olarak 5 sonuç döndürülsün

# # Yanıt formatı


# class QueryResponse(BaseModel):
#     location_advice: str
#     candidates: Dict[str, List[Dict[str, Any]]]


# @app.post("/query", response_model=QueryResponse)
# async def query_location(data: QueryRequest):
#     """
#     Kullanıcının girdiği `prompt`, konum (latitude, longitude) ve çap (radius) bilgilerine göre
#     en iyi lokasyonları bulur ve tavsiye verir.
#     """
#     # 1. Prompt'tan etiketleri çıkar
#     result = llm_api(data.prompt)
#     if not result or not result.get('existed_tags'):
#         return {"message": "No tags found for the given prompt."}

#     search_tag = result['existed_tags'][0]

#     # 2. En iyi lokasyonları bul
#     top_candidates = find_top_candidates(
#         data.latitude, data.longitude, data.radius, search_tag, data.num_results
#     )

#     # 3. Verileri okunabilir formatta hazırla
#     formatted_candidates = format_top_candidates(top_candidates)

#     # 4. LLM API kullanarak tavsiye oluştur
#     location_advice = get_location_advice(formatted_candidates, data.prompt)

#     return QueryResponse(
#         location_advice=location_advice,
#         candidates=top_candidates
#     )
