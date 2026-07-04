# MediVoice - AI Voice Agent Assistant

MediVoice is a conversational backend that lets patients book, cancel, and check appointments by voice. Built with FastAPI for the API layer, SQLAlchemy for persistence, and Streamlit for a quick manual-testing UI. Data is stored in PostgreSQL. It's meant to sit behind a VAPI assistant, translating natural-language requests into appointment records.



## ✨ What it does

- Book appointments — create a new appointment with the patient's name, visit reason, and requested time.
- Cancel appointments — clear out all of a patient's appointments on a chosen date.
- Check the schedule — pull up every active (not-canceled) appointment for a given day.
- Manual test UI — a lightweight Streamlit page for poking at the API without a voice client.
-PostgreSQL-backed storage — reliable, production-ready persistence via a Postgres database.

## 🛠️ Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd voice_agent
```

### 2. Create and activate a virtual environment

Using Python's built-in tooling:

```bash
python -m venv .venv
```

Activate it with one of the following:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

Using pip:

```bash
pip install -r requirements.txt
```

Or with uv:

```bash
uv sync
```

### 4. Configure the database

The project uses SQLite by default, so a local database file will be created automatically at `appointments_db.db`.

To use PostgreSQL instead, set:

```bash
export DATABASE_URL="postgresql://<user>:<password>@<host>:5432/<db_name>"
```

On Windows PowerShell:

```powershell
$env:DATABASE_URL="postgresql://<user>:<password>@<host>:5432/<db_name>"
```

### 5. Run the backend

```bash
python backend.py
```

The API will be available at:

- http://127.0.0.1:4444/
- http://127.0.0.1:4444/docs

### 6. Run the dashboard (optional)

```bash
streamlit run frontend.py
```

## 📁 Repository layout

- `backend.py` — FastAPI application and appointment endpoints.
- `database.py` — SQLAlchemy models, database setup, and session handling.
- `frontend.py` — Streamlit dashboard for viewing and managing appointments.
- `database_demo.py` — simple script for inspecting stored data.
- `api/index.py` — serverless entrypoint used by deployment wrappers.
- `render.yaml` and `vercel.json` — deployment configuration files.
- `pyproject.toml` and `requirements.txt` — project dependencies.

## 📡 API reference

All appointment routes accept JSON in the request body.

### Schedule an appointment

POST `/schedule_appointment/`

| Field | Type | Notes |
| --- | --- | --- |
| `patient_name` | string | Patient's full name |
| `reason` | string | Optional visit reason |
| `start_time` | string | ISO 8601 timestamp, for example `2026-02-20T09:00:00` |

Example:

```json
{
  "patient_name": "Hassan",
  "reason": "Annual checkup",
  "start_time": "2026-02-20T09:00:00"
}
```

### Cancel appointment(s)

POST `/cancel_appointment/`

| Field | Type | Notes |
| --- | --- | --- |
| `patient_name` | string | Patient's full name |
| `date` | string | ISO 8601 date to clear, for example `2026-02-20` |

### List appointments for a day

POST `/list_appointments/`

| Field | Type | Notes |
| --- | --- | --- |
| `date` | string | ISO 8601 date to query, for example `2026-02-20` |

## 🗄️ Storage

The app uses SQLAlchemy to manage appointments. By default it creates a local SQLite database file named `appointments_db.db`. If you provide `DATABASE_URL`, it will switch to PostgreSQL instead.

### Appointment table

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer | Auto-incrementing primary key |
| `patient_name` | String | Patient's name |
| `reason` | String | Optional visit reason |
| `start_time` | DateTime | Scheduled date and time |
| `canceled` | Boolean | Whether the appointment was canceled |
| `created_at` | DateTime | Record creation timestamp |

### Inspect the data directly

```bash
python database_demo.py
```

## 🔌 Wiring up VAPI

Point your VAPI assistant to this backend and map the tools to the following endpoints:

- `schedule_appointment`
- `cancel_appointment`
- `list_appointments`

Once connected, the assistant can handle the booking flow by voice.

## 📦 Tech stack

- FastAPI — REST API framework
- SQLAlchemy — ORM and database layer
- SQLite / PostgreSQL — persistence options
- Uvicorn — ASGI server
- Streamlit — manual testing dashboard