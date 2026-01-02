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
You are an expert resume writer and ATS optimization specialist. Your task is to strategically rewrite this resume to maximize the match score using the EXACT SAME scoring system the Job Matcher uses.

**Original Resume:**
{resume_text}

**Target Job Description:**
{job_description}

**Current Match Score:** {match_score}/100

**Current Score Breakdown:**
{score_breakdown}

**Recommendations to Address:**
{recommendations}

**Missing Skills:**
{missing_skills}

**SHARED SCORING CONTRACT (CRITICAL):**

All score changes MUST map to the Match Score Calculation rules.

Allowed score movements:
- Skills Match: max 40 points TOTAL
- Experience Relevance: max 30 points TOTAL
- Keyword Optimization: max 15 points TOTAL
- Achievements: max 10 points TOTAL
- Education: max 5 points TOTAL

If a category is already near its maximum, further improvements MUST NOT claim additional points.

**Your Goal:** Analyze the score breakdown to identify WHERE points can be gained, then rewrite the resume to capture those points.

**Critical Instructions - Follow These Exactly:**

1. **PRIORITIZE MISSING SKILLS** - This is the #1 factor affecting match score:
   - If a missing skill can be reasonably inferred from existing experience, ADD IT to the skills section
   - If candidate used related technologies, explicitly mention the missing skill variants
   - Example: If they used "JavaScript" and "React Native" is missing, add "React Native" if mobile development is shown
   - Example: If they show "leadership" experience but "team leadership" is missing, add that phrase
   - Add relevant missing keywords from the job description throughout the resume naturally
   - Transform generic experience into specific skills the job requires

2. **MATCH JOB DESCRIPTION LANGUAGE EXACTLY**:
   - Use the EXACT terminology from the job description, not synonyms
   - If job says "customer success" don't say "client relations" - use "customer success"
   - Mirror the job's phrasing for technical skills, tools, and responsibilities
   - This is critical for ATS keyword matching

