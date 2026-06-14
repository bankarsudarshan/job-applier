import uuid
import pytest
from sqlmodel import Session
from app.models.job import Job
from app.models.profile import Profile
from app.models.application import Application, ApplicationField
from app.services.resume_parser import resume_parser
from app.services.question_matching import question_matching
from app.services.job_discovery import job_discovery
from app.services.job_matching import job_matching
from app.services.application_service import application_service
from app.services.application_orchestrator import application_orchestrator
from tests.utils.user import create_random_user

def test_resume_parser_and_profile(db: Session) -> None:
    # 1. Create a random user
    user = create_random_user(db)
    
    # 2. Mock resume PDF parse and save
    resume_content = b"John Doe\nEmail: john@example.com\nSkills: Python, FastAPI\nEducation: BS CS"
    db_resume = resume_parser.parse_and_save(
        session=db,
        user_id=user.id,
        file_content=resume_content,
        filename="resume.txt",
        file_path="/tmp/resume.txt"
    )
    
    assert db_resume.id is not None
    assert db_resume.filename == "resume.txt"
    assert db_resume.raw_text == resume_content.decode()

    # 3. Check profile was created
    profile = db.query(Profile).filter_by(user_id=user.id).first()
    assert profile is not None
    assert "Python" in profile.skills or len(profile.skills) > 0

def test_question_matching(db: Session) -> None:
    user = create_random_user(db)
    
    # Save a question answer memory
    question = "Are you authorized to work in the United States?"
    answer = "Yes, I am a US citizen"
    mem = question_matching.save_answer(
        session=db,
        user_id=user.id,
        question=question,
        normalized_key="work_authorization",
        answer=answer
    )
    
    assert mem.id is not None
    assert mem.answer == answer

    # Match exact same question
    matched_answer = question_matching.find_matching_answer(db, user.id, question)
    assert matched_answer == answer

    # Match semantically similar question (using mock semantic search fallback since api key not set in tests)
    similar_question = "Do you have US work authorization?"
    # The mock fallback in question_similarity.py returns True for similarity check if API key is missing
    # or if it's evaluated similarly. In test environment, the fallback checks work.
    matched_similar = question_matching.find_matching_answer(db, user.id, similar_question)
    assert matched_similar is not None

def test_job_discovery_and_matching(db: Session) -> None:
    user = create_random_user(db)
    
    # Discover jobs
    jobs = job_discovery.discover_jobs(db)
    assert len(jobs) > 0
    
    # Calculate matches for the user
    matches = job_matching.match_jobs_for_user(db, user.id)
    assert len(matches) > 0
    assert matches[0]["score"] is not None

@pytest.mark.anyio
async def test_application_orchestrator_workflow(db: Session) -> None:
    user = create_random_user(db)
    
    # 1. Discover jobs to have one in DB
    jobs = job_discovery.discover_jobs(db)
    job = jobs[0]
    
    # 2. Create draft application
    app = application_service.create_application(db, user.id, job.id)
    assert app.status == "DRAFT"
    
    # 3. Start application orchestration (which extracts and resolves fields)
    updated_app = await application_orchestrator.start_application(db, user.id, app.id)
    
    # Since the user profile might be empty, some required fields will be unresolved,
    # putting the application into WAITING_FOR_USER status
    assert updated_app.status in ["WAITING_FOR_USER", "READY_TO_SUBMIT"]
    
    fields = application_service.get_fields(db, app.id)
    assert len(fields) > 0

    # 4. Save answers to resolve outstanding fields
    unresolved = [f for f in fields if not f.resolved]
    answers_list = []
    for f in unresolved:
        f.value = "Test Answer"
        f.resolved = True
        db.add(f)
    db.commit()

    # Re-evaluate
    resolved_app = await application_orchestrator.resolve_fields(db, user.id, app.id)
    assert resolved_app.status == "READY_TO_SUBMIT"

    # 5. Submit application
    final_app = await application_orchestrator.submit_application(db, user.id, app.id)
    assert final_app.status == "SUBMITTED"
