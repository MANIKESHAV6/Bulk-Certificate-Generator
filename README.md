# Bulk Certificate Generator

A Python REST API that generates PDF certificates in bulk, tracks generation results, verifies certificates using QR codes, and supports certificate revocation.

## Features

- Generate PDF certificates for multiple recipients through a single API request.
- Validate incoming recipient data using Pydantic.
- Generate certificates using ReportLab and a predefined layout.
- Store generation jobs and recipient records in SQLite using SQLAlchemy.
- Track successful and failed certificate generations.
- Continue processing other recipients when an individual certificate fails.
- Retrieve job status and recipient-level results.
- Download individual PDF certificates.
- Add QR codes to certificates for verification.
- Verify certificate validity through an API endpoint.
- Revoke certificates using an administrator token.
- Prevent downloads of revoked certificates.
- Test API behavior with automated tests.

## Technology Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy and SQLite
- ReportLab
- `qrcode` and Pillow
- Pytest and FastAPI TestClient

## Project Structure

```text
bulk-certificate-generator/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── migrations.py
│   └── services/
│       ├── __init__.py
│       └── certificate_generator.py
├── tests/
│   ├── test_api.py
│   └── test_database.py
├── generate_sample.py
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/MANIKESHAV6/Bulk-Certificate-Generator.git
cd Bulk-Certificate-Generator
```

### 2. Create and activate a virtual environment

For Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure the administrator token

Certificate revocation requires an administrator token. Set a local development token in PowerShell before starting the API:

```powershell
$env:CERTIFICATE_ADMIN_TOKEN = "replace-with-your-local-development-token"
```

Use your own local value. Do not put real secrets in source code, this README, or GitHub.

### 5. Run the API

```powershell
python -m uvicorn app.main:app --reload
```

The API is available at:

- Base URL: <http://127.0.0.1:8000>
- Interactive API documentation: <http://127.0.0.1:8000/docs>

The default QR verification URL uses `127.0.0.1`, which is suitable for local testing on the same computer. To let other devices reach the verification endpoint, set `PUBLIC_BASE_URL` to a reachable base URL before generating certificates.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Check that the API is running |
| `GET` | `/health` | Health check |
| `POST` | `/api/jobs` | Generate certificates for multiple recipients |
| `GET` | `/api/jobs/{job_id}` | Retrieve job status and recipient results |
| `GET` | `/api/certificates/{certificate_id}/download` | Download an individual PDF certificate |
| `GET` | `/api/verify/{certificate_id}` | Verify a certificate's current status |
| `POST` | `/api/certificates/{certificate_id}/revoke` | Revoke a certificate with administrator authorization |

## Example Bulk Generation Request

Send a `POST` request to `/api/jobs` with this JSON body:

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

## QR-Based Certificate Verification

Each generated certificate contains a QR code linked to its verification endpoint:

`GET /api/verify/{certificate_id}`

A successfully generated, non-revoked certificate returns `valid: true` and `status: "VALID"`. A revoked certificate returns `valid: false` and `status: "REVOKED"`. An unknown certificate ID returns HTTP `404`.

## Certificate Revocation

An authorized administrator can revoke a successfully generated certificate by providing a reason.

Endpoint:

`POST /api/certificates/{certificate_id}/revoke`

Example request body:

```json
{
  "reason": "Issued to the wrong recipient"
}
```

Include the administrator token in the `X-Admin-Token` request header. The token is configured using the `CERTIFICATE_ADMIN_TOKEN` environment variable.

After revocation:

- The verification endpoint reports the certificate as revoked.
- The download endpoint returns HTTP `410`.
- The database stores the revocation timestamp and reason.
- Repeated revocation requests preserve the original revocation details.

The administrator token is a simple access-control mechanism for this project. A production deployment should use stronger authentication and authorization, secure secret management, and appropriate audit controls.

## Job and Recipient Statuses

Generation jobs can have these statuses:

- `PROCESSING`: Generation is in progress.
- `COMPLETED`: All certificates were generated successfully.
- `COMPLETED_WITH_ERRORS`: Generation finished, but one or more certificates failed.

Individual recipient statuses include `PENDING`, `SUCCESS`, and `FAILED`. Verification reports whether a successfully generated certificate is currently valid or revoked.

## Run Automated Tests

Run the test suite from the project root:

```powershell
python -m pytest -v
```

The tests cover bulk generation, input validation, job status retrieval, PDF downloads, QR verification, certificate revocation, administrator authorization, and individual certificate-generation failures.

## Design Decisions

- **FastAPI:** Provides REST endpoints and interactive API documentation.
- **Pydantic:** Validates incoming request data.
- **SQLite and SQLAlchemy:** Store generation jobs, recipient information, and revocation details.
- **ReportLab:** Generates PDF certificates programmatically.
- **QR codes:** Provide a convenient link to the certificate verification endpoint.
- **Per-recipient exception handling:** Allows other certificates to be generated when an individual certificate fails.
- **Isolated test database:** Keeps automated tests separate from the normal application database.

## Current Limitations

Certificate generation currently runs synchronously within the POST request, so large batches may take longer to process. The default verification URL uses localhost and is not publicly accessible from other devices unless `PUBLIC_BASE_URL` is configured appropriately. Background processing, live progress reporting, CSV import, and production-grade authentication could be added in future versions.
