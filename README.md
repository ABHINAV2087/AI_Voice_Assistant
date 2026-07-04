# Voice Agent Appointment Backend

This project exposes a FastAPI backend for scheduling, canceling, and listing appointments. It is now prepared for deployment to Render or Vercel-compatible environments.

## Run locally

```bash
python -m uvicorn backend:app --host 0.0.0.0 --port 4444
```

## Endpoints

- GET /health
- POST /schedule_appointment/
- POST /cancel_appointment/
- POST /list_appointments/

## Deployment notes

- Render: use the included render.yaml.
- Vercel: deploy as a Python serverless app using the app entry point defined in backend.py, or use a containerized setup if preferred.
