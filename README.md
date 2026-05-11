# Backend - Conversational SHL Assessment Recommender

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Endpoints

```bash
GET http://localhost:8000/health
POST http://localhost:8000/chat
```

## Test request

```json
{
  "messages": [
    {"role": "user", "content": "Hiring a mid-level Java developer who works with stakeholders"}
  ]
}
```

## Important

Replace `data/shl_catalog.json` with the full SHL Individual Test Solutions catalog before final submission.
