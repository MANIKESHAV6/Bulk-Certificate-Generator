
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    status = Column(String(30), nullable=False, default="PENDING")

    total_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    recipients = relationship(
        "Recipient",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(
        String(36),
        ForeignKey("generation_jobs.id"),
        nullable=False,
        index=True,
    )

    name = Column(String(200), nullable=False)
    course_name = Column(String(200), nullable=False)
    completion_date = Column(String(50), nullable=False)

    certificate_id = Column(
        String(36),
        unique=True,
        nullable=True,
    )

    status = Column(String(20), nullable=False, default="PENDING")

    file_path = Column(String(500), nullable=True)
    error_message = Column(String(1000), nullable=True)

    job = relationship(
        "GenerationJob",
        back_populates="recipients",
    )
