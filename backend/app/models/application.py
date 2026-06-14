import uuid
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime
from sqlmodel import Field, Relationship, SQLModel

def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)

class Application(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    job_id: uuid.UUID = Field(
        foreign_key="job.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    status: str = Field(default="DRAFT", max_length=50, index=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    user: "User" = Relationship(back_populates="applications")
    job: "Job" = Relationship(back_populates="applications")
    fields: list["ApplicationField"] = Relationship(back_populates="application", cascade_delete=True)
    events: list["ApplicationEvent"] = Relationship(back_populates="application", cascade_delete=True)


class ApplicationField(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(
        foreign_key="application.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    field_name: str = Field(max_length=255)
    normalized_key: str = Field(max_length=255, index=True)
    field_type: str = Field(max_length=50)  # text, select, checkbox, radio, file, etc.
    options: list = Field(default_factory=list, sa_type=JSON)
    value: str | None = Field(default=None)
    is_required: bool = Field(default=False)
    resolved: bool = Field(default=False, index=True)
    selector: str | None = Field(default=None, max_length=512)

    application: "Application" = Relationship(back_populates="fields")


class ApplicationEvent(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(
        foreign_key="application.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    event_type: str = Field(max_length=50)  # INFO, WARNING, ERROR, STATUS_CHANGE, BROWSER_ACTION
    message: str = Field(default="")
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    application: "Application" = Relationship(back_populates="events")
