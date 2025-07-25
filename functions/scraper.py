"""
Job Advertisement Scraper
Extracts job information from various Australian job sites for document generation.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup
import json
import time

class JobAdScraper:
    """
    Scrapes job advertisements from supported Australian job sites.
    Supports: SEEK, Ethical Jobs, Jora, Indeed Australia, LinkedIn
    """
    
    def __init__(self):
        """Initialize the scraper with site-specific configurations."""
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-AU,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Site-specific selectors for extracting job information
        self.site_selectors = {
            'seek.com.au': {
                'title': 'h1[data-automation="job-detail-title"]',
                'company': '[data-automation="advertiser-name"]',
                'description': '[data-automation="jobAdDetails"]',
                'location': '[data-automation="job-detail-location"]',
                'salary': '[data-automation="job-detail-salary"]',
                'type': '[data-automation="job-detail-work-type"]'
            },
            'ethicaljobs.com.au': {
                'title': 'h1.job-title',
                'company': '.organisation-name',
                'description': '.job-description',
                'location': '.job-location',
                'salary': '.salary-info',
                'type': '.employment-type'
            },
            'jora.com': {
                'title': 'h1[data-testid="job-title"]',
                'company': '[data-testid="company-name"]',
                'description': '[data-testid="job-description"]',
                'location': '[data-testid="job-location"]'
            },
            'indeed.com.au': {
                'title': 'h1[data-testid="jobsearch-JobInfoHeader-title"]',
                'company': '[data-testid="inlineHeader-companyName"]',
                'description': '#jobDescriptionText',
                'location': '[data-testid="job-location"]'
            },
            'linkedin.com': {
                'title': 'h1.top-card-layout__title',
                'company': '.top-card-layout__card .top-card-layout__entity-info h4',
                'description': '.show-more-less-html__markup',
                'location': '.top-card-layout__second-subline'
            }
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 1.0  # Minimum delay between requests (seconds)
    
    async def scrape_job_ad(self, url: str) -> Dict[str, Any]:
        """
        Scrape job advertisement from the provided URL.
        
        Args:
            url: Job advertisement URL
            
        Returns:
            Dictionary containing extracted job information
        """
        
        try:
            # Parse URL to determine site
            parsed_url = urlparse(url)
            site_domain = parsed_url.netloc.lower()
            
            # Remove 'www.' prefix if present
            if site_domain.startswith('www.'):
                site_domain = site_domain[4:]
            
            print(f"Scraping job from: {site_domain}")
            
            # Get site-specific selectors
            selectors = self._get_selectors_for_site(site_domain)
            
            if not selectors:
                return self._create_fallback_job_data(url, "Unsupported job site")
            
            # Fetch page content
            html_content = await self._fetch_page(url)
            
            if not html_content:
                return self._create_fallback_job_data(url, "Failed to fetch page content")
            
            # Parse HTML and extract job information
            job_data = self._extract_job_info(html_content, selectors, url)
            
            # Post-process and validate data
            job_data = self._validate_and_clean_job_data(job_data)
            
            print(f"Successfully scraped job: {job_data.get('job_title', 'Unknown')}")
            return job_data
            
        except Exception as e:
            print(f"Error scraping job ad: {str(e)}")
            return self._create_fallback_job_data(url, f"Scraping error: {str(e)}")
    
    async def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from the provided URL with rate limiting.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content string or None if failed
        """
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            await asyncio.sleep(self.min_delay - time_since_last)
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers) as response:
                    
                    self.last_request_time = time.time()
                    
                    if response.status == 200:
                        content = await response.text()
                        return content
                    else:
                        print(f"HTTP error {response.status} for URL: {url}")
                        return None
                        
        except asyncio.TimeoutError:
            print(f"Timeout fetching URL: {url}")
            return None
            
        except Exception as e:
            print(f"Error fetching URL {url}: {str(e)}")
            return None
    
    def _get_selectors_for_site(self, domain: str) -> Optional[Dict[str, str]]:
        """
        Get CSS selectors for the specified site domain.
        
        Args:
            domain: Site domain name
            
        Returns:
            Dictionary of CSS selectors or None if unsupported
        """
        
        for site_key, selectors in self.site_selectors.items():
            if site_key in domain:
                return selectors
        
        return None
    
    def _extract_job_info(self, html_content: str, selectors: Dict[str, str], 
                         source_url: str) -> Dict[str, Any]:
        """
        Extract job information from HTML using CSS selectors.
        
        Args:
            html_content: HTML content to parse
            selectors: CSS selectors for extracting information
            source_url: Original URL for reference
            
        Returns:
            Dictionary containing extracted job information
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        job_data = {
            'source_url': source_url,
            'scraped_at': time.time()
        }
        
        # Extract basic job information
        job_data['job_title'] = self._extract_text(soup, selectors.get('title', ''))
        job_data['company_name'] = self._extract_text(soup, selectors.get('company', ''))
        job_data['location'] = self._extract_text(soup, selectors.get('location', ''))
        job_data['salary'] = self._extract_text(soup, selectors.get('salary', ''))
        job_data['employment_type'] = self._extract_text(soup, selectors.get('type', ''))
        
        # Extract job description (main content)
        description_element = soup.select_one(selectors.get('description', ''))
        if description_element:
            job_data['job_description'] = self._clean_text(description_element.get_text())
        else:
            job_data['job_description'] = self._extract_fallback_description(soup)
        
        # Extract key responsibilities and selection criteria
        responsibilities, criteria = self._extract_structured_content(job_data['job_description'])
        job_data['key_responsibilities'] = responsibilities
        job_data['selection_criteria'] = criteria
        
        return job_data
    
    def _extract_text(self, soup: BeautifulSoup, selector: str) -> str:
        """
        Extract and clean text from a CSS selector.
        
        Args:
            soup: BeautifulSoup object
            selector: CSS selector string
            
        Returns:
            Cleaned text string
        """
        
        if not selector:
            return ""
        
        try:
            element = soup.select_one(selector)
            if element:
                return self._clean_text(element.get_text())
            return ""
            
        except Exception as e:
            print(f"Error extracting text with selector '{selector}': {str(e)}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text string
        """
        
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        text = re.sub(r'[^\w\s\-.,!?():;&@#$%]', '', text)
        
        return text
    
    def _extract_fallback_description(self, soup: BeautifulSoup) -> str:
        """
        Extract job description using fallback methods when primary selector fails.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Job description text
        """
        
        # Try common generic selectors
        fallback_selectors = [
            '.job-description',
            '#job-description',
            '[class*="description"]',
            '[id*="description"]',
            'main',
            'article',
            '.content'
        ]
        
        for selector in fallback_selectors:
            elements = soup.select(selector)
            if elements:
                # Take the largest text block
                best_element = max(elements, key=lambda x: len(x.get_text()))
                return self._clean_text(best_element.get_text())
        
        # Last resort: extract all paragraph text
        paragraphs = soup.find_all('p')
        if paragraphs:
            return ' '.join([self._clean_text(p.get_text()) for p in paragraphs])
        
        return "Job description could not be extracted"
    
    def _extract_structured_content(self, description: str) -> tuple[str, str]:
        """
        Extract key responsibilities and selection criteria from job description.
        
        Args:
            description: Full job description text
            
        Returns:
            Tuple of (key_responsibilities, selection_criteria)
        """
        
        responsibilities = ""
        criteria = ""
        
        # Split description into sections
        sections = re.split(r'\n\s*\n|\r\n\s*\r\n', description)
        
        for section in sections:
            section_lower = section.lower()
            
            # Check if section contains responsibilities
            if any(keyword in section_lower for keyword in [
                'responsibilities', 'duties', 'role', 'will be responsible',
                'key tasks', 'primary duties', 'you will'
            ]):
                if len(section) > len(responsibilities):
                    responsibilities = section
            
            # Check if section contains selection criteria
            elif any(keyword in section_lower for keyword in [
                'requirements', 'qualifications', 'criteria', 'essential',
                'experience required', 'skills', 'must have', 'desirable'
            ]):
                if len(section) > len(criteria):
                    criteria = section
        
        return self._clean_text(responsibilities), self._clean_text(criteria)
    
    def _validate_and_clean_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted job data.
        
        Args:
            job_data: Raw extracted job data
            
        Returns:
            Validated and cleaned job data
        """
        
        # Ensure required fields have values
        required_fields = ['job_title', 'company_name', 'job_description']
        
        for field in required_fields:
            if not job_data.get(field) or job_data[field].strip() == "":
                job_data[field] = f"Not specified"
        
        # Limit field lengths to prevent excessive data
        max_lengths = {
            'job_title': 200,
            'company_name': 100,
            'location': 100,
            'salary': 100,
            'employment_type': 50,
            'job_description': 10000,
            'key_responsibilities': 5000,
            'selection_criteria': 5000
        }
        
        for field, max_length in max_lengths.items():
            if job_data.get(field) and len(job_data[field]) > max_length:
                job_data[field] = job_data[field][:max_length] + "..."
        
        return job_data
    
    def _create_fallback_job_data(self, url: str, error_message: str) -> Dict[str, Any]:
        """
        Create fallback job data structure when scraping fails.
        
        Args:
            url: Original job URL
            error_message: Description of the error
            
        Returns:
            Fallback job data dictionary
        """
        
        return {
            'source_url': url,
            'scraped_at': time.time(),
            'job_title': 'Job Title Not Available',
            'company_name': 'Company Not Available',
            'location': 'Location Not Specified',
            'salary': 'Not Specified',
            'employment_type': 'Not Specified',
            'job_description': f'Unable to extract job description. {error_message}. Please manually copy the job details.',
            'key_responsibilities': 'Please manually extract key responsibilities from the job advertisement.',
            'selection_criteria': 'Please manually extract selection criteria from the job advertisement.',
            'error': error_message
        }
    
    async def test_scraper(self, test_urls: list[str]) -> Dict[str, Any]:
        """
        Test the scraper with multiple URLs for validation.
        
        Args:
            test_urls: List of URLs to test
            
        Returns:
            Test results summary
        """
        
        results = {
            'total_tests': len(test_urls),
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'results': []
        }
        
        for url in test_urls:
            try:
                job_data = await self.scrape_job_ad(url)
                
                if 'error' not in job_data:
                    results['successful_scrapes'] += 1
                    status = 'success'
                else:
                    results['failed_scrapes'] += 1
                    status = 'failed'
                
                results['results'].append({
                    'url': url,
                    'status': status,
                    'title': job_data.get('job_title', 'N/A'),
                    'company': job_data.get('company_name', 'N/A')
                })
                
            except Exception as e:
                results['failed_scrapes'] += 1
                results['results'].append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
