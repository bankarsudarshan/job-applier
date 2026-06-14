import uuid
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime
from sqlmodel import Field, Relationship, SQLModel

def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)

class Job(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255, index=True)
    company: str = Field(max_length=255, index=True)
    location: str = Field(max_length=255)
    description: str = Field(default="")
    url: str = Field(unique=True, index=True, max_length=512)
    ats_type: str | None = Field(default=None, max_length=100)
    raw_data: dict = Field(default_factory=dict, sa_type=JSON)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    applications: list["Application"] = Relationship(back_populates="job", cascade_delete=True)
