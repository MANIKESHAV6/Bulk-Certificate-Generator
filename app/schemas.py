
from pydantic import BaseModel, Field, ConfigDict


class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    course_name: str = Field(min_length=1, max_length=200)
    completion_date: str = Field(min_length=1, max_length=50)


class BulkCertificateRequest(BaseModel):
    recipients: list[RecipientInput] = Field(min_length=1, max_length=500)


class RecipientResult(BaseModel):
    recipient_id: int
    name: str
    status: str
    certificate_id: str | None = None
    download_url: str | None = None
    error_message: str | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: str
    total_count: int
    success_count: int
    failure_count: int
    recipients: list[RecipientResult]
