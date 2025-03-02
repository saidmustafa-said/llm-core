<!-- @format -->

python version 3.11.4

Start the api:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Request api:
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d "{\"prompt\": \"i want to go to somewhere with a great view where i can also drink something\", \"latitude\": 40.985660, \"longitude\": 29.027361, \"radius\": 5000, \"num_results\": 5}"
