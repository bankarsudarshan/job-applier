import logging
import uuid
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.models.application import Application, ApplicationField, ApplicationEvent

logger = logging.getLogger(__name__)

class ApplicationService:
    def get_by_id(self, session: Session, application_id: uuid.UUID) -> Application | None:
        return session.get(Application, application_id)

    def get_by_user_id(self, session: Session, user_id: uuid.UUID) -> list[Application]:
        statement = select(Application).where(Application.user_id == user_id).order_by(Application.updated_at.desc())
        return session.exec(statement).all()

    def create_application(self, session: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> Application:
        app = Application(
            user_id=user_id,
            job_id=job_id,
            status="DRAFT"
        )
        session.add(app)
        session.commit()
        session.refresh(app)
        self.log_event(session, app.id, "STATUS_CHANGE", f"Application created. Status: {app.status}")
        return app

    def update_status(self, session: Session, app_id: uuid.UUID, status: str) -> Application:
        app = session.get(Application, app_id)
        if app:
            old_status = app.status
            app.status = status
            app.updated_at = datetime.now(timezone.utc)
            session.add(app)
            session.commit()
            session.refresh(app)
            self.log_event(session, app_id, "STATUS_CHANGE", f"Status updated from {old_status} to {status}")
        return app

    def save_fields(self, session: Session, app_id: uuid.UUID, fields: list[dict]) -> None:
        # Delete old fields first
        stmt = select(ApplicationField).where(ApplicationField.application_id == app_id)
        existing_fields = session.exec(stmt).all()
        for f in existing_fields:
            session.delete(f)
        session.commit()

        # Add new fields
        for f_data in fields:
            field = ApplicationField(
                application_id=app_id,
                field_name=f_data["field_name"],
                normalized_key=f_data["normalized_key"],
                field_type=f_data["field_type"],
                options=f_data.get("options", []),
                value=f_data.get("value"),
                is_required=f_data.get("is_required", False),
                resolved=f_data.get("resolved", False),
                selector=f_data.get("selector")
            )
            session.add(field)
        session.commit()

    def get_fields(self, session: Session, app_id: uuid.UUID) -> list[ApplicationField]:
        stmt = select(ApplicationField).where(ApplicationField.application_id == app_id)
        return session.exec(stmt).all()

    def log_event(self, session: Session, app_id: uuid.UUID, event_type: str, message: str) -> ApplicationEvent:
        event = ApplicationEvent(
            application_id=app_id,
            event_type=event_type,
            message=message
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event

    def get_events(self, session: Session, app_id: uuid.UUID) -> list[ApplicationEvent]:
        stmt = select(ApplicationEvent).where(ApplicationEvent.application_id == app_id).order_by(ApplicationEvent.created_at.asc())
        return session.exec(stmt).all()

application_service = ApplicationService()
