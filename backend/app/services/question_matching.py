import logging
import uuid
from sqlmodel import Session, select
from app.models.question_memory import QuestionMemory
from app.services.ai.question_similarity import question_similarity
from app.services.ai.embeddings import embeddings_service
from app.services.vector.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)

class QuestionMatching:
    def find_matching_answer(self, session: Session, user_id: uuid.UUID, question: str) -> str | None:
        """
        Looks up similar answered questions using vector search first, then falls back to full database scan.
        """
        # Generate embedding for the question
        query_vector = embeddings_service.get_embedding(question)

        # 1. Search in Qdrant first
        try:
            hits = qdrant_service.search_similar(
                collection="questions",
                query_vector=query_vector,
                limit=3
            )
            for hit in hits:
                payload = hit.get("payload", {})
                if payload.get("user_id") == str(user_id) and hit.get("score", 0.0) >= 0.85:
                    # Double check semantic match via LLM
                    stored_q = payload.get("question", "")
                    if stored_q and question_similarity.check_similarity(question, stored_q):
                        # Load from DB to ensure we get current answer
                        stmt = select(QuestionMemory).where(QuestionMemory.id == uuid.UUID(hit["id"]))
                        mem = session.exec(stmt).first()
                        if mem:
                            logger.info(f"Vector match found for question: '{question}' -> '{mem.question}'")
                            return mem.answer
        except Exception as e:
            logger.error(f"Error searching question vector: {e}")

        # 2. Database scan fallback with semantic check
        statement = select(QuestionMemory).where(QuestionMemory.user_id == user_id)
        memories = session.exec(statement).all()
        for mem in memories:
            if question_similarity.check_similarity(question, mem.question):
                logger.info(f"DB scan semantic match found for question: '{question}' -> '{mem.question}'")
                return mem.answer

        return None

    def save_answer(self, session: Session, user_id: uuid.UUID, question: str, normalized_key: str, answer: str) -> QuestionMemory:
        # Check if identical question already exists
        statement = select(QuestionMemory).where(
            QuestionMemory.user_id == user_id,
            QuestionMemory.question == question
        )
        existing = session.exec(statement).first()
        if existing:
            existing.answer = answer
            session.add(existing)
            db_obj = existing
        else:
            db_obj = QuestionMemory(
                user_id=user_id,
                question=question,
                normalized_key=normalized_key,
                answer=answer
            )
            session.add(db_obj)
        
        session.commit()
        session.refresh(db_obj)

        # Save to Qdrant vector database
        try:
            vector = embeddings_service.get_embedding(question)
            qdrant_service.upsert_vector(
                collection="questions",
                entity_id=str(db_obj.id),
                vector=vector,
                payload={
                    "user_id": str(user_id),
                    "question": question,
                    "normalized_key": normalized_key
                }
            )
        except Exception as e:
            logger.error(f"Failed to upsert question memory to Qdrant: {e}")

        return db_obj

question_matching = QuestionMatching()
