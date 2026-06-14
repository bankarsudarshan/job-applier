from pydantic import BaseModel, Field
from app.services.ai.llm_service import llm_service

class FieldMappingResponse(BaseModel):
    normalized_key: str = Field(
        ...,
        description=(
            "The closest matching canonical key from the list of available canonical options, "
            "or 'custom' if it does not fit any existing option."
        )
    )
    explanation: str = Field(..., description="Short explanation of why this mapping was chosen.")

CANONICAL_KEYS = [
    "first_name",
    "last_name",
    "full_name",
    "email",
    "phone",
    "address",
    "github_url",
    "linkedin_url",
    "portfolio_url",
    "website_url",
    "work_authorization",
    "sponsorship_required",
    "target_salary",
    "years_of_experience",
    "skills",
    "education_level",
    "gender",
    "race_ethnicity",
    "veteran_status",
    "disability_status",
    "cover_letter",
    "resume"
]

class FieldMapper:
    def map_field(self, field_label: str, field_type: str, options: list[str] | None = None) -> str:
        prompt = (
            f"Map the following web form field to one of our canonical fields:\n"
            f"Label: '{field_label}'\n"
            f"Type: '{field_type}'\n"
            f"Options: {options or 'None'}\n\n"
            f"Available Canonical Keys:\n"
            + "\n".join([f"- {key}" for key in CANONICAL_KEYS])
        )
        system_instruction = (
            "You are a database mapper. Analyze the form field label and map it to the "
            "most appropriate canonical key. If it doesn't match any, return 'custom'."
        )
        try:
            result = llm_service.generate_structured(
                prompt=prompt,
                response_schema=FieldMappingResponse,
                system_instruction=system_instruction
            )
            return result.normalized_key
        except Exception:
            return "custom"

field_mapper = FieldMapper()
