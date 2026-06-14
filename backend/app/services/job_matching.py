import logging
import uuid
from sqlmodel import Session, select
from app.models.job import Job
from app.models.resume import Resume
from app.services.ai.embeddings import embeddings_service
from app.services.vector.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)

class JobMatching:
    def match_jobs_for_user(self, session: Session, user_id: uuid.UUID, limit: int = 10) -> list[dict]:
        """
        Calculates compatibility scores for jobs using user resume embeddings.
        """
        # Get latest resume for user
        resume_statement = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
        latest_resume = session.exec(resume_statement).first()
        
        if not latest_resume:
            # Fallback: scan all jobs and return them with a base score
            logger.warning(f"No resume found for user {user_id}. Returning default scores.")
            jobs = session.exec(select(Job).limit(limit)).all()
            return [{"job": job, "score": 0.5} for job in jobs]

        try:
            # Get latest resume embedding
            query_vector = embeddings_service.get_embedding(latest_resume.raw_text)

            # Search similar jobs in Qdrant
            hits = qdrant_service.search_similar(
                collection="jobs",
                query_vector=query_vector,
                limit=limit
            )

            results = []
            for hit in hits:
                stmt = select(Job).where(Job.id == uuid.UUID(hit["id"]))
                job = session.exec(stmt).first()
                if job:
                    results.append({
                        "job": job,
                        "score": hit["score"]
                    })
            return results
        except Exception as e:
            logger.error(f"Error matching jobs in Qdrant: {e}. Falling back to default list.")
            jobs = session.exec(select(Job).limit(limit)).all()
            return [{"job": job, "score": 0.7} for job in jobs]

job_matching = JobMatching()
