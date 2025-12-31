"""
Job matching service for scoring resumes against job descriptions.
Uses LLMs to generate match scores, identify missing skills, and provide recommendations.
"""
from typing import Dict, List, Optional, Any
import json

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class JobMatcher:
    """Service for matching resumes to job descriptions."""

    MATCHING_PROMPT = """
You are an expert recruiter and career advisor. Analyze how well this resume matches the job description.

**Resume:**
{resume_text}

**Job Description:**
{job_description}

Provide a comprehensive matching analysis with the following:

1. **Match Score (0-100)**: An overall compatibility score where:
   - 90-100: Exceptional match, candidate exceeds requirements
   - 75-89: Strong match, candidate meets most requirements
   - 60-74: Good match, candidate meets core requirements
   - 40-59: Partial match, candidate has relevant experience but gaps exist
   - 0-39: Poor match, significant gaps in qualifications

2. **Missing Skills**: List specific skills, qualifications, or experience mentioned in the job description that are not evident in the resume

3. **Actionable Recommendations**: Provide 5-7 specific, actionable recommendations for the candidate to improve their fit for this role. For EACH recommendation, include:
   - The specific action they should take
   - Priority level (High/Medium/Low)
   - Estimated impact on match score (+5 to +20 points)
   - Why this will help

4. **Explanation**: Provide a detailed explanation (2-3 paragraphs) of:
   - Why you gave this score
   - What the candidate does well
   - What the candidate needs to improve
   - How competitive they would be for this position

5. **Strengths**: List 3-5 key strengths that make this candidate suitable for the role

6. **Weaknesses**: List 3-5 key weaknesses or gaps that might hurt the candidate's chances

Format your response as JSON with the following structure:
{{
    "match_score": <number 0-100>,
    "missing_skills": ["skill1", "skill2", ...],
    "recommendations": [
        {{
            "action": "Specific action to take",
            "priority": "High|Medium|Low",
            "impact_estimate": <number 5-20>,
            "reason": "Why this will help"
        }},
        ...
    ],
    "explanation": "Detailed explanation text",
    "strengths": ["strength1", "strength2", ...],
    "weaknesses": ["weakness1", "weakness2", ...]
}}

Be honest and objective in your assessment. Focus on factual analysis rather than encouragement.
"""

    QUICK_MATCH_PROMPT = """
Quick analysis: Score this resume (0-100) against the job description.

Resume: {resume_text}

Job: {job_description}

Respond with ONLY a JSON object:
{{
    "match_score": <number>,
    "top_3_missing_skills": ["skill1", "skill2", "skill3"],
    "one_sentence_summary": "Brief summary of the match"
}}
"""

    def __init__(self, llm_client):
        """
        Initialize matcher with an LLM client.

        Args:
            llm_client: Instance of BaseLLMClient
        """
        self.llm_client = llm_client

    async def match(
        self,
        resume_text: str,
        job_description: str,
        detailed: bool = True
    ) -> Dict[str, Any]:
        """
        Match a resume against a job description.

        Args:
            resume_text: Extracted resume text
            job_description: Job description text
            detailed: If True, provide detailed analysis. If False, quick match.

        Returns:
            Matching results dictionary
        """
        try:
            logger.info(
                "Starting job match",
                detailed=detailed,
                resume_length=len(resume_text),
                job_length=len(job_description)
            )

            if detailed:
                prompt = self.MATCHING_PROMPT.format(
                    resume_text=resume_text,
                    job_description=job_description
                )
                max_tokens = 3000
            else:
                prompt = self.QUICK_MATCH_PROMPT.format(
                    resume_text=resume_text,
                    job_description=job_description
                )
                max_tokens = 500

            response = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.2,  # Lower temperature for more consistent scoring
                max_tokens=max_tokens
            )

            logger.info("Job match analysis completed")

            # Parse JSON response
            match_data = self._parse_response(response.content)

            # Add metadata
            match_data["_metadata"] = {
                "model": response.model,
                "provider": response.provider,
                "tokens_used": response.tokens_used,
                "cost_estimate": response.cost_estimate,
                "detailed": detailed
            }

            # Validate match score
            if "match_score" in match_data:
                match_data["match_score"] = max(0, min(100, match_data["match_score"]))

            return match_data

        except Exception as e:
            logger.error("Job matching failed", error=str(e))
            raise

    async def batch_match(
        self,
        resume_texts: List[str],
        job_description: str,
        detailed: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Match multiple resumes against a single job description.

        Args:
            resume_texts: List of resume texts
            job_description: Job description text
            detailed: If True, provide detailed analysis for each

        Returns:
            List of matching results
        """
        results = []

        logger.info(
            "Starting batch match",
            num_resumes=len(resume_texts),
            detailed=detailed
        )

        for idx, resume_text in enumerate(resume_texts):
            try:
                logger.info(f"Matching resume {idx + 1}/{len(resume_texts)}")
                result = await self.match(resume_text, job_description, detailed)
                result["resume_index"] = idx
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to match resume {idx}", error=str(e))
                results.append({
                    "resume_index": idx,
                    "error": str(e),
                    "match_score": 0
                })

        # Sort by match score descending
        results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

        logger.info("Batch match completed", successful=len(results))

        return results

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
            return {"raw_response": content, "parse_error": str(e)}


class SkillExtractor:
    """Service for extracting skills from job descriptions."""

    EXTRACTION_PROMPT = """
Extract all required and preferred skills from this job description.

Job Description:
{job_description}

Categorize skills into:
1. **Technical Skills**: Programming languages, frameworks, tools, technologies
2. **Soft Skills**: Communication, leadership, teamwork, etc.
3. **Domain Knowledge**: Industry-specific knowledge and expertise
4. **Certifications**: Required or preferred certifications
5. **Experience Level**: Years of experience required

Format as JSON:
{{
    "technical_skills": {{
        "required": ["skill1", "skill2"],
        "preferred": ["skill3", "skill4"]
    }},
    "soft_skills": ["skill1", "skill2"],
    "domain_knowledge": ["knowledge1", "knowledge2"],
    "certifications": ["cert1", "cert2"],
    "experience_level": {{
        "minimum_years": <number>,
        "preferred_years": <number>,
        "level": "entry/mid/senior"
    }}
}}
"""

    def __init__(self, llm_client):
        """Initialize extractor with an LLM client."""
        self.llm_client = llm_client

    async def extract_skills(self, job_description: str) -> Dict[str, Any]:
        """
        Extract structured skills from job description.

        Args:
            job_description: Job description text

        Returns:
            Structured skills data
        """
        try:
            logger.info("Extracting skills from job description")

            prompt = self.EXTRACTION_PROMPT.format(job_description=job_description)

            response = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2000
            )

            # Parse response
            if "```json" in response.content:
                content = response.content.split("```json")[1].split("```")[0]
            elif "```" in response.content:
                content = response.content.split("```")[1].split("```")[0]
            else:
                content = response.content

            skills_data = json.loads(content.strip())

            logger.info("Skills extracted successfully")

            return skills_data

        except Exception as e:
            logger.error("Skill extraction failed", error=str(e))
            raise
