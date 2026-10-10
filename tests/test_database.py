
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import GenerationJob, Recipient


@pytest.fixture
def db_session():
    # Create a separate in-memory database for this test.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=test_engine)

    TestingSession = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


def test_job_with_multiple_recipients(db_session):
    job = GenerationJob(
        status="PENDING",
        total_count=2,
    )

    job.recipients = [
        Recipient(
            name="Asha",
            course_name="Python Basics",
            completion_date="10 October 2026",
        ),
        Recipient(
            name="Ravi",
            course_name="Python Basics",
            completion_date="10 October 2026",
        ),
    ]

    db_session.add(job)
    db_session.commit()

    # Reload the job from the database.
    saved_job = db_session.get(GenerationJob, job.id)

    assert saved_job is not None
    assert saved_job.total_count == 2
    assert len(saved_job.recipients) == 2

    for recipient in saved_job.recipients:
        assert recipient.job_id == saved_job.id
        assert recipient.status == "PENDING"
        assert recipient.file_path is None


def test_record_generation_failure(db_session):
    job = GenerationJob(total_count=1)

    recipient = Recipient(
        name="Asha",
        course_name="Python Basics",
        completion_date="10 October 2026",
        status="PENDING",
    )

    job.recipients.append(recipient)
    db_session.add(job)
    db_session.commit()

    # Simulate a certificate-generation failure.
    recipient.status = "FAILED"
    recipient.error_message = "Sample generation error"
    job.failure_count = 1
    job.status = "COMPLETED_WITH_ERRORS"

    db_session.commit()
    db_session.refresh(recipient)
    db_session.refresh(job)

    assert recipient.status == "FAILED"
    assert recipient.error_message == "Sample generation error"
    assert job.failure_count == 1
    assert job.status == "COMPLETED_WITH_ERRORS"
