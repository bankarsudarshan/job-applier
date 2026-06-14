from pydantic import BaseModel, Field
from app.services.ai.llm_service import llm_service

class QuestionSimilarityResponse(BaseModel):
    similarity_score: float = Field(
        ...,
        description="Floating point value between 0.0 and 1.0 representing semantic equivalence."
    )
    is_similar: bool = Field(
        ...,
        description="True if the two questions ask for the same underlying information and can share the same answer."
    )

class QuestionSimilarity:
    def check_similarity(self, question_a: str, question_b: str) -> bool:
        prompt = (
            f"Compare the following two job application questions:\n"
            f"Question A: '{question_a}'\n"
            f"Question B: '{question_b}'\n\n"
            "Do they ask for the same information, meaning the answer to A would be a correct "
            "and sufficient answer to B?"
        )
        system_instruction = (
            "You are a semantic analyzer. Decide if two questions are functionally identical "
            "for the purpose of filling out a job application. Return a score and a boolean."
        )
        try:
            result = llm_service.generate_structured(
                prompt=prompt,
                response_schema=QuestionSimilarityResponse,
                system_instruction=system_instruction
            )
            # Threshold of 0.85 for semantic equivalence
            return result.is_similar and result.similarity_score >= 0.85
        except Exception:
            return False

question_similarity = QuestionSimilarity()
