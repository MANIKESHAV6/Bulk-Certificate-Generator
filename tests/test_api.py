
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.services import certificate_generator as generator_module
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
    verification_response = api_client.get(
    "/api/verify/nonexistent-certificate"
    )

    assert verification_response.status_code == 404
    assert job_response.status_code == 404
    assert certificate_response.status_code == 404


def test_verify_successful_certificate(api_client):
    response = api_client.post(
        "/api/jobs",
        json=sample_request(),
    )

    assert response.status_code == 200

    recipient = response.json()["recipients"][0]
    certificate_id = recipient["certificate_id"]

    verify_response = api_client.get(
        f"/api/verify/{certificate_id}"
    )

    assert verify_response.status_code == 200

    data = verify_response.json()

    assert data["certificate_id"] == certificate_id
    assert data["valid"] is True
    assert data["status"] == "VALID"
    assert data["recipient_name"] == recipient["name"]
    assert data["course_name"] == "Python Backend Development"
    assert data["completion_date"] == "10 October 2026"

def test_pdf_generation_uses_verification_qr(api_client, monkeypatch):
    captured_urls = []
    real_qr_make = generator_module.qrcode.make

    def tracking_qr_make(data, *args, **kwargs):
        captured_urls.append(data)
        return real_qr_make(data, *args, **kwargs)

    monkeypatch.setattr(
        generator_module.qrcode,
        "make",
        tracking_qr_make,
    )

    response = api_client.post(
        "/api/jobs",
        json=sample_request(),
    )

    assert response.status_code == 200

    recipients = response.json()["recipients"]

    expected_urls = {
        f"{main.PUBLIC_BASE_URL}/api/verify/{item['certificate_id']}"
        for item in recipients
    }

    assert set(captured_urls) == expected_urls
    assert len(captured_urls) == len(recipients)


def test_revoke_certificate_invalidates_verification_and_download(
    api_client,
    monkeypatch,
):
    monkeypatch.setenv(
        "CERTIFICATE_ADMIN_TOKEN",
        "test-admin-token",
    )

    response = api_client.post(
        "/api/jobs",
        json=sample_request(),
    )
    assert response.status_code == 200

    recipient = response.json()["recipients"][0]
    certificate_id = recipient["certificate_id"]

    # Verify the certificate before revocation.
    before = api_client.get(
        f"/api/verify/{certificate_id}"
    )
    assert before.status_code == 200
    assert before.json()["valid"] is True

    # Revoke the certificate using the administrator token.
    revoke_response = api_client.post(
        f"/api/certificates/{certificate_id}/revoke",
        headers={"X-Admin-Token": "test-admin-token"},
        json={"reason": "Issued to the wrong recipient"},
    )

    assert revoke_response.status_code == 200
    revoke_data = revoke_response.json()

    assert revoke_data["revoked"] is True
    assert revoke_data["status"] == "REVOKED"
    assert revoke_data["reason"] == "Issued to the wrong recipient"
    assert revoke_data["revoked_at"] is not None

    # Verification must now report that the certificate is revoked.
    after = api_client.get(
        f"/api/verify/{certificate_id}"
    )
    assert after.status_code == 200
    assert after.json()["valid"] is False
    assert after.json()["status"] == "REVOKED"

    # Downloads must be refused after revocation.
    download_response = api_client.get(
        f"/api/certificates/{certificate_id}/download"
    )
    assert download_response.status_code == 410

    # Repeating the revoke request must preserve the original reason.
    repeated = api_client.post(
        f"/api/certificates/{certificate_id}/revoke",
        headers={"X-Admin-Token": "test-admin-token"},
        json={"reason": "A different reason"},
    )

    assert repeated.status_code == 200
    assert repeated.json()["reason"] == "Issued to the wrong recipient"


def test_revocation_rejects_wrong_admin_token(
    api_client,
    monkeypatch,
):
    monkeypatch.setenv(
        "CERTIFICATE_ADMIN_TOKEN",
        "test-admin-token",
    )

    response = api_client.post(
        "/api/jobs",
        json=sample_request(),
    )
    assert response.status_code == 200

    certificate_id = response.json()["recipients"][0]["certificate_id"]

    revoke_response = api_client.post(
        f"/api/certificates/{certificate_id}/revoke",
        headers={"X-Admin-Token": "incorrect-token"},
        json={"reason": "Administrative correction"},
    )

    assert revoke_response.status_code == 403

    # The certificate remains valid because the attempted revocation failed.
    verify_response = api_client.get(
        f"/api/verify/{certificate_id}"
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["valid"] is True


def test_revocation_requires_configured_token(
    api_client,
    monkeypatch,
):
    monkeypatch.delenv(
        "CERTIFICATE_ADMIN_TOKEN",
        raising=False,
    )

    response = api_client.post(
        "/api/jobs",
        json=sample_request(),
    )
    assert response.status_code == 200

    certificate_id = response.json()["recipients"][0]["certificate_id"]

    revoke_response = api_client.post(
        f"/api/certificates/{certificate_id}/revoke",
        headers={"X-Admin-Token": "some-token"},
        json={"reason": "Administrative correction"},
    )

    assert revoke_response.status_code == 503
