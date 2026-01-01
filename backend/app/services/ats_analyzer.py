"""
ATS (Applicant Tracking System) analyzer for resume optimization.
Analyzes resume for ATS compatibility and keyword matching.
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter

from app.core.logging_config import get_logger
from app.core.llm_providers import BaseLLMClient

logger = get_logger(__name__)


class ATSAnalyzer:
    """Analyze resume for ATS compatibility and keyword matching."""

    # Common ATS-unfriendly elements
    ATS_ISSUES = {
        "tables": r'\|.*\|',  # Markdown tables
        "special_chars": r'[▪▫■□●○◆◇★☆]',  # Special bullets
        "headers_footers": r'(page \d+ of \d+|confidential)',
        "text_boxes": r'\[.*?\]',  # Bracketed text boxes
    }

    # Required sections for good ATS score
    REQUIRED_SECTIONS = [
        "experience", "work experience", "employment",
        "education", "skills", "summary", "objective"
    ]

    # Common filler words to exclude
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'have', 'this', 'we', 'you', 'your',
        'our', 'their', 'they', 'can', 'been', 'had', 'but', 'not', 'or'
    }

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm_client = llm_client

    def analyze_ats_score(
        self,
        resume_text: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Analyze resume for ATS compatibility.

        Args:
            resume_text: Candidate's resume text
            job_description: Job description text

        Returns:
            Dictionary with ats_score, keyword_matches, issues, and recommendations
        """
        try:
            # Extract keywords from job description
            job_keywords = self._extract_keywords(job_description)

            # Extract keywords from resume
            resume_keywords = self._extract_keywords(resume_text)

            # Calculate keyword matches
            keyword_analysis = self._analyze_keyword_matches(
                job_keywords=job_keywords,
                resume_keywords=resume_keywords,
                resume_text=resume_text,
                job_description=job_description
            )

            # Check for ATS formatting issues
            formatting_score, issues = self._check_formatting(resume_text)

            # Check for required sections
            section_score, section_issues = self._check_sections(resume_text)

            # Check for contact information
            contact_score = self._check_contact_info(resume_text)

            # Calculate overall ATS score (weighted)
            ats_score = (
                keyword_analysis['match_percentage'] * 0.50 +  # 50% weight on keywords
                formatting_score * 0.25 +  # 25% on formatting
                section_score * 0.15 +  # 15% on sections
                contact_score * 0.10  # 10% on contact info
            )

            # Compile recommendations
            recommendations = []

            if keyword_analysis['match_percentage'] < 60:
                recommendations.append({
                    "type": "keywords",
                    "priority": "high",
                    "issue": f"Only {keyword_analysis['matched_count']}/{keyword_analysis['total_keywords']} key terms matched",
                    "suggestion": f"Add these missing keywords: {', '.join(keyword_analysis['missing_keywords'][:10])}"
                })

            if issues:
                recommendations.append({
                    "type": "formatting",
                    "priority": "medium",
                    "issue": f"Found {len(issues)} ATS formatting issues",
                    "suggestion": "Use simple formatting: standard fonts, no tables, standard bullet points (•, -, *)"
                })

            if section_issues:
                recommendations.append({
                    "type": "sections",
                    "priority": "high",
                    "issue": f"Missing important sections: {', '.join(section_issues)}",
                    "suggestion": "Add missing sections to improve ATS parsing"
                })

            if contact_score < 100:
                recommendations.append({
                    "type": "contact",
                    "priority": "high",
                    "issue": "Missing contact information",
                    "suggestion": "Include email and phone number at the top of resume"
                })

            result = {
                "ats_score": round(ats_score, 1),
                "keyword_analysis": keyword_analysis,
                "formatting_score": formatting_score,
                "section_score": section_score,
                "contact_score": contact_score,
                "issues": issues + section_issues,
                "recommendations": recommendations
            }

            logger.info("ATS analysis completed", ats_score=ats_score)
            return result

        except Exception as e:
            logger.error("Failed to analyze ATS score", error=str(e))
            raise

    def _extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """
        Extract meaningful keywords from text.

        Args:
            text: Text to extract keywords from
            min_length: Minimum keyword length

        Returns:
            List of keywords
        """
        # Convert to lowercase
        text_lower = text.lower()

        # Extract multi-word phrases (2-3 words) that are likely skills/technologies
        phrases = []

        # Common tech patterns
        tech_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b',  # Capitalized phrases
            r'\b\w+\.js\b', r'\b\w+\.py\b',  # File extensions
            r'\b[A-Z]{2,}\b',  # Acronyms
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            phrases.extend([m.lower() for m in matches])

        # Extract individual words
        words = re.findall(r'\b\w+\b', text_lower)

        # Filter words: remove stop words, keep only meaningful terms
        keywords = [
            word for word in words
            if len(word) >= min_length
            and word not in self.STOP_WORDS
            and not word.isdigit()
        ]

        # Combine phrases and keywords
        all_keywords = list(set(phrases + keywords))

        # Get frequency
        keyword_freq = Counter(all_keywords)

        # Return keywords sorted by frequency (most common first)
        return [k for k, v in keyword_freq.most_common(100)]

    def _analyze_keyword_matches(
        self,
        job_keywords: List[str],
        resume_keywords: List[str],
        resume_text: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Analyze keyword matches between job and resume.

        Returns:
            Dictionary with match statistics and lists
        """
        resume_text_lower = resume_text.lower()
        job_desc_lower = job_description.lower()

        # Find important keywords (appear in job description)
        # Prioritize keywords that appear multiple times in job description
        job_keyword_freq = Counter(
            word for word in job_keywords
            if job_desc_lower.count(word) > 0
        )

        # Get top keywords from job (most important)
        important_job_keywords = [
            k for k, v in job_keyword_freq.most_common(50)
        ]

        # Check which job keywords are in resume
        matched_keywords = [
            kw for kw in important_job_keywords
            if kw in resume_text_lower
        ]

        missing_keywords = [
            kw for kw in important_job_keywords[:30]  # Top 30 missing
            if kw not in resume_text_lower
        ]

        # Calculate match percentage
        total_keywords = len(important_job_keywords)
        matched_count = len(matched_keywords)
        match_percentage = (matched_count / total_keywords * 100) if total_keywords > 0 else 0

        # Extract skills specifically (common skill patterns)
        skills_in_job = self._extract_skills(job_description)
        skills_in_resume = self._extract_skills(resume_text)

        matched_skills = [s for s in skills_in_job if s.lower() in resume_text_lower]
        missing_skills = [s for s in skills_in_job if s.lower() not in resume_text_lower]

        return {
            "total_keywords": total_keywords,
            "matched_count": matched_count,
            "match_percentage": round(match_percentage, 1),
            "matched_keywords": matched_keywords[:20],  # Top 20 matches
            "missing_keywords": missing_keywords[:20],  # Top 20 missing
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        }

    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills and technologies."""
        text_lower = text.lower()

        # Common skill patterns
        skill_patterns = [
            # Programming languages
            r'\b(python|java|javascript|typescript|c\+\+|c#|ruby|go|rust|swift|kotlin|php|scala)\b',
            # Frameworks
            r'\b(react|angular|vue|django|flask|spring|node\.?js|express|fastapi|rails)\b',
            # Databases
            r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch|dynamodb|oracle)\b',
            # Cloud/DevOps
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|terraform|ansible|git)\b',
            # Tools
            r'\b(jira|confluence|tableau|power\s?bi|excel|salesforce)\b',
            # Methodologies
            r'\b(agile|scrum|devops|ci/cd|microservices|rest\s?api|graphql)\b',
        ]

        skills = []
        for pattern in skill_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.extend(matches)

        # Also look for capitalized tech terms (likely skills)
        capitalized = re.findall(r'\b[A-Z][a-zA-Z]*(?:\.[a-z]+)?\b', text)
        skills.extend(capitalized)

        return list(set(skills))

    def _check_formatting(self, resume_text: str) -> Tuple[float, List[str]]:
        """
        Check for ATS-unfriendly formatting.

        Returns:
            Tuple of (score out of 100, list of issues)
        """
        issues = []
        score = 100.0

        # Check for tables
        if re.search(self.ATS_ISSUES["tables"], resume_text):
            issues.append("Contains tables (may not parse correctly)")
            score -= 20

        # Check for special characters
        special_chars = re.findall(self.ATS_ISSUES["special_chars"], resume_text)
        if special_chars:
            issues.append(f"Contains {len(set(special_chars))} types of special bullet points")
            score -= 10

        # Check for overly complex formatting
        if resume_text.count('\t') > 20:
            issues.append("Excessive tab characters detected")
            score -= 10

        # Check for very long lines (might be text boxes or columns)
        lines = resume_text.split('\n')
        long_lines = [l for l in lines if len(l) > 200]
        if len(long_lines) > 5:
            issues.append("Some lines are very long (possible column formatting)")
            score -= 15

        return max(score, 0), issues

    def _check_sections(self, resume_text: str) -> Tuple[float, List[str]]:
        """
        Check for required resume sections.

        Returns:
            Tuple of (score out of 100, list of missing sections)
        """
        text_lower = resume_text.lower()

        # Group related section names
        section_groups = {
            "experience": ["experience", "work experience", "employment history", "professional experience"],
            "education": ["education", "academic background", "qualifications"],
            "skills": ["skills", "technical skills", "core competencies", "expertise"],
        }

        found_sections = []
        missing_sections = []

        for section_name, variations in section_groups.items():
            found = any(variation in text_lower for variation in variations)
            if found:
                found_sections.append(section_name)
            else:
                missing_sections.append(section_name)

        # Calculate score
        total_sections = len(section_groups)
        found_count = len(found_sections)
        score = (found_count / total_sections) * 100

        return score, missing_sections

    def _check_contact_info(self, resume_text: str) -> float:
        """
        Check for contact information.

        Returns:
            Score out of 100
        """
        score = 0

        # Check for email
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text):
            score += 50

        # Check for phone
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # US format
            r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',  # (123) 456-7890
            r'\+\d{1,3}\s*\d{3,}',  # International
        ]
        if any(re.search(pattern, resume_text) for pattern in phone_patterns):
            score += 50

        return score

    async def get_ats_recommendations(
        self,
        resume_text: str,
        job_description: str,
        ats_analysis: Dict[str, Any]
    ) -> List[str]:
        """
        Use LLM to generate specific ATS improvement recommendations.

        Args:
            resume_text: Candidate's resume
            job_description: Job description
            ats_analysis: Results from analyze_ats_score

        Returns:
            List of actionable recommendations
        """
        if not self.llm_client:
            return []

        try:
            prompt = f"""You are an ATS (Applicant Tracking System) optimization expert.

**ATS Analysis Results:**
- ATS Score: {ats_analysis['ats_score']}/100
- Keyword Match: {ats_analysis['keyword_analysis']['match_percentage']}%
- Matched Keywords: {', '.join(ats_analysis['keyword_analysis']['matched_keywords'][:10])}
- Missing Keywords: {', '.join(ats_analysis['keyword_analysis']['missing_keywords'][:10])}

**Resume Issues:**
{', '.join(ats_analysis['issues']) if ats_analysis['issues'] else 'No major issues'}

**Job Description:**
{job_description[:500]}...

**Resume:**
{resume_text[:500]}...

Provide 5-7 specific, actionable recommendations to improve this resume's ATS score. Focus on:
1. Which specific keywords to add and where
2. Formatting improvements
3. Section additions or reorganization
4. Content optimization

Format as a numbered list. Be specific and actionable.
"""

            response = await self.llm_client.generate(prompt)

            # Parse numbered list
            lines = response.strip().split('\n')
            recommendations = [
                line.strip().lstrip('0123456789.-) ')
                for line in lines
                if line.strip() and line.strip()[0].isdigit()
            ]

            return recommendations[:7]

        except Exception as e:
            logger.error("Failed to generate ATS recommendations", error=str(e))
            return []
