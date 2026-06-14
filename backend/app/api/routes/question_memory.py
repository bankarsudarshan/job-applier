from typing import List
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from app.api.deps import SessionDep, CurrentUser
from app.models.question_memory import QuestionMemory
from app.services.question_matching import question_matching

router = APIRouter(prefix="/questions", tags=["questions"])

class QuestionMemoryPublic(BaseModel):
    id: uuid.UUID
    question: str
    normalized_key: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionMemoryCreate(BaseModel):
    question: str
    normalized_key: str
    answer: str

class QuestionMatchRequest(BaseModel):
    question: str

class QuestionMatchResponse(BaseModel):
    matched: bool
    answer: str | None

@router.get("/", response_model=List[QuestionMemoryPublic])
def list_questions(session: SessionDep, current_user: CurrentUser):
    statement = select(QuestionMemory).where(QuestionMemory.user_id == current_user.id).order_by(QuestionMemory.created_at.desc())
    return session.exec(statement).all()

@router.post("/", response_model=QuestionMemoryPublic)
def save_question_answer(
    session: SessionDep,
    current_user: CurrentUser,
    data: QuestionMemoryCreate
):
    mem = question_matching.save_answer(
        session=session,
        user_id=current_user.id,
        question=data.question,
        normalized_key=data.normalized_key,
        answer=data.answer
    )
    return mem

@router.post("/match", response_model=QuestionMatchResponse)
def match_question(
    session: SessionDep,
    current_user: CurrentUser,
    data: QuestionMatchRequest
):
    answer = question_matching.find_matching_answer(session, current_user.id, data.question)
    return QuestionMatchResponse(
        matched=answer is not None,
        answer=answer
    )
