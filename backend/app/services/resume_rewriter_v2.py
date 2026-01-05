"""
Resume rewriting service v2 with ATS optimization and anti-hallucination controls.
Uses LLMs to rewrite resumes based on match recommendations and job requirements.
"""
from typing import Dict, Any, Optional, List
import json
import re

from app.core.logging_config import get_logger

logger = get_logger(__name__)


def remove_tables_from_resume(resume_text: str) -> str:
    """
    Remove ASCII tables and pipe-separated layouts from resume text.

    This is a safety net to ensure LLM-generated resumes are ATS-friendly
    even if the prompt instructions weren't perfectly followed.

    Args:
        resume_text: Resume text potentially containing tables

    Returns:
        Cleaned resume text without tables
    """
    lines = resume_text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Skip lines that are table borders (mostly +, -, =, | characters)
        if re.match(r'^[\s|+\-=]{4,}$', line):
            continue

        # Skip lines with 3+ pipe separators (likely table rows)
        # Allow lines with 1-2 pipes (could be: "Email: x@y.com | Phone: 123")
        if line.count('|') >= 3:
            continue

        cleaned_lines.append(line)

    # Final safety check: if many pipes remain, log warning
    final_text = '\n'.join(cleaned_lines)
    pipe_count = final_text.count('|')
    if pipe_count > 10:
        logger.warning(f"Resume still contains {pipe_count} pipe characters after table removal")

    return final_text


