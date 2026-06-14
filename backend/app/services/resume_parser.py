import logging
import os
import uuid
from io import BytesIO
from sqlmodel import Session
from app.models.resume import Resume
from app.services.ai.resume_extractor import resume_extractor
from app.services.ai.embeddings import embeddings_service
from app.services.vector.qdrant_service import qdrant_service
from app.services.profile_service import profile_service

logger = logging.getLogger(__name__)

# Try importing pypdf
try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

class ResumeParser:
    def extract_text(self, file_content: bytes, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            if not HAS_PYPDF:
                logger.error("pypdf not installed. Cannot parse PDF.")
                return "Mock PDF content for: " + filename
            try:
                reader = PdfReader(BytesIO(file_content))
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()
            except Exception as e:
                logger.error(f"Error parsing PDF file {filename}: {e}")
                return ""
        elif ext in [".txt", ".md"]:
            try:
                return file_content.decode("utf-8")
            except Exception as e:
                logger.error(f"Error decoding text file {filename}: {e}")
                return ""
        else:
            logger.warning(f"Unsupported file format {ext} for resume. Returning empty.")
            return ""

    def parse_and_save(self, session: Session, user_id: uuid.UUID, file_content: bytes, filename: str, file_path: str) -> Resume:
        # 1. Extract text
        raw_text = self.extract_text(file_content, filename)
        if not raw_text:
            raw_text = "Empty Resume"

        # 2. Extract structured profile using LLM
        structured_profile = resume_extractor.extract_profile(raw_text)

        # 3. Save to Resume table
        db_resume = Resume(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            raw_text=raw_text,
            parsed_data=structured_profile.model_dump()
        )
        session.add(db_resume)
        session.commit()
        session.refresh(db_resume)

        # 4. Upsert/update Profile
        profile_service.create_or_update(
            session=session,
            user_id=user_id,
            profile_data=structured_profile.model_dump()
        )

        # 5. Generate embedding & save to Qdrant vector database
        try:
            embedding = embeddings_service.get_embedding(raw_text)
            qdrant_service.upsert_vector(
                collection="resumes",
                entity_id=str(db_resume.id),
                vector=embedding,
                payload={
                    "user_id": str(user_id),
                    "filename": filename
                }
            )
            logger.info(f"Resume {filename} successfully indexed in Qdrant.")
        except Exception as q_err:
            logger.error(f"Failed to index resume in Qdrant: {q_err}")

        return db_resume

resume_parser = ResumeParser()
