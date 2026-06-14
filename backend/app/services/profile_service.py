import logging
import uuid
from typing import Any
from sqlmodel import Session, select
from app.models.profile import Profile

logger = logging.getLogger(__name__)

class ProfileService:
    def get_by_user_id(self, session: Session, user_id: uuid.UUID) -> Profile | None:
        statement = select(Profile).where(Profile.user_id == user_id)
        return session.exec(statement).first()

    def create_or_update(self, session: Session, user_id: uuid.UUID, profile_data: dict) -> Profile:
        profile = self.get_by_user_id(session, user_id)
        if not profile:
            profile = Profile(
                user_id=user_id,
                personal_info=profile_data.get("personal_info", {}),
                education=profile_data.get("education", []),
                experience=profile_data.get("experience", []),
                skills=profile_data.get("skills", []),
                portfolio_links=profile_data.get("portfolio_links", []),
                preferences=profile_data.get("preferences", {})
            )
            session.add(profile)
        else:
            profile.personal_info = profile_data.get("personal_info", profile.personal_info)
            profile.education = profile_data.get("education", profile.education)
            profile.experience = profile_data.get("experience", profile.experience)
            profile.skills = profile_data.get("skills", profile.skills)
            profile.portfolio_links = profile_data.get("portfolio_links", profile.portfolio_links)
            profile.preferences = profile_data.get("preferences", profile.preferences)
            session.add(profile)

        session.commit()
        session.refresh(profile)
        return profile

    def get_profile_value_by_key(self, profile: Profile, key: str) -> Any | None:
        """
        Retrieves a value from the profile based on a canonical key.
        """
        personal = profile.personal_info or {}
        prefs = profile.preferences or {}
        
        # Exact field mapping
        if key == "first_name":
            return personal.get("first_name")
        elif key == "last_name":
            return personal.get("last_name")
        elif key == "full_name":
            return f"{personal.get('first_name', '')} {personal.get('last_name', '')}".strip() or None
        elif key == "email":
            return personal.get("email")
        elif key == "phone":
            return personal.get("phone")
        elif key == "address":
            return personal.get("address")
        elif key == "target_salary":
            return prefs.get("target_salary")
        elif key == "work_authorization":
            return prefs.get("work_authorization")
        elif key == "sponsorship_required":
            return prefs.get("sponsorship_required")

        # Search in portfolio links
        for link in (profile.portfolio_links or []):
            name = link.get("name", "").lower()
            if key == "github_url" and "github" in name:
                return link.get("url")
            elif key == "linkedin_url" and "linkedin" in name:
                return link.get("url")
            elif key == "portfolio_url" and ("portfolio" in name or "personal" in name):
                return link.get("url")
            elif key == "website_url" and "website" in name:
                return link.get("url")

        return None

profile_service = ProfileService()