3. **QUANTIFY AND STRENGTHEN ACHIEVEMENTS**:
   - Add metrics to every bullet point possible (%, $, #, time saved)
   - Use power verbs that match the seniority level required
   - Make accomplishments directly relevant to the job requirements

4. **STRATEGIC RESTRUCTURING**:
   - Lead with most relevant experience for THIS specific job
   - Move less relevant experience lower or condense it
   - Ensure skills section prominently features all required/preferred job skills candidate has touched
   - Add a professional summary if missing, highlighting alignment with job

5. **MAINTAIN TRUTHFULNESS** (Critical Constraint):
   - NEVER fabricate jobs, degrees, or certifications
   - Only add skills the candidate has demonstrably used or could reasonably claim
   - If experience suggests familiarity with a tool/skill, you CAN claim it
   - Example: If they automated tasks, they CAN claim "process automation" even if not explicitly stated

**REALISTIC SCORE IMPACT RULES (MANDATORY):**

You may ONLY claim score increases that fit within remaining headroom for each category.

**Category-by-Category Improvement Strategy:**

1. **Skills Match (Currently: {skills_points}/40, Headroom: {skills_headroom}):**
   - Adding a truly MISSING required skill: +(40/total_required_skills) points each
   - Adding a preferred skill: +(10/total_preferred_skills) points each
   - Converting inferred → explicit wording: +0 points for Skills Match, but helps Keyword Optimization
   - **Maximum possible gain:** {skills_headroom} points

2. **Keyword Optimization (Currently: {keyword_points}/15, Headroom: {keyword_headroom}):**
   - Adding exact job description keyword: +1-2 points each (max {keyword_headroom})
   - Using exact terminology vs synonyms: +1-2 points total
   - **Maximum possible gain:** {keyword_headroom} points

3. **Experience Relevance (Currently: {experience_points}/30, Headroom: {experience_headroom}):**
   - Cannot change actual years of experience
   - Can only reorganize/emphasize relevant experience: +1-3 points max
   - **Maximum possible gain:** {experience_headroom} points (likely small)

4. **Achievements (Currently: {achievement_points}/10, Headroom: {achievement_headroom}):**
   - Adding metrics to unquantified achievements: +1-2 points each
   - Making achievements more relevant to job: +1-2 points total
   - **Maximum possible gain:** {achievement_headroom} points

5. **Education (Currently: {education_points}/5, Headroom: {education_headroom}):**
   - Cannot change actual education/certifications
   - **Maximum possible gain:** {education_headroom} points (likely 0)

Format your response as JSON with the following structure:
{{
    "improved_resume": "The complete rewritten resume text with ALL improvements",
    "changes_made": [
        {{
            "change": "Added Python to skills section",
            "evidence": "Original resume shows 'automated data processing scripts'",
            "category_affected": "skills_match",
            "estimated_point_gain": 2.5
        }},
        {{
            "change": "Changed 'coding' to 'software development' to match job terminology",
            "category_affected": "keyword_optimization",
            "estimated_point_gain": 1.0
        }}
    ],
    "score_projection": {{
        "skills_match": {{
            "original_points": {skills_points},
            "projected_points": <new value, max 40>,
            "skills_added": ["Python", "Docker"],
            "reasoning": "Added 2 missing required skills"
        }},
        "keyword_optimization": {{
            "original_points": {keyword_points},
            "projected_points": <new value, max 15>,
            "keywords_added": ["software development", "agile"],
            "reasoning": "Replaced synonyms with exact job terminology"
        }},
        "achievements": {{
            "original_points": {achievement_points},
            "projected_points": <new value, max 10>,
            "achievements_quantified": 3,
            "reasoning": "Added metrics to 3 bullet points"
        }},
        "experience_relevance": {{
            "original_points": {experience_points},
            "projected_points": <same as original>,
            "note": "Cannot change actual experience, only reorganized for relevance"
        }},
        "education": {{
            "original_points": {education_points},
            "projected_points": <same as original>
        }}
    }},
    "projected_total_score": <sum of all projected_points>,
    "projected_improvement": <projected_total - current_total>,
    "confidence_level": "high|medium|low",
    "confidence_notes": "Explain any uncertainty in projections"
}}

**CRITICAL RULES FOR ESTIMATION:**

1. **Respect Ceilings:** Never project a category score above its maximum
2. **Calculate Honestly:** projected_improvement = sum of all (projected_points - original_points)
3. **Show Your Math:** List every skill/keyword added and its estimated impact
4. **Be Conservative:** If uncertain, round DOWN
5. **Acknowledge Limits:** If skills_match is 38/40, say "limited room for improvement"

Example: If skills_match is 35/40 and you add 2 required skills (out of 10 total required):
- Point gain = 2 × (40/10) = 8 points
- But ceiling is 40, so max new score = 40
- Projected improvement = 40 - 35 = 5 points (NOT 8!)

**Your projected_improvement MUST be realistic based on actual headroom available.**
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
        missing_skills: Optional[List[str]] = None,
        score_breakdown: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an improved version of a resume.

        Args:
            resume_text: Original resume text
            job_description: Target job description
            match_score: Current match score (0-100)
            recommendations: List of improvement recommendations
            missing_skills: List of missing skills to address
            score_breakdown: Detailed score breakdown by category (CRITICAL for accurate estimates)

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

            # Extract category scores and calculate headroom
            if score_breakdown:
                skills_breakdown = score_breakdown.get('skills_match', {})
                skills_points = skills_breakdown.get('points', 0) if isinstance(skills_breakdown, dict) else score_breakdown.get('skills_match', 0)

                keyword_breakdown = score_breakdown.get('keyword_optimization', {})
                keyword_points = keyword_breakdown.get('points', 0) if isinstance(keyword_breakdown, dict) else score_breakdown.get('keyword_optimization', 0)

                experience_breakdown = score_breakdown.get('experience_relevance', {})
                experience_points = experience_breakdown.get('points', 0) if isinstance(experience_breakdown, dict) else score_breakdown.get('experience_relevance', 0)

                achievement_breakdown = score_breakdown.get('achievements', {})
                achievement_points = achievement_breakdown.get('points', 0) if isinstance(achievement_breakdown, dict) else score_breakdown.get('achievements', 0)

                education_breakdown = score_breakdown.get('education', {})
                education_points = education_breakdown.get('points', 0) if isinstance(education_breakdown, dict) else score_breakdown.get('education', 0)

                score_breakdown_text = json.dumps(score_breakdown, indent=2)
            else:
                # Fallback if no breakdown provided
                skills_points = keyword_points = experience_points = achievement_points = education_points = 0
                score_breakdown_text = "Score breakdown not available"

            # Calculate headroom
            skills_headroom = 40 - skills_points
            keyword_headroom = 15 - keyword_points
            experience_headroom = 30 - experience_points
            achievement_headroom = 10 - achievement_points
            education_headroom = 5 - education_points

            prompt = self.REWRITE_PROMPT.format(
                resume_text=resume_text,
                job_description=job_description,
                match_score=match_score,
                score_breakdown=score_breakdown_text,
                recommendations=rec_text,
                missing_skills=skills_text,
                skills_points=skills_points,
                skills_headroom=skills_headroom,
                keyword_points=keyword_points,
                keyword_headroom=keyword_headroom,
                experience_points=experience_points,
                experience_headroom=experience_headroom,
                achievement_points=achievement_points,
                achievement_headroom=achievement_headroom,
                education_points=education_points,
                education_headroom=education_headroom
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
