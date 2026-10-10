# Bulk Certificate Generator

A Python REST API that generates PDF certificates in bulk, tracks generation results, and allows users to download individual certificates.

## Features

- Generate certificates for multiple recipients through a single API request.
- Validate recipient data using Pydantic.
- Create PDF certificates using ReportLab.
- Store generation jobs and recipient results in SQLite using SQLAlchemy.
- Track successful and failed certificate generations.
- Continue processing other recipients when an individual certificate fails.
- Retrieve job status and recipient-level results.
- Download generated certificates through an API endpoint.
- Automated tests for API behavior, validation, downloads, and individual failures.

## Technology Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- ReportLab
- Pytest
- HTTPX / FastAPI TestClient

## Project Structure

```text
bulk-certificate-generator/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── services/
│       ├── __init__.py
│       └── certificate_generator.py
├── tests/
│   ├── test_api.py
│   └── test_database.py
├── generated_certificates/
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/MANIKESHAV6/Bulk-Certificate-Generator.git
cd bulk-certificate-generator
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the API

```bash
python -m uvicorn app.main:app --reload
```

The API runs locally at `http://127.0.0.1:8000`.

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Check that the API is running |
| GET | `/health` | Health check |
| POST | `/api/jobs` | Generate certificates for multiple recipients |
| GET | `/api/jobs/{job_id}` | Retrieve job status and recipient results |
| GET | `/api/certificates/{certificate_id}/download` | Download an individual PDF certificate |

## Example Request

Send a POST request to `/api/jobs` with a JSON body:

```json
{
  "recipients": [
    {
      "name": "Asha Reddy",
      "course_name": "Python Backend Development",
      "completion_date": "10 October 2026"
    },
    {
      "name": "Ravi Kumar",
      "course_name": "Database Fundamentals",
      "completion_date": "10 October 2026"
    }
  ]
}
```

The response includes a job ID, generation status, success and failure counts, and recipient-level results. Successful results include a certificate ID and download URL.

## Job Statuses

- `PROCESSING`: Generation is in progress.
- `COMPLETED`: All certificates were generated successfully.
- `COMPLETED_WITH_ERRORS`: Generation finished, but one or more certificates failed.

Individual recipient statuses include `PENDING`, `SUCCESS`, and `FAILED`.

## Run Tests

Run the automated test suite from the project root:

```bash
python -m pytest -v
```

The tests cover bulk generation, job status retrieval, PDF downloading, input validation, unknown resources, and individual certificate-generation failures.

## Design Decisions

- **FastAPI:** Provides REST endpoints and interactive API documentation.
- **SQLite and SQLAlchemy:** Persist jobs and recipient-level generation results.
- **ReportLab:** Generates PDF certificates programmatically from a predefined layout.
- **Pydantic:** Validates incoming request data.
- **Per-recipient exception handling:** Allows processing to continue when an individual certificate fails.
- **Isolated test database:** Keeps automated tests separate from the application's normal database.

## Current Limitations

Certificate generation currently runs synchronously within the POST request. Large batches may take longer to process. Background workers and live intermediate progress reporting could be added in a future version.