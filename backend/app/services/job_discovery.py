import logging
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.models.job import Job
from app.services.ai.embeddings import embeddings_service
from app.services.vector.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)

class JobDiscovery:
    def discover_jobs(self, session: Session) -> list[Job]:
        """
        Mock job discovery. In production this would scrape Greenhouse, Lever, Workday or LinkedIn.
        """
        mock_jobs = [
            {
                "title": "Software Engineer (FastAPI/React)",
                "company": "FastAPI Solutions",
                "location": "Remote, US",
                "description": "We are looking for a Software Engineer experienced in Python, FastAPI, SQLModel, and React. You will build high-quality web applications.",
                "url": "https://boards.greenhouse.io/fastapisolutions/jobs/101",
                "ats_type": "Greenhouse",
                "raw_data": {}
            },
            {
                "title": "Full Stack Developer",
                "company": "Leverage Tech",
                "location": "San Francisco, CA",
                "description": "Join our team to develop modern React frontends and Python services. Familiarity with PostgreSQL and Docker required.",
                "url": "https://jobs.lever.co/leveragetech/202",
                "ats_type": "Lever",
                "raw_data": {}
            },
            {
                "title": "Backend Python Engineer",
                "company": "DataStream",
                "location": "New York, NY",
                "description": "Build high-throughput APIs. Experience with database migrations, Postgres, async frameworks, and vector databases (Qdrant) is a big plus.",
                "url": "https://jobs.lever.co/datastream/303",
                "ats_type": "Lever",
                "raw_data": {}
            }
        ]

        discovered = []
        for job_data in mock_jobs:
            # Check if job already exists
            statement = select(Job).where(Job.url == job_data["url"])
            existing = session.exec(statement).first()
            if not existing:
                job = Job(
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    description=job_data["description"],
                    url=job_data["url"],
                    ats_type=job_data["ats_type"],
                    raw_data=job_data["raw_data"]
                )
                session.add(job)
                session.commit()
                session.refresh(job)
                discovered.append(job)

                # Index job description in Qdrant for matching
                try:
                    vector = embeddings_service.get_embedding(job.description)
                    qdrant_service.upsert_vector(
                        collection="jobs",
                        entity_id=str(job.id),
                        vector=vector,
                        payload={
                            "title": job.title,
                            "company": job.company,
                            "location": job.location
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to index job in Qdrant: {e}")
            else:
                discovered.append(existing)

        return discovered

job_discovery = JobDiscovery()
