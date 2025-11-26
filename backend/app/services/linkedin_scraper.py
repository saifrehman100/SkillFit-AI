"""
LinkedIn job scraper service.
Extracts job details from LinkedIn job postings.
"""
import re
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LinkedInScraperError(Exception):
    """Exception raised when LinkedIn scraping fails."""
    pass


class LinkedInScraper:
    """Service for scraping LinkedIn job postings."""

    @staticmethod
    async def scrape_job(url: str) -> Dict[str, Any]:
        """
        Scrape job details from a LinkedIn URL.

        Args:
            url: LinkedIn job posting URL

        Returns:
            Dictionary with job details (title, company, description, etc.)

        Raises:
            LinkedInScraperError: If scraping fails
        """
        try:
            logger.info("Scraping LinkedIn job", url=url)

            # Validate URL
            if not LinkedInScraper._is_valid_linkedin_url(url):
                raise LinkedInScraperError(
                    "Invalid LinkedIn URL. Please provide a valid LinkedIn job posting URL."
                )

            # Fetch the page
            async with httpx.AsyncClient(follow_redirects=True) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract job details
            job_data = {
                "title": LinkedInScraper._extract_title(soup),
                "company": LinkedInScraper._extract_company(soup),
                "description": LinkedInScraper._extract_description(soup),
                "requirements": LinkedInScraper._extract_requirements(soup),
                "location": LinkedInScraper._extract_location(soup),
                "source_url": url
            }

            # Validate that we got at least title and description
            if not job_data["title"] or not job_data["description"]:
                raise LinkedInScraperError(
                    "Could not extract job details. The page might require authentication."
                )

            logger.info(
                "LinkedIn job scraped successfully",
                title=job_data["title"],
                company=job_data["company"]
            )

            return job_data

        except httpx.HTTPError as e:
            logger.error("HTTP error scraping LinkedIn", error=str(e))
            raise LinkedInScraperError(f"Failed to fetch LinkedIn page: {str(e)}")
        except Exception as e:
            logger.error("Error scraping LinkedIn", error=str(e))
            raise LinkedInScraperError(f"Failed to scrape job details: {str(e)}")

    @staticmethod
    def _is_valid_linkedin_url(url: str) -> bool:
        """Check if URL is a valid LinkedIn job posting URL."""
        patterns = [
            r'linkedin\.com/jobs/view/\d+',
            r'linkedin\.com/jobs/collections/.*',
            r'linkedin\.com/jobs/search/.*'
        ]
        return any(re.search(pattern, url) for pattern in patterns)

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> Optional[str]:
        """Extract job title from LinkedIn page."""
        # Try multiple selectors
        selectors = [
            'h1.top-card-layout__title',
            'h1.topcard__title',
            'h2.topcard__title',
            'h1[class*="job-title"]',
            'h1[class*="topcard"]'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        # Fallback: look for any h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)

        return None

    @staticmethod
    def _extract_company(soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from LinkedIn page."""
        selectors = [
            'a.topcard__org-name-link',
            'span.topcard__flavor',
            'a[class*="company"]',
            'span[class*="company"]'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        return None

    @staticmethod
    def _extract_description(soup: BeautifulSoup) -> Optional[str]:
        """Extract job description from LinkedIn page."""
        selectors = [
            'div.show-more-less-html__markup',
            'div.description__text',
            'div[class*="description"]',
            'section.description',
            'div.job-view-layout'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Get text and clean it up
                text = element.get_text(separator='\n', strip=True)
                # Remove excessive whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                return text

        return None

    @staticmethod
    def _extract_requirements(soup: BeautifulSoup) -> Optional[str]:
        """Extract requirements section from description."""
        description = LinkedInScraper._extract_description(soup)
        if not description:
            return None

        # Look for common requirement section markers
        patterns = [
            r"(?:Requirements?|Qualifications?|Skills?|What [Ww]e['\u2019]re [Ll]ooking [Ff]or)[\s\S]*?(?=\n\n[A-Z]|\Z)",
            r'(?:Required|Must [Hh]ave)[\s\S]*?(?=\n\n[A-Z]|\Z)'
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    @staticmethod
    def _extract_location(soup: BeautifulSoup) -> Optional[str]:
        """Extract job location from LinkedIn page."""
        selectors = [
            'span.topcard__flavor--bullet',
            'span[class*="location"]',
            'div[class*="location"]'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        return None
