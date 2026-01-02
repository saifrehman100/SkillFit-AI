"""
Job matching service for scoring resumes against job descriptions.
Uses LLMs to generate match scores, identify missing skills, and provide recommendations.
"""
from typing import Dict, List, Optional, Any
import json

from app.core.logging_config import get_logger
from app.services.ats_analyzer import ATSAnalyzer

logger = get_logger(__name__)


class JobMatcher:
    """Service for matching resumes to job descriptions."""

    MATCHING_PROMPT = """
You are an expert ATS (Applicant Tracking System) and recruiter analyzing resume-job fit. Your scoring must reflect how modern ATS systems and recruiters evaluate candidates.

**Resume:**
{resume_text}

**Job Description:**
{job_description}

**Your Task:** Provide a detailed, objective analysis of how well this resume matches the job requirements.

**SHARED SCORING CONTRACT (CRITICAL):**

All score changes MUST map to the Match Score Calculation rules.

Allowed score movements:
- Skills Match: max 40 points TOTAL
- Experience Relevance: max 30 points TOTAL
- Keyword Optimization: max 15 points TOTAL
- Achievements: max 10 points TOTAL
- Education: max 5 points TOTAL

If a category is already near its maximum, further improvements MUST NOT claim additional points.

Estimated improvements MUST:
- Reference a specific scoring category
- Respect category caps
- Avoid double-counting inferred skills

**Scoring Methodology - Apply This Systematically:**

**Match Score Calculation (0-100):**

1. **Skills Match (40 points maximum):**
   - Count required technical skills explicitly mentioned in resume (+4 points each, max 20)
   - Count preferred/nice-to-have skills present (+2 points each, max 10)
   - Related/transferable skills that demonstrate capability (+1 point each, max 10)
   - NOTE: Give credit if the skill is mentioned ANYWHERE in resume, not just skills section
   - Look for skills in job descriptions, achievements, tools used, technologies mentioned

2. **Experience Relevance (30 points maximum):**
   - Job titles/roles closely aligned with requirements (+10 points)
   - Years of experience meets or exceeds requirement (+10 points)
   - Industry/domain experience relevant (+10 points)
   - NOTE: Experience can be demonstrated through projects, achievements, not just job titles

3. **Keyword Optimization (15 points maximum):**
   - Resume uses exact terminology from job description (+8 points)
   - High density of relevant keywords throughout resume (+7 points)
   - This is critical for ATS parsing - exact matches count heavily

4. **Achievements & Impact (10 points maximum):**
   - Quantified achievements demonstrating relevant capabilities (+5 points)
   - Clear demonstration of responsibilities matching job needs (+5 points)

5. **Education & Certifications (5 points maximum):**
   - Education level meets requirements (+3 points)
   - Relevant certifications mentioned (+2 points)

**Scoring Ranges:**
- 90-100: Exceptional - Has ALL required skills + most preferred, perfect keyword match, strong relevant experience
- 75-89: Strong - Has 80%+ required skills, good keyword optimization, relevant experience
- 60-74: Good - Has 60-79% required skills, decent keyword match, some relevant experience
- 40-59: Moderate - Has 40-59% required skills, gaps exist but transferable skills present
- 0-39: Weak - Missing majority of required skills and experience

**Critical Instructions:**

**Skill Recognition Rules (Critical):**
1. **Explicit vs Inferred Skills**:
   - If a skill is EXPLICITLY mentioned (e.g., "Python" in skills section), count it and mark as "explicit"
   - If a skill is IMPLIED from context (e.g., used "automated scripts" implies scripting), count it but mark as "inferred"
   - Important: Converting inferred → explicit in a rewrite does NOT add Skills Match points, but may add Keyword Optimization points (if headroom exists)

2. **Accept Variants**: Treat reasonable variants as matches (React.js = React = ReactJS, leadership = team leadership)

3. **Don't Over-Penalize**: A resume can still score 75+ even if missing some preferred skills, if it has strong required skills and good keyword optimization.

4. **Consistency**: Two similar resumes should get similar scores. Use the point system above strictly.

**Output Requirements:**

1. **Missing Skills**: ONLY list skills that are:
   - Explicitly required in job description
   - Completely absent from resume (not mentioned anywhere)
   - Not inferable from related skills shown

2. **Actionable Recommendations**: Provide 5-7 specific recommendations with REALISTIC impact estimates:
   - Adding a critical missing skill: +8-15 points
   - Adding multiple related skills: +5-10 points
   - Improving keyword density: +5-8 points
   - Quantifying achievements: +3-5 points
   - Restructuring/formatting: +2-3 points

3. **Explanation**: Explain your score breakdown using the categories above.

Format your response as JSON with the following structure:
{{
    "match_score": <number 0-100>,
    "score_breakdown": {{
        "skills_match": {{
            "points": <number 0-40>,
            "required_skills_found": ["skill1", "skill2"],
            "required_skills_missing": ["skill3"],
            "preferred_skills_found": ["skill4"],
            "preferred_skills_missing": ["skill5"],
            "inferred_skills": ["skill6"]
        }},
        "experience_relevance": {{
            "points": <number 0-30>,
            "years_score": <number 0-10>,
            "role_score": <number 0-10>,
            "industry_score": <number 0-10>
        }},
        "keyword_optimization": {{
            "points": <number 0-15>,
            "keywords_found": ["keyword1", "keyword2"],
            "keywords_missing": ["keyword3"]
        }},
        "achievements": {{
            "points": <number 0-10>,
            "quantified_count": <number>
        }},
        "education": {{
            "points": <number 0-5>
        }}
    }},
    "score_headroom": {{
        "skills_match_remaining": <40 - skills_match_points>,
        "experience_remaining": <30 - experience_points>,
        "keyword_remaining": <15 - keyword_points>,
        "achievements_remaining": <10 - achievement_points>,
        "education_remaining": <5 - education_points>
    }},
    "missing_skills": ["skill1", "skill2", ...],
    "recommendations": [
        {{
            "action": "Add [specific skill] to skills section",
            "category_affected": "skills_match|keyword_optimization|achievements|etc",
            "current_category_score": <number>,
            "max_category_score": <number>,
            "realistic_point_gain": <number 0-10>,
            "priority": "High|Medium|Low",
            "reason": "Why this will help"
        }},
        ...
    ],
    "explanation": "Detailed explanation referencing score breakdown by category",
    "strengths": ["strength1", "strength2", ...],
    "weaknesses": ["weakness1", "weakness2", ...]
}}

**Important:**
- Be consistent and objective. Use the point system above strictly.
- Calculate realistic_point_gain considering category ceilings
- If a category is near max, don't suggest improvements for that category
- Show your work in the score_breakdown with actual lists of found/missing items
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

            # Run ATS analysis (in parallel with match scoring)
            try:
                ats_analyzer = ATSAnalyzer(self.llm_client)
                ats_result = ats_analyzer.analyze_ats_score(
                    resume_text=resume_text,
                    job_description=job_description
                )

                # Add ATS data to match results
                match_data["ats_score"] = ats_result["ats_score"]
                match_data["keyword_matches"] = ats_result["keyword_analysis"]

                # Transform issues into formatting_issues and missing_sections
                formatting_issues = []
                missing_sections = []
                for issue in ats_result.get("issues", []):
                    if isinstance(issue, dict):
                        issue_text = issue.get("issue", str(issue))
                        if issue.get("type") == "section":
                            missing_sections.append(issue_text)
                        else:
                            formatting_issues.append(issue_text)
                    else:
                        formatting_issues.append(str(issue))

                match_data["ats_issues"] = {
                    "formatting_score": ats_result["formatting_score"],
                    "section_score": ats_result["section_score"],
                    "contact_score": ats_result["contact_score"],
                    "formatting_issues": formatting_issues,
                    "missing_sections": missing_sections,
                    "recommendations": ats_result["recommendations"]
                }

                logger.info("ATS analysis included in match", ats_score=ats_result["ats_score"])

            except Exception as e:
                logger.error("ATS analysis failed, continuing without it", error=str(e))
                # Continue without ATS data if it fails
                match_data["ats_score"] = None
                match_data["keyword_matches"] = None
                match_data["ats_issues"] = None

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
