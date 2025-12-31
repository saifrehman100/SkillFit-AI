"""
Resume rewriting service for generating improved resume content.
Uses LLMs to rewrite resumes based on match recommendations and job requirements.
"""
from typing import Dict, Any, Optional, List
import json

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ResumeRewriter:
    """Service for rewriting and improving resume content."""

    REWRITE_PROMPT = """
You are an expert resume writer and career coach. Your task is to rewrite and improve this resume to better match the target job description.

**Original Resume:**
{resume_text}

**Target Job Description:**
{job_description}

**Current Match Score:** {match_score}%

**Recommendations to Address:**
{recommendations}

**Missing Skills to Incorporate (if applicable):**
{missing_skills}

Please generate an improved version of this resume that:
1. Addresses all the recommendations provided
2. Incorporates relevant missing skills where truthful and applicable
3. Improves the presentation and formatting
4. Uses stronger action verbs and quantifiable achievements
5. Tailors the content to match the job requirements better
6. Maintains truthfulness - DO NOT fabricate experience or skills

**Guidelines:**
- Keep the same overall structure (contact info, experience, education, skills)
- Enhance existing bullet points with stronger language and quantification
- Reorder or emphasize relevant experience for this job
- Add relevant keywords from the job description naturally
- Make achievements more impactful with metrics where possible
- DO NOT invent new jobs, skills, or qualifications
- Only suggest adding skills if they can be reasonably learned quickly

Format your response as JSON with the following structure:
{{
    "improved_resume": "The complete rewritten resume text",
    "changes_summary": [
        "Key change 1 description",
        "Key change 2 description",
        ...
    ],
    "estimated_new_score": <number 0-100>,
    "score_improvement": <number>,
    "key_improvements": [
        "Improvement 1",
        "Improvement 2",
        ...
    ]
}}

Be professional, honest, and focus on presenting existing qualifications in the best light.
"""

    QUICK_IMPROVE_PROMPT = """
Quick resume improvement: Rewrite this resume section to be more impactful.

Original: {resume_section}

Make it more compelling by:
- Using stronger action verbs
- Adding quantifiable results where possible
- Making it more concise and impactful

Return ONLY the improved version as plain text.
"""

    def __init__(self, llm_client):
        """
        Initialize rewriter with an LLM client.

        Args:
            llm_client: Instance of BaseLLMClient
        """
        self.llm_client = llm_client

    async def rewrite_resume(
        self,
        resume_text: str,
        job_description: str,
        match_score: float,
        recommendations: Optional[List[Dict[str, Any]]] = None,
        missing_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate an improved version of a resume.

        Args:
            resume_text: Original resume text
            job_description: Target job description
            match_score: Current match score (0-100)
            recommendations: List of improvement recommendations
            missing_skills: List of missing skills to address

        Returns:
            Dictionary with improved resume and analysis
        """
        try:
            logger.info(
                "Starting resume rewrite",
                match_score=match_score,
                num_recommendations=len(recommendations) if recommendations else 0
            )

            # Format recommendations
            if recommendations:
                rec_text = "\n".join([
                    f"- {rec.get('action', rec) if isinstance(rec, dict) else rec}"
                    for rec in recommendations
                ])
            else:
                rec_text = "No specific recommendations provided"

            # Format missing skills
            skills_text = ", ".join(missing_skills) if missing_skills else "None specified"

            prompt = self.REWRITE_PROMPT.format(
                resume_text=resume_text,
                job_description=job_description,
                match_score=match_score,
                recommendations=rec_text,
                missing_skills=skills_text
            )

            response = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,  # Balanced creativity and consistency
                max_tokens=4096
            )

            logger.info("Resume rewrite completed")

            # Parse JSON response
            result = self._parse_response(response.content)

            # Add metadata
            result["_metadata"] = {
                "model": response.model,
                "provider": response.provider,
                "tokens_used": response.tokens_used,
                "cost_estimate": response.cost_estimate,
            }

            return result

        except Exception as e:
            logger.error("Resume rewriting failed", error=str(e))
            raise

    async def improve_section(self, resume_section: str) -> str:
        """
        Quick improvement of a single resume section.

        Args:
            resume_section: Text of resume section to improve

        Returns:
            Improved version of the section
        """
        try:
            prompt = self.QUICK_IMPROVE_PROMPT.format(resume_section=resume_section)

            response = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )

            return response.content.strip()

        except Exception as e:
            logger.error("Section improvement failed", error=str(e))
            raise

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract JSON.

        Args:
            content: Raw LLM response

        Returns:
            Parsed data dictionary
        """
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())
            return data

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON response", error=str(e))
            # Return raw content if JSON parsing fails
            return {"improved_resume": content, "parse_error": str(e)}
