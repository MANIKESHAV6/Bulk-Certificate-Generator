<CodeBlock language="markdown" editable>
# Bulk Certificate Generator

A Python REST API that generates PDF certificates in bulk, tracks generation results, verifies certificates using QR codes, and supports certificate revocation.
Features
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
- Test API behavior using automated tests.
Technology Stack
- Python
- FastAPI
- SQLAlchemy
- SQLite
- ReportLab
- qrcode and Pillow
- Pydantic
- Pytest
- FastAPI TestClient
Project Structure
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


Setup
1. Clone the repository
git clone https://github.com/MANIKESHAV6/Bulk-Certificate-Generator.git
cd Bulk-Certificate-Generator


2. Create and activate a virtual environment
For Windows PowerShell:
python -m venv .venv
.venv\Scripts\Activate.ps1


3. Install dependencies
python -m pip install -r requirements.txt


4. Configure the administrator token
Set a local development token in PowerShell before starting the API:
$env:CERTIFICATE_ADMIN_TOKEN = "replace-with-your-local-development-token"


Do not commit a real secret to GitHub.
5. Run the API
python -m uvicorn app.main:app --reload


The API is available at:
- Base URL: http://127.0.0.1:8000
- Interactive documentation: http://127.0.0.1:8000/docs
The default QR verification URLs use localhost. To make them accessible from another device, configure PUBLIC_BASE_URL to a reachable address before generating certificates.
API Endpoints
Method	Endpoint	Description
GET	/	Check that the API is running
GET	/health	Health check
POST	/api/jobs	Generate certificates for multiple recipients
GET	/api/jobs/DIL0	Retrieve job status and recipient results
GET	/api/certificates/DIL1/download	Download a certificate PDF
GET	/api/verify/DIL2	Verify a certificate's current status
POST	/api/certificates/DIL3/revoke	Revoke a certificate with administrator authorization
Example Bulk Generation Request
Send a POST request to /api/jobs with this JSON body:
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


The response contains a job ID, generation status, success and failure counts, and recipient-level results. Successful results include a certificate ID and download URL.
QR-Based Certificate Verification
Each generated certificate contains a QR code linked to its verification endpoint.
Endpoint:
GET /api/verify/DIL4
A successfully generated and non-revoked certificate returns valid: true and status: "VALID".
A revoked certificate returns valid: false and status: "REVOKED".
An unknown certificate ID returns HTTP 404.
Certificate Revocation
An authorized administrator can revoke a successfully generated certificate by providing a reason.
Endpoint:
POST /api/certificates/DIL0/revoke
Example request body:
{
  "reason": "Issued to the wrong recipient"
}


Include the administrator token in the X-Admin-Token request header.
After revocation:
- The verification endpoint reports the certificate as revoked.
- The download endpoint returns HTTP 410.
- The database stores the revocation timestamp and reason.
- Repeated revocation requests preserve the original revocation details.
The administrator token is a simple access-control mechanism for this project. A production deployment should use stronger authentication, authorization, and secure secret management.
Job Statuses
Generation jobs can have the following statuses:
- PROCESSING: Generation is in progress.
- COMPLETED: All certificates were generated successfully.
- COMPLETED_WITH_ERRORS: Generation finished, but one or more certificates failed.
Individual recipient statuses include PENDING, SUCCESS, and FAILED.
Run Automated Tests
Run the test suite from the project root:
python -m pytest -v


The tests cover bulk generation, input validation, job status, PDF downloads, QR verification, certificate revocation, administrator authorization, and individual generation failures.
Design Decisions
- FastAPI: Provides REST endpoints and interactive API documentation.
- Pydantic: Validates incoming request data.
- SQLite and SQLAlchemy: Store generation jobs, recipient information, and revocation details.
- ReportLab: Generates PDF certificates programmatically.
- QR codes: Provide a convenient link to the certificate verification endpoint.
- Per-recipient exception handling: Allows other certificates to be generated when an individual certificate fails.
- Isolated test database: Keeps automated tests separate from the normal application database.
Current Limitations
Certificate generation currently runs synchronously within the POST request, so large batches may take longer to process.
The default verification URLs use localhost, which is suitable for local testing but not public verification from other devices.
Background processing, live progress reporting, CSV import, and production-grade user authentication could be added in future versions.
</CodeBlock>