from app.services.ai.llm_service import llm_service

class CoverLetterGenerator:
    def generate(self, profile_data: dict, job_title: str, company: str, job_description: str) -> str:
        personal_info = profile_data.get("personal_info", {})
        skills = profile_data.get("skills", [])
        experience = profile_data.get("experience", [])
        
        experience_summary = ""
        if experience:
            latest = experience[0]
            experience_summary = f"Currently a {latest.get('role')} at {latest.get('company')}."

        prompt = (
            f"Generate a customized cover letter for the following position:\n"
            f"Job Title: {job_title}\n"
            f"Company: {company}\n"
            f"Job Description: {job_description}\n\n"
            f"Applicant Info:\n"
            f"- Name: {personal_info.get('first_name', '')} {personal_info.get('last_name', '')}\n"
            f"- Skills: {', '.join(skills[:8])}\n"
            f"- Experience: {experience_summary}\n\n"
            "Write a concise, professional cover letter (around 200-250 words) highlighting "
            "how the applicant's skills align with the job description."
        )
        system_instruction = "You are an expert career counselor. Write persuasive, elegant, and professional cover letters."
        return llm_service.generate_text(
            prompt=prompt,
            system_instruction=system_instruction
        )

cover_letter_generator = CoverLetterGenerator()
