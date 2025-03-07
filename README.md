<!-- @format -->

## Python Version: Python 3.10.0

Install Libraries:

```bash
pip install -r requirements.txt
```

Start the api:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Request api:

```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d "{\"prompt\": \"i want to go to somewhere with a great view where i can also drink something\", \"latitude\": 40.985660, \"longitude\": 29.027361, \"radius\": 5000, \"num_results\": 5}"
```

Note: if you add new libraries run this command.

```bash
pip freeze > requirements.txt
```