class ResumeRewriterV2:
    """Service for rewriting and improving resume content with ATS optimization."""

    REWRITE_PROMPT = """
You are an expert resume writer and ATS optimization specialist. Your task is to strategically rewrite this resume to maximize BOTH Match Score AND ATS Score.

**IMPORTANT:** All scoring projections are heuristic estimates, not exact ATS calculations.

**Original Resume:**
{resume_text}

**Target Job Description:**
{job_description}

**Current Match Score:** {match_score}/100

**Current Score Breakdown:**
{score_breakdown}

**Current ATS Score:** {ats_score}/100

**ATS Analysis:**
{ats_analysis}

**Recommendations:**
{recommendations}

**Missing Skills:**
{missing_skills}

---

## DECISION PRIORITY (When Rules Conflict)

When rules or objectives conflict, follow this priority order:

1. **Truthfulness** - NEVER violate (highest priority)
2. **ATS Parseability** - Resume must be machine-readable
3. **Keyword Matching** - Include required skills terminology
4. **Match Score Optimization** - Improve content fit
5. **Formatting Aesthetics** - Clean layout (lowest priority)

---

## SCORING SYSTEMS

### Match Score Calculation (0-100):

**Allowed score movements:**
- Skills Match: max 40 points TOTAL
- Experience Relevance: max 30 points TOTAL
- Keyword Optimization: max 15 points TOTAL
- Achievements: max 10 points TOTAL
- Education: max 5 points TOTAL

**Current Category Scores:**
- Skills Match: {skills_points}/40 (Headroom: {skills_headroom})
- Keyword Optimization: {keyword_points}/15 (Headroom: {keyword_headroom})
- Experience Relevance: {experience_points}/30 (Headroom: {experience_headroom})
- Achievements: {achievement_points}/10 (Headroom: {achievement_headroom})
- Education: {education_points}/5 (Headroom: {education_headroom})

### ATS Score Calculation (0-100):

**Formula:** (Keyword Match × 0.50) + (Formatting × 0.25) + (Sections × 0.15) + (Contact × 0.10)

**Components:**
1. **Keyword Matching (50% weight):** Percentage of job keywords found in resume
2. **Formatting Quality (25% weight):** No tables, standard bullets only, simple layout
3. **Required Sections (15% weight):** Must have Experience, Education, Skills sections
4. **Contact Information (10% weight):** Email and phone number present

---

## MARGINAL GAIN AWARENESS (CRITICAL - Prevents Score Inflation)

**Follow these rules to avoid over-estimating improvements:**

1. **Keyword Repetition:** Repeating a keyword already present ≥2 times yields ZERO ATS gain
2. **Skill Double-Counting:** Adding a skill already counted elsewhere does NOT increase Skills Match points
3. **Near-Ceiling Categories:** If category is within 2 points of ceiling, assume minimal or ZERO gain
4. **Minimum Threshold:** Do not project improvements less than 1 point
5. **Overlapping Improvements:** Skills that improve both Skills Match AND Keyword Optimization should count points in ONLY ONE category

**Why this matters:** Without these rules, you will over-estimate improvements by 10-20 points.

---

## REWRITING INSTRUCTIONS

### TIER 1: MUST DO (Highest Priority)

**1. ADD MISSING SKILLS (But Only With Evidence)**

✅ **YOU CAN add a skill if:**
- Candidate's work directly demonstrates usage (e.g., "deployed containerized apps" → can add "Docker")
- Related technology strongly implies it (e.g., "React development" + "mobile apps" → can add "React Native")
- Context explicitly mentions it (e.g., "sprint planning, standups" → can add "Agile methodology")

❌ **YOU CANNOT add a skill if:**
- No evidence exists in their experience
- It's a different domain entirely
- You're guessing based on job title alone

**Rule:** Every skill added to Skills section MUST also appear at least once in an Experience bullet demonstrating usage.

**2. FIX ATS FORMATTING ISSUES**

**Remove ALL Tables:**
```
❌ BEFORE:
+---------+-----------+
| Skill   | Level     |
+---------+-----------+
| Python  | Expert    |
+---------+-----------+

✅ AFTER:
TECHNICAL SKILLS
Programming Languages: Python (Expert), JavaScript, SQL
```

**Standardize Bullets:**
- Use ONLY: • (Unicode U+2022)
- Replace ALL: ●, ▪, ◆, ★, -, *, or any other bullet character

**Simplify Layout:**
- No columns, no text boxes, no complex formatting
- Keep lines ≤100 characters (target)
- Plain text structure only

**3. ENSURE REQUIRED SECTIONS**

Must include these sections with clear headers:

```
[CANDIDATE NAME]
Email: email@example.com | Phone: (555) 123-4567 | Location | LinkedIn

PROFESSIONAL SUMMARY
[3-4 lines highlighting relevant experience, key skills, and major achievements]

TECHNICAL SKILLS
[Comma-separated or categorized list]

PROFESSIONAL EXPERIENCE
[or WORK EXPERIENCE or EXPERIENCE]

Company Name | Job Title | Start Date - End Date
• Achievement-focused bullet points
• Quantified results where possible

EDUCATION

Degree, Major | University | Year
```

**4. FORMAT CONTACT INFORMATION**

✅ **REQUIRED:**
- Email must be present
- Phone number must be present
- Format: `Email: john@email.com | Phone: (555) 123-4567`

❌ **If missing:**
- Email missing → Add to blockers: "CRITICAL: Email address missing from original resume"
- Phone missing → Add placeholder: `Phone: (000) 000-0000 [UPDATE REQUIRED]`
- NEVER fabricate realistic contact info

### TIER 2: HIGH ROI (Optimize After Tier 1)

**5. USE EXACT JOB TERMINOLOGY**

- Replace synonyms with exact phrases from job description
- Example: Job says "microservices architecture" → Use "microservices architecture", NOT "distributed systems"
- Example: Job says "customer success" → Use "customer success", NOT "client relations"

**This improves both Keyword Optimization (Match) and Keyword Matching (ATS)**

**6. QUANTIFY ACHIEVEMENTS (Anti-Hallucination Rules)**

✅ **YOU CAN quantify when:**
- Numeric evidence exists in original (team size, budget, users, time, percentage)
- Strong contextual bounds exist (e.g., "enterprise-scale", "production environment")
- Conservative ranges can be inferred (e.g., "small team" = "team of 3-5")

❌ **YOU CANNOT quantify when:**
- No numeric signal exists in original resume
- You're inventing precise percentages (e.g., "improved by 47%")
- You're guessing team sizes or impact metrics

**Instead use:**
- Qualitative impact: "Improved system performance in high-traffic production environment"
- Conservative ranges: "Led small engineering team (3-5 developers)"
- Scope indicators: "enterprise-scale application", "customer-facing platform"

**Rule:** If no numeric signal exists, use qualitative impact or conservative ranges. NEVER invent precise percentages or counts.

**7. ADD PROFESSIONAL SUMMARY**

If missing, add 3-4 line summary at the top highlighting:
- Years of experience in target domain
- Key skills matching job requirements
- 1-2 major relevant achievements
- Alignment with role requirements

### TIER 3: POLISH (If Time/Tokens Allow)

**8. OPTIMIZE KEYWORD DENSITY**

- Use job keywords 2-3 times across different sections
- Place critical keywords in: Summary, Skills, and Experience
- Don't keyword stuff (no keyword should appear >3 times total)
- Vary phrasing naturally

**9. RESTRUCTURE FOR RELEVANCE**

- Lead with most relevant job experience for THIS role
- Move less relevant experience lower or condense it
- Emphasize achievements that align with job requirements

---

## SPECIAL CASE HANDLING

**Career Changers:**
- Emphasize transferable skills in Summary
- Map previous industry experience to target role
- Focus on skills section as primary lever

**Entry-Level / Limited Experience:**
- Expand Education section (projects, coursework, GPA if >3.5)
- Include internships, freelance, volunteer work
- Skills section becomes primary focus

**Overqualified Candidates:**
- De-emphasize seniority if role is lower level
- Focus on role-relevant scope, not title inflation

**Missing Contact Info:**
- Email missing → CRITICAL blocker
- Phone missing → Add placeholder `(000) 000-0000 [UPDATE REQUIRED]`

---

## PRE-OUTPUT CHECKLIST

Before returning JSON, verify ALL of these:

□ improved_resume contains NO tables
□ improved_resume uses ONLY • bullets (no ●▪◆-* etc)
□ All skills_added have justification with evidence from original resume
□ No fabricated credentials, employers, or dates
□ No invented precise metrics (no "47%" without source)
□ projected_points ≤ category maximum for ALL categories
□ projected_improvement = sum of (projected - original) for all categories
□ Email present in contact section (or noted in blockers)
□ Phone present or placeholder added
□ Section headers match required names
□ Line lengths ≤100 characters (target)
□ Every skill in Skills section appears in Experience demonstrating usage

---

## OUTPUT FORMAT

Return valid JSON with this EXACT structure:

```json
{{
    "improved_resume": "<<FULL REWRITTEN RESUME TEXT - ATS-FRIENDLY FORMAT>>",

    "match_score_changes": {{
        "skills_match": {{
            "original_points": {skills_points},
            "projected_points": <number 0-40>,
            "improvement": <projected - original>,
            "skills_added": ["skill1", "skill2"],
            "evidence": "Brief justification for each added skill",
            "note": "Skills without usage context receive 50% points"
        }},
        "keyword_optimization": {{
            "original_points": {keyword_points},
            "projected_points": <number 0-15>,
            "improvement": <projected - original>,
            "keywords_added": ["keyword1", "keyword2"],
            "justification": "Explanation of changes"
        }},
        "achievements": {{
            "original_points": {achievement_points},
            "projected_points": <number 0-10>,
            "improvement": <projected - original>,
            "achievements_quantified": <count>,
            "justification": "What was quantified and how"
        }},
        "experience_relevance": {{
            "original_points": {experience_points},
            "projected_points": <number 0-30>,
            "improvement": <projected - original>,
            "justification": "Reorganization or emphasis changes"
        }},
        "education": {{
            "original_points": {education_points},
            "projected_points": <number 0-5>,
            "improvement": <projected - original>,
            "note": "Usually unchanged (cannot fabricate credentials)"
        }}
    }},

    "ats_score_changes": {{
        "formatting": {{
            "original_score": <number 0-100>,
            "projected_score": <number 0-100>,
            "improvement": <number>,
            "fixes_applied": ["Removed table", "Standardized bullets to •", "Simplified layout"]
        }},
        "sections": {{
            "original_score": <number 0-100>,
            "projected_score": <number 0-100>,
            "improvement": <number>,
            "fixes_applied": ["Added SKILLS header", "Added PROFESSIONAL SUMMARY"]
        }},
        "contact_info": {{
            "original_score": <number 0-100>,
            "projected_score": <number 0-100>,
            "improvement": <number>,
            "fixes_applied": ["Added phone placeholder"]
        }},
        "keyword_match": {{
            "original_percentage": <number 0-100>,
            "projected_percentage": <number 0-100>,
            "improvement": <number>,
            "keywords_added_count": <number>,
            "top_keywords_added": ["keyword1", "keyword2", "keyword3"]
        }}
    }},

    "final_scores": {{
        "match_score": {{
            "original": {match_score},
            "projected": <sum of all projected category scores>,
            "improvement": <projected - original>
        }},
        "ats_score": {{
            "original": {ats_score},
            "projected": <weighted average of ATS components>,
            "improvement": <projected - original>
        }}
    }},

    "warnings": [
        "Education score at ceiling; no improvement possible",
        "Limited quantification possible due to lack of metrics in original"
    ],

    "blockers": [
        "Job requires 8+ years experience; candidate has 3 years (Experience Relevance limited)",
        "Email address missing from original resume - CRITICAL"
    ],

    "hallucination_risk": {{
        "level": "low | medium | high",
        "borderline_inferences": [
            "Added 'Docker' skill - inferred from 'containerization' and 'deployment' mentions",
            "Estimated 'team of 5' - resume mentions 'team coordination' in context of small project"
        ],
        "notes": "Any skills or metrics added without explicit evidence"
    }},

    "summary_of_changes": [
        "Added PROFESSIONAL SUMMARY section highlighting cloud experience",
        "Added Skills section with: Python, Docker, Kubernetes (justified by containerization work)",
        "Quantified 3 achievements with conservative estimates",
        "Removed table from Projects section, converted to bullets",
        "Replaced all special bullets with standard •",
        "Added phone placeholder: (000) 000-0000 [UPDATE REQUIRED]",
        "Used exact job terminology: 'microservices', 'CI/CD pipelines', 'agile methodology'"
    ],

    "confidence": "high | medium | low",
    "confidence_notes": "Explanation of confidence level and any limitations"
}}
```

## CONFIDENCE CRITERIA

**HIGH:**
- All skills added have explicit evidence
- All metrics sourced from original or conservative estimates
- ATS issues fully resolved
- Projected improvement ≥15 points

**MEDIUM:**
- Some inferred skills (1-2 with reasonable evidence)
- Some estimated metrics with contextual support
- Minor ATS issues may remain
- Projected improvement 5-14 points

**LOW:**
- Significant skill gaps (>3 missing required skills with no evidence)
- Major experience mismatch (years, seniority)
- Critical ATS issues unresolvable
- Projected improvement <5 points

---

## EXAMPLE TRANSFORMATION

**BEFORE (Poor Match + ATS):**
```
John Doe
john@email.com

EXPERIENCE
XYZ Corp (2020-Present)
●●● Led development initiatives
▪ Worked on various projects
◆ Improved system efficiency

+----------+------------------+
| Skills   | Tools            |
+----------+------------------+
| Coding   | Some frameworks  |
+----------+------------------+
```

**AFTER (Optimized for Match + ATS):**
```
John Doe
Email: john.doe@email.com | Phone: (555) 123-4567 | San Francisco, CA

PROFESSIONAL SUMMARY
Senior Software Engineer with 5+ years of experience in cloud-native development, microservices architecture, and CI/CD automation. Expertise in Python, Docker, and Kubernetes with proven track record of improving system performance and leading agile teams.

TECHNICAL SKILLS
Programming Languages: Python, JavaScript, TypeScript, SQL
Cloud & DevOps: Docker, Kubernetes, AWS, CI/CD Pipelines, Jenkins
Frameworks: Django, Flask, React, Node.js
Methodologies: Agile, Scrum, Microservices Architecture, RESTful APIs

PROFESSIONAL EXPERIENCE

Senior Software Engineer | XYZ Corp | 2020 - Present
• Architected and deployed microservices-based REST API handling 10,000+ requests/day using Python and Docker
• Improved system performance by 40%, reducing API response time from 200ms to 120ms through optimization
• Led agile team of 5 engineers, implementing CI/CD pipelines that reduced deployment time by 60%
• Orchestrated containerized applications using Kubernetes, managing 50+ production containers
```

---

Now rewrite the resume following ALL instructions above. Ensure BOTH Match Score and ATS Score are maximized while maintaining absolute truthfulness.
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
        score_breakdown: Optional[Dict[str, Any]] = None,
        ats_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an improved version of a resume optimized for both Match and ATS scores.

        Args:
            resume_text: Original resume text
            job_description: Target job description
            match_score: Current match score (0-100)
            recommendations: List of improvement recommendations
            missing_skills: List of missing skills to address
            score_breakdown: Detailed score breakdown by category
            ats_analysis: ATS analysis results (score, issues, recommendations)

        Returns:
            Dictionary with improved resume and detailed analysis
        """
        try:
            logger.info(
                "Starting resume rewrite v2",
                match_score=match_score,
                ats_score=ats_analysis.get('ats_score') if ats_analysis else None,
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
                skills_points = keyword_points = experience_points = achievement_points = education_points = 0
                score_breakdown_text = "Score breakdown not available"

            # Calculate headroom
            skills_headroom = 40 - skills_points
            keyword_headroom = 15 - keyword_points
            experience_headroom = 30 - experience_points
            achievement_headroom = 10 - achievement_points
            education_headroom = 5 - education_points

            # Format ATS analysis
            if ats_analysis:
                ats_score = ats_analysis.get('ats_score', 0)
                ats_text = f"""
**Current ATS Score:** {ats_score}/100

**ATS Component Scores:**
- Keyword Match: {ats_analysis.get('keyword_analysis', {}).get('match_percentage', 0)}%
- Formatting: {ats_analysis.get('formatting_score', 0)}/100
- Sections: {ats_analysis.get('section_score', 0)}/100
- Contact Info: {ats_analysis.get('contact_score', 0)}/100

**Issues Found:**
{chr(10).join(f"- {issue}" for issue in ats_analysis.get('issues', [])[:10]) if ats_analysis.get('issues') else "No major issues"}

**Missing Keywords:**
{', '.join(ats_analysis.get('keyword_analysis', {}).get('missing_keywords', [])[:15])}
"""
            else:
                ats_score = 0
                ats_text = "ATS analysis not available"

            prompt = self.REWRITE_PROMPT.format(
                resume_text=resume_text,
                job_description=job_description,
                match_score=match_score,
                score_breakdown=score_breakdown_text,
                ats_score=ats_score,
                ats_analysis=ats_text,
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
                temperature=0.3,
                max_tokens=4096
            )

            logger.info("Resume rewrite v2 completed")

            # Parse JSON response
            result = self._parse_response(response.content)

            # Post-process: Remove any remaining tables (safety net)
            if "improved_resume" in result:
                original_resume = result["improved_resume"]
                cleaned_resume = remove_tables_from_resume(original_resume)

                if original_resume != cleaned_resume:
                    logger.info("Removed tables from improved resume (post-processing)")
                    result["improved_resume"] = cleaned_resume

                    # Add note about table removal
                    if "summary_of_changes" not in result:
                        result["summary_of_changes"] = []
                    result["summary_of_changes"].append(
                        "Post-processing: Removed table formatting for ATS compatibility"
                    )

            # Add metadata
            result["_metadata"] = {
                "model": response.model,
                "provider": response.provider,
                "tokens_used": response.tokens_used,
                "cost_estimate": response.cost_estimate,
                "version": "v2",
                "post_processed": True
            }

            return result

        except Exception as e:
            logger.error("Resume rewriting v2 failed", error=str(e))
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
