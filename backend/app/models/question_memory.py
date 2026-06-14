import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)

class QuestionMemory(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    question: str = Field(index=True)
    normalized_key: str = Field(index=True, max_length=255)
    answer: str
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )

    user: "User" = Relationship(back_populates="question_memories")
