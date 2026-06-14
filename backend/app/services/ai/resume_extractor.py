from typing import Any, List
from pydantic import BaseModel, Field
from app.services.ai.llm_service import llm_service

# Structured Schemas for the LLM output
class PersonalInfoSchema(BaseModel):
    first_name: str = Field(default="", description="First name of the applicant")
    last_name: str = Field(default="", description="Last name of the applicant")
    email: str = Field(default="", description="Contact email address")
    phone: str = Field(default="", description="Phone number")
    address: str = Field(default="", description="Home address or current location")

class EducationEntrySchema(BaseModel):
    institution: str = Field(..., description="Name of university, college, or school")
    degree: str = Field(..., description="Degree obtained, e.g. B.S. in Computer Science")
    start_date: str | None = Field(default=None, description="Start date, e.g. YYYY-MM or Year")
    end_date: str | None = Field(default=None, description="End date, graduation date, or 'Present'")

class ExperienceEntrySchema(BaseModel):
    company: str = Field(..., description="Name of the company or organization")
    role: str = Field(..., description="Job title / role")
    description: str = Field(default="", description="Key responsibilities and achievements")
    start_date: str | None = Field(default=None, description="Start date, e.g. YYYY-MM")
    end_date: str | None = Field(default=None, description="End date or 'Present'")

class PortfolioLinkSchema(BaseModel):
    name: str = Field(..., description="Platform name, e.g. GitHub, LinkedIn, Personal Website")
    url: str = Field(..., description="Link URL")

class PreferencesSchema(BaseModel):
    roles: List[str] = Field(default_factory=list, description="Preferred job titles")
    target_salary: int | None = Field(default=None, description="Target annual salary in USD")
    work_authorization: str | None = Field(default=None, description="Citizenship or work auth status, e.g. US Citizen, H1B, etc.")

class ResumeProfileSchema(BaseModel):
    personal_info: PersonalInfoSchema
    education: List[EducationEntrySchema] = Field(default_factory=list)
    experience: List[ExperienceEntrySchema] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list, description="List of technical and professional skills")
    portfolio_links: List[PortfolioLinkSchema] = Field(default_factory=list)
    preferences: PreferencesSchema

class ResumeExtractor:
    def extract_profile(self, resume_text: str) -> ResumeProfileSchema:
        prompt = (
            "Analyze the following resume text and extract all information into the structured schema. "
            "Make sure to extract skills, education, experiences, portfolio links, and preferences accurately.\n\n"
            f"Resume Text:\n{resume_text}"
        )
        system_instruction = "You are a professional resume parser. Extract information exactly as presented and format it as structured JSON."
        return llm_service.generate_structured(
            prompt=prompt,
            response_schema=ResumeProfileSchema,
            system_instruction=system_instruction
        )

resume_extractor = ResumeExtractor()
