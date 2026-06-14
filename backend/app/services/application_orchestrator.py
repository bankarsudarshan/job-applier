import logging
import os
import uuid
from sqlmodel import Session, select
from app.models.application import Application, ApplicationField
from app.models.job import Job
from app.models.resume import Resume
from app.services.application_service import application_service
from app.services.profile_service import profile_service
from app.services.question_matching import question_matching
from app.services.ai.field_mapper import field_mapper
from app.services.browser.application_runner import application_runner

logger = logging.getLogger(__name__)

class ApplicationOrchestrator:
    async def start_application(self, session: Session, user_id: uuid.UUID, app_id: uuid.UUID) -> Application:
        """
        Starts the application runner, fetches form fields, resolves them.
        """
        app = application_service.get_by_id(session, app_id)
        if not app:
            raise ValueError(f"Application {app_id} not found.")

        application_service.update_status(session, app_id, "IN_PROGRESS")
        application_service.log_event(session, app_id, "INFO", "Fetching job application form fields...")

        # Fetch job URL
        job = session.get(Job, app.job_id)
        if not job:
            application_service.update_status(session, app_id, "FAILED")
            application_service.log_event(session, app_id, "ERROR", "Job details not found.")
            return app

        # 1. Open browser and parse fields
        ats_type, fields = await application_runner.extract_fields_from_url(job.url)
        
        # Save ATS type back to job if it wasn't set
        if ats_type and not job.ats_type:
            job.ats_type = ats_type
            session.add(job)
            session.commit()

        # 2. Save fields to DB
        application_service.save_fields(session, app_id, fields)
        application_service.log_event(session, app_id, "INFO", f"Discovered {len(fields)} fields from form.")

        # 3. Resolve fields
        return await self.resolve_fields(session, user_id, app_id)

    async def resolve_fields(self, session: Session, user_id: uuid.UUID, app_id: uuid.UUID) -> Application:
        """
        Attempts to fill form fields using Profile and QuestionMemory.
        If required fields are missing, puts application in WAITING_FOR_USER.
        """
        app = application_service.get_by_id(session, app_id)
        if not app:
            raise ValueError("Application not found.")

        profile = profile_service.get_by_user_id(session, user_id)
        fields = application_service.get_fields(session, app_id)

        missing_required = False

        for field in fields:
            # Skip if already resolved
            if field.resolved:
                continue

            # 1. Map label to canonical key
            if not field.normalized_key or field.normalized_key == "custom":
                field.normalized_key = field_mapper.map_field(field.field_name, field.field_type, field.options)

            # 2. Try resolving using User Profile
            resolved_value = None
            if profile:
                resolved_value = profile_service.get_profile_value_by_key(profile, field.normalized_key)

            # 3. Try resolving using QuestionMemory
            if not resolved_value:
                resolved_value = question_matching.find_matching_answer(session, user_id, field.field_name)

            # 4. Handle file upload (resume/cover letter)
            if not resolved_value and field.field_type == "file":
                if "resume" in field.normalized_key or "resume" in field.field_name.lower():
                    # Get latest resume
                    stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
                    latest_resume = session.exec(stmt).first()
                    if latest_resume:
                        resolved_value = latest_resume.file_path

            # 5. Set field value if resolved
            if resolved_value is not None:
                field.value = str(resolved_value)
                field.resolved = True
                session.add(field)
            else:
                if field.is_required:
                    missing_required = True
                    field.resolved = False
                    session.add(field)

        session.commit()

        if missing_required:
            application_service.update_status(session, app_id, "WAITING_FOR_USER")
            application_service.log_event(
                session,
                app_id,
                "WARNING",
                "Application paused. Some required questions require your attention."
            )
        else:
            application_service.update_status(session, app_id, "READY_TO_SUBMIT")
            application_service.log_event(session, app_id, "INFO", "All required fields resolved. Ready to submit.")

        return app

    async def submit_application(self, session: Session, user_id: uuid.UUID, app_id: uuid.UUID) -> Application:
        """
        Submits the application using the browser automation driver.
        """
        app = application_service.get_by_id(session, app_id)
        if not app:
            raise ValueError("Application not found.")

        if app.status != "READY_TO_SUBMIT":
            # Re-verify resolve status
            app = await self.resolve_fields(session, user_id, app_id)
            if app.status != "READY_TO_SUBMIT":
                application_service.log_event(session, app_id, "ERROR", "Cannot submit application with missing fields.")
                return app

        application_service.log_event(session, app_id, "INFO", "Submitting application...")

        job = session.get(Job, app.job_id)
        fields = application_service.get_fields(session, app_id)

        # Build list of fields to pass to runner
        fields_list = [
            {
                "field_name": f.field_name,
                "selector": f.selector or f"[name='{f.normalized_key}']",
                "field_type": f.field_type,
                "value": f.value
            }
            for f in fields
        ]

        # File upload support
        resume_path = None
        for f in fields:
            if f.field_type == "file" and f.value:
                resume_path = f.value
                break

        # Run Playwright submit
        success = await application_runner.submit_application(
            url=job.url,
            fields=fields_list,
            resume_path=resume_path
        )

        if success:
            application_service.update_status(session, app_id, "SUBMITTED")
            application_service.log_event(session, app_id, "INFO", "Application submitted successfully!")
            
            # Save newly answered questions to QuestionMemory for future reuse
            for f in fields:
                if f.value and not f.field_type == "file":
                    question_matching.save_answer(
                        session=session,
                        user_id=user_id,
                        question=f.field_name,
                        normalized_key=f.normalized_key,
                        answer=f.value
                    )
        else:
            application_service.update_status(session, app_id, "FAILED")
            application_service.log_event(session, app_id, "ERROR", "Browser automation failed during submission.")

        return app

application_orchestrator = ApplicationOrchestrator()
