import uuid
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime
from sqlmodel import Field, Relationship, SQLModel

def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)

class Profile(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        unique=True,
        index=True,
        ondelete="CASCADE",
    )
    personal_info: dict = Field(default_factory=dict, sa_type=JSON)
    education: list = Field(default_factory=list, sa_type=JSON)
    experience: list = Field(default_factory=list, sa_type=JSON)
    skills: list = Field(default_factory=list, sa_type=JSON)
    portfolio_links: list = Field(default_factory=list, sa_type=JSON)
    preferences: dict = Field(default_factory=dict, sa_type=JSON)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    user: "User" = Relationship(back_populates="profile")
