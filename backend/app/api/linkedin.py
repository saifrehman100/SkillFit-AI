"""
LinkedIn integration endpoints.
Quick job matching from LinkedIn URLs.
"""
from typing import Optional

from typing import Optional as OptionalType

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.llm_providers import LLMFactory
from app.models.database import get_db
from app.services.linkedin_scraper import LinkedInScraper, LinkedInScraperError
from app.services.resume_parser import ResumeParser, ResumeParseError
from app.services.job_matcher import JobMatcher
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/scan-job")
async def scan_linkedin_job(
    linkedin_url: str = Form(..., description="LinkedIn job posting URL (e.g., https://www.linkedin.com/jobs/view/123456789)"),
    resume: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    detailed: bool = Form(default=True, description="Provide detailed analysis (default: true)"),
    llm_provider: Optional[str] = Form(
        default=None,
        description="LLM provider: 'openai', 'claude', 'gemini', or 'openai_compatible' (default: system configured)"
    ),
    llm_model: Optional[str] = Form(
        default=None,
        description="Model name - OpenAI: 'gpt-4-turbo'/'gpt-4o', Claude: 'claude-3-5-sonnet-20241022', Gemini: 'gemini-1.5-pro' (default: system configured)"
    ),
    api_key: Optional[str] = Form(
        default=None,
        description="Your LLM API key (optional - uses system default if not provided). Example: 'sk-proj-...' for OpenAI"
    ),
    db: Session = Depends(get_db)
):
    """
    🚀 Quick LinkedIn Job Match Scanner

    Upload your resume and provide a LinkedIn job URL to get instant matching results!

    **This endpoint:**
    1. ✅ Scrapes the job details from LinkedIn
    2. ✅ Parses your resume
    3. ✅ Uses AI to analyze the match
    4. ✅ Returns match score, missing skills, and recommendations

    **No authentication required!** This is a public endpoint - just upload and go.

    **Parameters:**
    - `linkedin_url` (required): Full LinkedIn job posting URL
      - Example: https://www.linkedin.com/jobs/view/3234567890

    - `resume` (required): Your resume file
      - Supported formats: PDF, DOCX, TXT
      - Max size: 10MB

    - `detailed` (optional): Get detailed analysis
      - Default: true
      - Set to false for quick match score only

    - `llm_provider` (optional): Choose your AI provider
      - Options: 'openai', 'claude', 'gemini', 'openai_compatible'
      - Default: Uses system-configured provider (currently OpenAI)
      - Leave empty to use default

    - `llm_model` (optional): Specify exact model
      - OpenAI models: 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini', 'gpt-4'
      - Claude models: 'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229'
      - Gemini models: 'gemini-1.5-pro', 'gemini-1.5-flash'
      - Default: Uses system-configured model
      - Leave empty to use default

    - `api_key` (optional): Your own API key
      - Provide your own API key if you want to use your quota
      - OpenAI format: 'sk-proj-...'
      - Claude format: 'sk-ant-...'
      - Gemini format: 'AIza...'
      - If not provided, uses system-configured API key

    **Example Usage:**

    Basic usage (uses system defaults):
    ```
    linkedin_url: https://www.linkedin.com/jobs/view/3234567890
    resume: [upload your resume.pdf]
    ```

    With custom model:
    ```
    linkedin_url: https://www.linkedin.com/jobs/view/3234567890
    resume: [upload your resume.pdf]
    llm_provider: openai
    llm_model: gpt-4-turbo
    ```

    With your own API key:
    ```
    linkedin_url: https://www.linkedin.com/jobs/view/3234567890
    resume: [upload your resume.pdf]
    llm_provider: openai
    llm_model: gpt-4o
    api_key: sk-proj-your-api-key-here
    ```

    **Returns:**
    - Match score (0-100)
    - Missing skills you need to develop
    - Specific recommendations to improve your chances
    - Detailed explanation of the match
    - Strengths and weaknesses
    - Job details (title, company, location, description)
    - Metadata (provider used, tokens consumed, cost estimate)
    """
    try:
        logger.info(
            "LinkedIn job scan requested",
            linkedin_url=linkedin_url,
            filename=resume.filename
        )

        # Step 1: Scrape LinkedIn job
        logger.info("Step 1: Scraping LinkedIn job...")
        try:
            scraper = LinkedInScraper()
            job_data = await scraper.scrape_job(linkedin_url)
        except LinkedInScraperError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to scrape LinkedIn job: {str(e)}"
            )

        # Step 2: Parse resume
        logger.info("Step 2: Parsing resume...")
        try:
            resume_content = await resume.read()
            resume_text = ResumeParser.parse(resume_content, resume.filename)
        except ResumeParseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse resume: {str(e)}"
            )

        # Step 3: Get LLM client
        logger.info("Step 3: Initializing AI analysis...")
        provider = llm_provider or settings.default_llm_provider
        model = llm_model or settings.default_model_name

        # Use provided API key or fall back to system default
        llm_api_key = api_key
        if not llm_api_key:
            # Get system default API key based on provider
            if provider == "openai":
                llm_api_key = settings.openai_api_key
            elif provider == "claude":
                llm_api_key = settings.anthropic_api_key
            elif provider == "gemini":
                llm_api_key = settings.google_api_key
            elif provider == "openai_compatible":
                llm_api_key = settings.openai_compatible_api_key

        if not llm_api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No API key provided for {provider}. Please provide an API key or configure one in settings."
            )

        llm_client = LLMFactory.create_client(
            provider=provider,
            api_key=llm_api_key,
            model=model
        )

        # Step 4: Perform matching
        logger.info("Step 4: Analyzing match with AI...")
        matcher = JobMatcher(llm_client)

        # Combine job description and requirements
        job_description = job_data["description"]
        if job_data.get("requirements"):
            job_description += f"\n\nRequirements:\n{job_data['requirements']}"

        match_result = await matcher.match(
            resume_text=resume_text,
            job_description=job_description,
            detailed=detailed
        )

        # Step 5: Build response
        logger.info("Step 5: Building response...")
        response = {
            "success": True,
            "job": {
                "title": job_data["title"],
                "company": job_data.get("company", "N/A"),
                "location": job_data.get("location", "N/A"),
                "source_url": linkedin_url
            },
            "match": {
                "score": match_result.get("match_score", 0),
                "missing_skills": match_result.get("missing_skills", []),
                "recommendations": match_result.get("recommendations", []),
                "explanation": match_result.get("explanation", ""),
                "strengths": match_result.get("strengths", []),
                "weaknesses": match_result.get("weaknesses", [])
            },
            "metadata": {
                "llm_provider": match_result["_metadata"]["provider"],
                "llm_model": match_result["_metadata"]["model"],
                "tokens_used": match_result["_metadata"]["tokens_used"],
                "cost_estimate": match_result["_metadata"]["cost_estimate"]
            }
        }

        logger.info(
            "LinkedIn job scan completed successfully",
            match_score=response["match"]["score"]
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("LinkedIn job scan failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during job scanning: {str(e)}"
        )


@router.post("/test-scraper")
async def test_linkedin_scraper(
    linkedin_url: str = Form(..., description="LinkedIn job posting URL (e.g., https://www.linkedin.com/jobs/view/123456789)")
):
    """
    🧪 Test LinkedIn Job Scraper

    Test the LinkedIn scraper without doing a full match analysis.
    Useful for debugging, previewing job details, or verifying a LinkedIn URL works.

    **No authentication required!** This is a public testing endpoint.

    **Parameters:**
    - `linkedin_url` (required): Full LinkedIn job posting URL
      - Example: https://www.linkedin.com/jobs/view/3234567890
      - Must be a valid LinkedIn job posting URL

    **What it does:**
    - Validates the LinkedIn URL format
    - Scrapes the job posting page
    - Extracts job details (title, company, description, requirements, location)
    - Does NOT perform AI matching (use /scan-job for that)

    **Example Usage:**
    ```
    linkedin_url: https://www.linkedin.com/jobs/view/3234567890
    ```

    **Returns:**
    ```json
    {
      "success": true,
      "job": {
        "title": "Senior Software Engineer",
        "company": "Tech Corp",
        "description": "Full job description...",
        "requirements": "Required skills and qualifications...",
        "location": "San Francisco, CA",
        "source_url": "https://www.linkedin.com/jobs/view/3234567890"
      }
    }
    ```

    **Use Cases:**
    - Test if a LinkedIn URL is valid and scrapable
    - Preview job details before uploading a resume
    - Debug scraping issues
    - Verify job posting is still available
    """
    try:
        logger.info("Testing LinkedIn scraper", url=linkedin_url)

        scraper = LinkedInScraper()
        job_data = await scraper.scrape_job(linkedin_url)

        return {
            "success": True,
            "job": job_data
        }

    except LinkedInScraperError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to scrape LinkedIn job: {str(e)}"
        )
    except Exception as e:
        logger.error("Scraper test failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
