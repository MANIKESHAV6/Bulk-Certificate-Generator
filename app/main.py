
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models
from app.models import GenerationJob, Recipient
from app.schemas import (
    BulkCertificateRequest,
    JobResponse,
    RecipientResult,
)
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from app.services.certificate_generator import generate_certificate


# Create missing database tables.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator",
    description="Generate and manage certificates for multiple recipients.",
    version="1.0.0",
)

# Store generated PDFs inside the project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CERTIFICATE_DIR = PROJECT_ROOT / "generated_certificates"


@app.get("/")
def home():
    return {
        "message": "Bulk Certificate Generator API is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/jobs", response_model=JobResponse)
def create_generation_job(
    request: BulkCertificateRequest,
    db: Session = Depends(get_db),
):
    # Step 1: Create and save the overall job.
    job = GenerationJob(
        status="PROCESSING",
        total_count=len(request.recipients),
        success_count=0,
        failure_count=0,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Step 2: Save each recipient before generating PDFs.
    recipient_records = []

    for item in request.recipients:
        recipient = Recipient(
            job_id=job.id,
            name=item.name,
            course_name=item.course_name,
            completion_date=item.completion_date,
            certificate_id=str(uuid4()),
            status="PENDING",
        )
        db.add(recipient)
        recipient_records.append(recipient)

    db.commit()

    # Step 3: Generate certificates independently.
    for recipient in recipient_records:
        try:
            filename = f"{recipient.certificate_id}.pdf"
            output_path = CERTIFICATE_DIR / filename

            saved_path = generate_certificate(
                recipient_name=recipient.name,
                course_name=recipient.course_name,
                completion_date=recipient.completion_date,
                certificate_id=recipient.certificate_id,
                output_path=str(output_path),
            )

            recipient.status = "SUCCESS"
            recipient.file_path = saved_path
            recipient.error_message = None
            job.success_count += 1

        except Exception as exc:
            # Record the failure and continue with other recipients.
            recipient.status = "FAILED"
            recipient.error_message = (
                f"Certificate generation failed: {type(exc).__name__}"
            )
            job.failure_count += 1

    # Step 4: Set the final job status and persist the results.
    if job.failure_count == 0:
        job.status = "COMPLETED"
    else:
        job.status = "COMPLETED_WITH_ERRORS"

    db.commit()
    db.refresh(job)

    results = []

    for recipient in recipient_records:
        results.append(
            RecipientResult(
                recipient_id=recipient.id,
                name=recipient.name,
                status=recipient.status,
                certificate_id=recipient.certificate_id,
                download_url=(
                    f"/api/certificates/{recipient.certificate_id}/download"
                    if recipient.status == "SUCCESS"
                    else None
                ),
                error_message=recipient.error_message,
            )
        )

    return JobResponse(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        recipients=results,
    )

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = (
        db.query(GenerationJob)
        .filter(GenerationJob.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Generation job not found",
        )

    results = []

    for recipient in job.recipients:
        results.append(
            RecipientResult(
                recipient_id=recipient.id,
                name=recipient.name,
                status=recipient.status,
                certificate_id=recipient.certificate_id,
                download_url=(
                    f"/api/certificates/{recipient.certificate_id}/download"
                    if recipient.status == "SUCCESS"
                    else None
                ),
                error_message=recipient.error_message,
            )
        )

    return JobResponse(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        recipients=results,
    )



@app.get("/api/certificates/{certificate_id}/download")
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
):
    recipient = (
        db.query(Recipient)
        .filter(Recipient.certificate_id == certificate_id)
        .first()
    )

    if recipient is None:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    if recipient.status != "SUCCESS" or not recipient.file_path:
        raise HTTPException(
            status_code=409,
            detail="Certificate is not available because generation did not succeed",
        )

    file_path = Path(recipient.file_path)

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Certificate file not found on server",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"{certificate_id}.pdf",
    )
