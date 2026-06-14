import uuid
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime
from sqlmodel import Field, Relationship, SQLModel

def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)

class Resume(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)
    raw_text: str = Field(default="")
    parsed_data: dict = Field(default_factory=dict, sa_type=JSON)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    user: "User" = Relationship(back_populates="resumes")
