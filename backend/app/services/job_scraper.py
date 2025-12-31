"""
Job scraper for importing jobs from LinkedIn, Indeed, and other platforms.
Uses web scraping to extract job details from URLs.
"""
import re
from typing import Dict, Optional, Any
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class JobScraperError(Exception):
    """Base exception for job scraper errors."""
    pass


class JobScraper:
    """Scrapes job details from job posting URLs."""

    SUPPORTED_PLATFORMS = {
        "linkedin.com": "linkedin",
        "indeed.com": "indeed",
        "glassdoor.com": "glassdoor",
    }

    @classmethod
    async def scrape_job(cls, url: str) -> Dict[str, Any]:
        """
        Scrape job details from a URL.

        Args:
            url: Job posting URL

        Returns:
            Dictionary with job details (title, company, description, etc.)

        Raises:
            JobScraperError: If scraping fails or platform is not supported
        """
        platform = cls._detect_platform(url)

        if not platform:
            raise JobScraperError(
                f"Unsupported platform. Supported: {', '.join(cls.SUPPORTED_PLATFORMS.keys())}"
            )

        logger.info("Scraping job from platform", platform=platform, url=url)

        if platform == "linkedin":
            return await cls._scrape_linkedin(url)
        elif platform == "indeed":
            return await cls._scrape_indeed(url)
        elif platform == "glassdoor":
            return await cls._scrape_glassdoor(url)
        else:
            raise JobScraperError(f"Platform {platform} not yet implemented")

    @classmethod
    def _detect_platform(cls, url: str) -> Optional[str]:
        """Detect the job platform from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            domain = domain.replace("www.", "")

            for platform_domain, platform_name in cls.SUPPORTED_PLATFORMS.items():
                if platform_domain in domain:
                    return platform_name

            return None
        except Exception:
            return None

    @classmethod
    async def _scrape_linkedin(cls, url: str) -> Dict[str, Any]:
        """
        Scrape job details from LinkedIn.

        Note: LinkedIn has strong anti-bot measures. This is a simplified implementation.
        For production, consider using LinkedIn API or professional scraping services.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract job title
            title = None
            title_selectors = [
                'h1.top-card-layout__title',
                'h1.topcard__title',
                'h1',
            ]
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get_text(strip=True)
                    break

            # Extract company name
            company = None
            company_selectors = [
                'a.topcard__org-name-link',
                'span.topcard__flavor',
                '.top-card-layout__company',
            ]
            for selector in company_selectors:
                elem = soup.select_one(selector)
                if elem:
                    company = elem.get_text(strip=True)
                    break

            # Extract job description
            description = None
            desc_selectors = [
                'div.description__text',
                'div.show-more-less-html__markup',
                'section.description',
            ]
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    description = elem.get_text(separator='\n', strip=True)
                    break

            # If we couldn't find description, try to get all text
            if not description:
                # Get main content
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    # Remove script and style tags
                    for tag in main_content(['script', 'style', 'nav', 'footer', 'header']):
                        tag.decompose()
                    description = main_content.get_text(separator='\n', strip=True)

            if not title:
                raise JobScraperError("Could not extract job title from LinkedIn page")

            result = {
                "title": title,
                "company": company or "Unknown Company",
                "description": description or "No description available",
                "source_url": url,
                "requirements": None,  # Could be extracted separately if needed
            }

            logger.info("Successfully scraped LinkedIn job", title=title, company=company)
            return result

        except httpx.HTTPError as e:
            logger.error("HTTP error scraping LinkedIn", error=str(e))
            raise JobScraperError(f"Failed to fetch LinkedIn page: {str(e)}")
        except Exception as e:
            logger.error("Error scraping LinkedIn", error=str(e))
            raise JobScraperError(f"Failed to scrape LinkedIn job: {str(e)}")

    @classmethod
    async def _scrape_indeed(cls, url: str) -> Dict[str, Any]:
        """Scrape job details from Indeed."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            }

            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract job title
            title = None
            title_elem = soup.select_one('h1.jobsearch-JobInfoHeader-title, h1.icl-u-xs-mb--xs')
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Extract company name
            company = None
            company_elem = soup.select_one('[data-company-name="true"], div.jobsearch-InlineCompanyRating > div')
            if company_elem:
                company = company_elem.get_text(strip=True)

            # Extract job description
            description = None
            desc_elem = soup.select_one('#jobDescriptionText, div.jobsearch-jobDescriptionText')
            if desc_elem:
                description = desc_elem.get_text(separator='\n', strip=True)

            if not title:
                raise JobScraperError("Could not extract job title from Indeed page")

            result = {
                "title": title,
                "company": company or "Unknown Company",
                "description": description or "No description available",
                "source_url": url,
                "requirements": None,
            }

            logger.info("Successfully scraped Indeed job", title=title, company=company)
            return result

        except httpx.HTTPError as e:
            logger.error("HTTP error scraping Indeed", error=str(e))
            raise JobScraperError(f"Failed to fetch Indeed page: {str(e)}")
        except Exception as e:
            logger.error("Error scraping Indeed", error=str(e))
            raise JobScraperError(f"Failed to scrape Indeed job: {str(e)}")

    @classmethod
    async def _scrape_glassdoor(cls, url: str) -> Dict[str, Any]:
        """Scrape job details from Glassdoor."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            }

            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract job title
            title = None
            title_elem = soup.select_one('div[data-test="jobTitle"], h1')
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Extract company
            company = None
            company_elem = soup.select_one('div[data-test="employerName"]')
            if company_elem:
                company = company_elem.get_text(strip=True)

            # Extract description
            description = None
            desc_elem = soup.select_one('div[data-test="jobDescriptionContent"], div.desc')
            if desc_elem:
                description = desc_elem.get_text(separator='\n', strip=True)

            if not title:
                raise JobScraperError("Could not extract job title from Glassdoor page")

            result = {
                "title": title,
                "company": company or "Unknown Company",
                "description": description or "No description available",
                "source_url": url,
                "requirements": None,
            }

            logger.info("Successfully scraped Glassdoor job", title=title, company=company)
            return result

        except httpx.HTTPError as e:
            logger.error("HTTP error scraping Glassdoor", error=str(e))
            raise JobScraperError(f"Failed to fetch Glassdoor page: {str(e)}")
        except Exception as e:
            logger.error("Error scraping Glassdoor", error=str(e))
            raise JobScraperError(f"Failed to scrape Glassdoor job: {str(e)}")
