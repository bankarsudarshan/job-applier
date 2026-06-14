from typing import List
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from app.api.deps import SessionDep, CurrentUser
from app.models.job import Job
from app.services.job_discovery import job_discovery
from app.services.job_matching import job_matching

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobPublic(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    location: str
    description: str
    url: str
    ats_type: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class JobMatchPublic(BaseModel):
    job: JobPublic
    score: float

@router.get("/", response_model=List[JobPublic])
def list_jobs(session: SessionDep, current_user: CurrentUser):
    statement = select(Job).order_by(Job.created_at.desc())
    return session.exec(statement).all()

@router.post("/discover", response_model=List[JobPublic])
def discover_new_jobs(session: SessionDep, current_user: CurrentUser):
    # Runs the job crawler / discoverer
    jobs = job_discovery.discover_jobs(session)
    return jobs

@router.get("/match", response_model=List[JobMatchPublic])
def get_matched_jobs(session: SessionDep, current_user: CurrentUser):
    matches = job_matching.match_jobs_for_user(session, current_user.id)
    return matches

@router.get("/{job_id}", response_model=JobPublic)
def get_job(session: SessionDep, current_user: CurrentUser, job_id: uuid.UUID):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
