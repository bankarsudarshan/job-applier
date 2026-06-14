from typing import List, Dict, Any
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.api.deps import SessionDep, CurrentUser
from app.models.application import Application, ApplicationField, ApplicationEvent
from app.models.job import Job
from app.services.application_service import application_service
from app.services.application_orchestrator import application_orchestrator

router = APIRouter(prefix="/applications", tags=["applications"])

class ApplicationFieldPublic(BaseModel):
    id: uuid.UUID
    field_name: str
    normalized_key: str
    field_type: str
    options: List[Dict[str, Any]]
    value: str | None
    is_required: bool
    resolved: bool

    class Config:
        from_attributes = True

class ApplicationEventPublic(BaseModel):
    id: uuid.UUID
    event_type: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True

class JobShortPublic(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    location: str

    class Config:
        from_attributes = True

class ApplicationPublic(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    job: JobShortPublic
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApplicationCreate(BaseModel):
    job_id: uuid.UUID

class FieldResolveInput(BaseModel):
    field_id: uuid.UUID
    value: str

@router.get("/", response_model=List[ApplicationPublic])
def list_applications(session: SessionDep, current_user: CurrentUser):
    return application_service.get_by_user_id(session, current_user.id)

@router.post("/", response_model=ApplicationPublic)
def create_application(
    session: SessionDep,
    current_user: CurrentUser,
    data: ApplicationCreate
):
    # Verify job exists
    job = session.get(Job, data.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    app = application_service.create_application(session, current_user.id, data.job_id)
    return app

@router.post("/{app_id}/start")
async def start_applying(
    app_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks
):
    app = application_service.get_by_id(session, app_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    # Start in background task or run synchronously to let frontend know quickly
    background_tasks.add_task(
        application_orchestrator.start_application,
        session=session,
        user_id=current_user.id,
        app_id=app_id
    )
    return {"message": "Application runner started in background."}

@router.get("/{app_id}/fields", response_model=List[ApplicationFieldPublic])
def get_application_fields(
    app_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
):
    app = application_service.get_by_id(session, app_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    return application_service.get_fields(session, app_id)

@router.post("/{app_id}/resolve")
async def resolve_application_fields(
    app_id: uuid.UUID,
    answers: List[FieldResolveInput],
    session: SessionDep,
    current_user: CurrentUser
):
    app = application_service.get_by_id(session, app_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    # Update field values in database
    for ans in answers:
        field = session.get(ApplicationField, ans.field_id)
        if field and field.application_id == app_id:
            field.value = ans.value
            field.resolved = True
            session.add(field)
    session.commit()

    # Re-orchestrate resolution
    updated_app = await application_orchestrator.resolve_fields(session, current_user.id, app_id)
    return {"status": updated_app.status}

@router.post("/{app_id}/submit")
async def submit_job_application(
    app_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks
):
    app = application_service.get_by_id(session, app_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    if app.status != "READY_TO_SUBMIT":
        raise HTTPException(status_code=400, detail="Application is not in READY_TO_SUBMIT state.")

    # Submit application in background task
    background_tasks.add_task(
        application_orchestrator.submit_application,
        session=session,
        user_id=current_user.id,
        app_id=app_id
    )
    return {"message": "Application submission started in background."}

@router.get("/{app_id}/events", response_model=List[ApplicationEventPublic])
def get_application_events(
    app_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
):
    app = application_service.get_by_id(session, app_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    return application_service.get_events(session, app_id)
