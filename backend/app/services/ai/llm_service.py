import json
import logging
from typing import Any, Type, TypeVar
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)

# Try importing generativeai
try:
    import google.generativeai as genai
    HAS_GENAI = True
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
except ImportError:
    HAS_GENAI = False

T = TypeVar("T", bound=BaseModel)

class LLMService:
    def __init__(self) -> None:
        self.api_key_configured = bool(settings.GEMINI_API_KEY) and HAS_GENAI
        if self.api_key_configured:
            logger.info("Gemini LLM Service initialized with API key.")
        else:
            logger.warning("Gemini API key not configured or google-generativeai not installed. Running in MOCK mode.")

    def generate_text(self, prompt: str, system_instruction: str | None = None) -> str:
        if not self.api_key_configured:
            return self._mock_generate_text(prompt)
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API generation error: {e}. Falling back to mock.")
            return self._mock_generate_text(prompt)

    def generate_structured(self, prompt: str, response_schema: Type[T], system_instruction: str | None = None) -> T:
        if not self.api_key_configured:
            return self._mock_structured(prompt, response_schema)
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_instruction
            )
            # Use Gemini structured outputs if supported, otherwise normal JSON prompting
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema
                )
            )
            return response_schema.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Structured Gemini API error: {e}. Attempting raw JSON parse fallback.")
            try:
                # Basic JSON prompt fallback
                fallback_model = genai.GenerativeModel("gemini-1.5-flash")
                json_prompt = f"{prompt}\n\nReturn the output STRICTLY as a JSON object matching this schema: {response_schema.model_json_schema()}"
                response = fallback_model.generate_content(json_prompt)
                text = response.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                return response_schema.model_validate_json(text)
            except Exception as inner_e:
                logger.error(f"Fallback JSON parsing failed: {inner_e}. Using mock.")
                return self._mock_structured(prompt, response_schema)

    def _mock_generate_text(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "cover letter" in prompt_lower:
            return (
                "Dear Hiring Manager,\n\n"
                "I am excited to apply for this position. Based on my experience, I believe "
                "I would make a great fit for your team. I look forward to discussing how "
                "my skills align with your requirements.\n\n"
                "Best regards,\nApplicant"
            )
        return "Mock Gemini response for prompt: " + prompt[:50] + "..."

    def _mock_structured(self, prompt: str, response_schema: Type[T]) -> T:
        # Generate basic dummy mock object matching the requested schema
        schema = response_schema.model_json_schema()
        properties = schema.get("properties", {})
        mock_data = {}
        for prop_name, prop_val in properties.items():
            prop_type = prop_val.get("type")
            if prop_type == "string":
                mock_data[prop_name] = f"Mock {prop_name}"
            elif prop_type == "array":
                mock_data[prop_name] = []
            elif prop_type == "object":
                mock_data[prop_name] = {}
            elif prop_type == "boolean":
                mock_data[prop_name] = False
            elif prop_type == "integer" or prop_type == "number":
                mock_data[prop_name] = 0

        # Custom tailored mock data injection depending on expected schema properties
        if "personal_info" in properties:
            mock_data["personal_info"] = {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "address": "123 Main St, Anytown, USA"
            }
            mock_data["skills"] = ["Python", "FastAPI", "React", "TypeScript"]
            mock_data["education"] = [
                {
                    "institution": "State University",
                    "degree": "B.S. Computer Science",
                    "start_date": "2018-09-01",
                    "end_date": "2022-05-30"
                }
            ]
            mock_data["experience"] = [
                {
                    "company": "Tech Corp",
                    "role": "Software Engineer",
                    "description": "Developed web applications.",
                    "start_date": "2022-06-01",
                    "end_date": "2024-05-01"
                }
            ]
            mock_data["portfolio_links"] = [
                {"name": "GitHub", "url": "https://github.com/johndoe"},
                {"name": "LinkedIn", "url": "https://linkedin.com/in/johndoe"}
            ]
            mock_data["preferences"] = {
                "roles": ["Software Engineer", "Full Stack Developer"],
                "target_salary": 120000,
                "work_authorization": "Authorized to work in US"
            }
        elif "normalized_key" in properties:
            mock_data["normalized_key"] = "work_authorization"
            mock_data["explanation"] = "Field refers to legal work status."
        elif "similarity_score" in properties:
            mock_data["similarity_score"] = 0.95
            mock_data["is_similar"] = True

        return response_schema.model_validate(mock_data)

llm_service = LLMService()
