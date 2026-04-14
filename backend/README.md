# PredictX Industrial AI Backend (FastAPI)

## Run locally

1. Create virtual environment and activate it.
2. Install dependencies:

   pip install -r requirements.txt

3. Create environment file:

   copy .env.example .env

4. Start API:

   uvicorn app.main:app --reload --port 8000

## Key endpoints

- POST /api/login
- GET /api/users
- GET /api/sensors/live
- GET /api/sensors/history
- GET /api/machines
- GET /api/machines/{id}
- GET /api/predict/failure
- GET /api/predict/alerts
- POST /api/reports/export
- GET /health
- WS /ws/telemetry

## Demo credentials

- ava@predictx.ai / admin123
- rohan@predictx.ai / engineer123
