import os
from typing import List
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlmodel import select
from app.api.deps import SessionDep, CurrentUser
from app.models.resume import Resume
from app.services.resume_parser import resume_parser

router = APIRouter(prefix="/resumes", tags=["resumes"])

class ResumePublic(BaseModel):
    id: uuid.UUID
    filename: str
    file_path: str
    parsed_data: dict
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/upload", response_model=ResumePublic)
async def upload_resume(
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...)
):
    # Ensure uploads directory exists
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".txt", ".md"]:
        raise HTTPException(status_code=400, detail="Only PDF, TXT or MD files are supported.")

    file_content = await file.read()
    
    # Save file to disk
    file_uuid = uuid.uuid4()
    saved_filename = f"{file_uuid}{ext}"
    file_path = os.path.join(uploads_dir, saved_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Parse and save resume synchronously for fast response
    # (can also be put in a FastAPI BackgroundTask if needed, but parsing is quick enough with fallback)
    try:
        db_resume = resume_parser.parse_and_save(
            session=session,
            user_id=current_user.id,
            file_content=file_content,
            filename=file.filename,
            file_path=file_path
        )
        return db_resume
    except Exception as e:
        # Cleanup file if parsing fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {e}")

@router.get("/", response_model=List[ResumePublic])
def list_resumes(session: SessionDep, current_user: CurrentUser):
    statement = select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.created_at.desc())
    return session.exec(statement).all()

@router.get("/{resume_id}", response_model=ResumePublic)
def get_resume(session: SessionDep, current_user: CurrentUser, resume_id: uuid.UUID):
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
