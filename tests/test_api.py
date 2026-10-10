
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main
from app.database import Base, get_db
from app.services.certificate_generator import (
    generate_certificate as real_generate_certificate,
)


@pytest.fixture
def api_client(monkeypatch, tmp_path):
    # Create an isolated in-memory database for this test.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override_get_db

    # Save test certificates in a temporary folder.
    monkeypatch.setattr(
        main,
        "CERTIFICATE_DIR",
        tmp_path / "generated_certificates",
    )

    # Use the real PDF generator by default.
    monkeypatch.setattr(
        main,
        "generate_certificate",
        real_generate_certificate,
    )

    with TestClient(main.app) as client:
        yield client

    main.app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def sample_request():
    return {
        "recipients": [
            {
                "name": "Asha Reddy",
                "course_name": "Python Backend Development",
                "completion_date": "10 October 2026",
            },
            {
                "name": "Ravi Kumar",
                "course_name": "Database Fundamentals",
                "completion_date": "10 October 2026",
            },
        ]
    }


def test_bulk_generation_and_job_status(api_client):
    response = api_client.post("/api/jobs", json=sample_request())

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["total_count"] == 2
    assert data["success_count"] == 2
    assert data["failure_count"] == 0

    # Retrieve the same job using its ID.
    job_id = data["job_id"]
    status_response = api_client.get(f"/api/jobs/{job_id}")

    assert status_response.status_code == 200

    status_data = status_response.json()
    assert status_data["job_id"] == job_id
    assert status_data["success_count"] == 2
    assert len(status_data["recipients"]) == 2

    for recipient in status_data["recipients"]:
        assert recipient["status"] == "SUCCESS"
        assert recipient["download_url"] is not None


def test_download_certificate_pdf(api_client):
    response = api_client.post("/api/jobs", json=sample_request())
    assert response.status_code == 200

    recipient = response.json()["recipients"][0]
    certificate_id = recipient["certificate_id"]

    download_response = api_client.get(
        f"/api/certificates/{certificate_id}/download"
    )

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    assert download_response.content.startswith(b"%PDF-")


def test_individual_failure_does_not_stop_other_certificates(
    api_client, monkeypatch
):
    # Simulate a failure only for Ravi.
    def generate_with_one_failure(**kwargs):
        if kwargs["recipient_name"] == "Ravi Kumar":
            raise RuntimeError("Simulated PDF generation failure")

        return real_generate_certificate(**kwargs)

    monkeypatch.setattr(
        main,
        "generate_certificate",
        generate_with_one_failure,
    )

    request_data = sample_request()
    request_data["recipients"].append(
        {
            "name": "Priya Sharma",
            "course_name": "FastAPI Essentials",
            "completion_date": "10 October 2026",
        }
    )

    response = api_client.post("/api/jobs", json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "COMPLETED_WITH_ERRORS"
    assert data["total_count"] == 3
    assert data["success_count"] == 2
    assert data["failure_count"] == 1

    results = {item["name"]: item for item in data["recipients"]}

    assert results["Asha Reddy"]["status"] == "SUCCESS"
    assert results["Ravi Kumar"]["status"] == "FAILED"
    assert results["Priya Sharma"]["status"] == "SUCCESS"

    assert results["Ravi Kumar"]["error_message"] is not None
    assert results["Ravi Kumar"]["download_url"] is None

    # The job status endpoint must preserve the failure result.
    job_id = data["job_id"]
    status_response = api_client.get(f"/api/jobs/{job_id}")

    assert status_response.status_code == 200
    assert status_response.json()["failure_count"] == 1

    # A failed certificate cannot be downloaded.
    failed_certificate_id = results["Ravi Kumar"]["certificate_id"]

    download_response = api_client.get(
        f"/api/certificates/{failed_certificate_id}/download"
    )

    assert download_response.status_code == 409


def test_invalid_request_is_rejected(api_client):
    # The course_name field is missing.
    invalid_request = {
        "recipients": [
            {
                "name": "Asha Reddy",
                "completion_date": "10 October 2026",
            }
        ]
    }

    response = api_client.post("/api/jobs", json=invalid_request)

    assert response.status_code == 422


def test_unknown_job_and_certificate_return_404(api_client):
    job_response = api_client.get("/api/jobs/nonexistent-job")
    certificate_response = api_client.get(
        "/api/certificates/nonexistent-certificate/download"
    )

    assert job_response.status_code == 404
    assert certificate_response.status_code == 404
