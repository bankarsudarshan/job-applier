from fastapi import APIRouter, HTTPException
from app.api.deps import SessionDep, CurrentUser
from app.schemas.profile import ProfilePublic, ProfileCreate, ProfileUpdate
from app.services.profile_service import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/me", response_model=ProfilePublic)
def get_my_profile(session: SessionDep, current_user: CurrentUser):
    profile = profile_service.get_by_user_id(session, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/me", response_model=ProfilePublic)
def update_my_profile(
    session: SessionDep,
    current_user: CurrentUser,
    profile_in: ProfileUpdate
):
    profile = profile_service.create_or_update(
        session=session,
        user_id=current_user.id,
        profile_data=profile_in.model_dump()
    )
    return profile
