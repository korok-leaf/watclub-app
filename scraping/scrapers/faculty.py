"""Faculty clubs scraper"""
import asyncio
import aiohttp
import json
from typing import List, Dict
import logging
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from dotenv import load_dotenv
import re

load_dotenv()

from .base import BaseScraper
from models.organization import Organization

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_slug(name: str) -> str:
    """Convert club name to URL-friendly slug."""
    # Convert to lowercase
    slug = name.lower()
    # Replace non-alphanumeric characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


class FacultyScraper(BaseScraper):
    def __init__(self):
        super().__init__("faculty")
        self.base_urls = {
            "mathsoc": "https://mathsoc.uwaterloo.ca/community/community",
            "scisoc": "https://uwaterloo.ca/science-society/departmental-clubs",
            "engsoc": "https://www.engsoc.uwaterloo.ca/about-us/affiliates/",
        }
    
    async def scrape(self) -> List[Organization]:
        """Main scraping method - processes all faculty club directories concurrently"""
        all_organizations = []
        
        tasks = [
            self.scrape_faculty(faculty_name, base_url) 
            for faculty_name, base_url in self.base_urls.items()
        ]
        
        logger.info(f"Starting concurrent scraping of {len(tasks)} faculties")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, (faculty_name, result) in enumerate(zip(self.base_urls.keys(), results)):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {faculty_name}: {result}")
            elif isinstance(result, list):
                logger.info(f"Successfully scraped {len(result)} clubs from {faculty_name}")
                all_organizations.extend(result)
            else:
                logger.warning(f"Unexpected result type from {faculty_name}: {type(result)}")
        
        logger.info(f"Total faculty clubs scraped: {len(all_organizations)}")
        return all_organizations
    
    async def scrape_faculty(self, faculty_name: str, base_url: str) -> List[Organization]:
        """Scrape clubs from a specific faculty directory"""
        logger.info(f"Starting to scrape {faculty_name}")
        if faculty_name in ["mathsoc", "engsoc"]:
            return await self.scrape_with_llm_parsing(faculty_name, base_url)
        elif faculty_name == "scisoc":
            return await self.scrape_scisoc(base_url)
        else:
            # TODO: Implement other faculty-specific scraping logic
            logger.info(f"Skipping {faculty_name} - not implemented yet")
            return []

    async def scrape_with_llm_parsing(self, faculty_name: str, base_url: str) -> List[Organization]:
        """Use LLM reasoning to parse faculty pages and extract club information"""
        organizations = []
        
        async with aiohttp.ClientSession() as session:
            try:
                # Fetch the page content
                async with session.get(base_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch {base_url}: HTTP {response.status}")
                        return []
                    
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract all text content
                    page_text = soup.get_text(separator='\n', strip=True)
                    
                    # Use reasoning model to parse content
                    clubs_data = await self.parse_content_with_reasoning_llm(
                        faculty_name, page_text
                    )
                    
                    # Process each club
                    for club_data in clubs_data:
                        try:
                            # Create organization
                            org = Organization(
                                name=club_data['name'],
                                slug=generate_slug(club_data['name']),
                                org_type="faculty",
                                description=club_data['description'],
                                faculty=faculty_name,
                                social_media=club_data.get('social_media', {}),
                                source_url=base_url,
                                last_active="Current"
                            )
                            
                            organizations.append(org)
                            logger.info(f"Created organization for {club_data['name']}")
                            
                        except Exception as e:
                            logger.error(f"Error creating organization for {club_data.get('name', 'unknown')}: {e}")
                
            except Exception as e:
                logger.error(f"Error scraping {faculty_name}: {e}")
        
        return organizations

    async def create_organization(self, club_data: Dict[str, str], faculty_name: str, social_media: Dict[str, List[str]]) -> Organization:
        """Create Organization object from club data"""
        return Organization(
            name=club_data["name"],
            org_type="faculty",
            description=club_data["description"],
            faculty=faculty_name,
            social_media=social_media,
            source_url=self.base_urls.get(faculty_name, ""),
            last_active="Current"
        )

    async def parse_content_with_reasoning_llm(self, faculty_name: str, page_text: str) -> List[Dict]:
        """Use reasoning model to parse faculty page content and extract club information"""
        
        prompt = f"""
You are tasked with analyzing a {faculty_name} faculty page from University of Waterloo to extract student club information.

Faculty: {faculty_name}
Page Content:
{page_text}

Please carefully analyze this content and extract ALL student clubs/organizations mentioned. For each club, provide:

1. Club name (exact name as mentioned)
2. Description (clean, comprehensive description. Do not change the wording or content.)
3. Social media links (if any are mentioned)

CRITICAL: Return ONLY valid JSON. No comments, no duplicate keys, no trailing commas.

Return a JSON array with this structure:
[
  {{
    "name": "Club Name",
    "description": "Clean description of the club",
    "social_media": {{
      "website": ["list of website URLs"],
      "email": ["list of email addresses"], 
      "facebook": ["list of Facebook URLs"],
      "instagram": ["list of Instagram URLs"],
      "twitter": ["list of Twitter/X URLs"],
      "linkedin": ["list of LinkedIn URLs"],
      "discord": ["list of Discord URLs"]
    }}
  }}
]

Important guidelines:
- Carefully separate different clubs - don't merge them
- Extract complete descriptions for each club. Do not change the wording or content.
- Only include social media links that are explicitly mentioned
- Be thorough - don't miss any clubs mentioned in the content
- Ignore WUSA (Waterloo Undergraduate Student Association)
"""

        try:
            client = AsyncOpenAI()
            
            response = await client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_content = response.choices[0].message.content
            
            # Clean JSON from markdown if present
            if "```json" in response_content:
                start = response_content.find("```json") + 7
                end = response_content.find("```", start)
                if end != -1:
                    response_content = response_content[start:end].strip()
            elif "```" in response_content:
                start = response_content.find("```") + 3
                end = response_content.find("```", start)
                if end != -1:
                    response_content = response_content[start:end].strip()
            
            result = json.loads(response_content)
            logger.info(f"LLM extracted {len(result)} clubs from {faculty_name}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {faculty_name}: {e}")
            logger.error(f"Response was: {response_content}")
            return []
        except Exception as e:
            logger.error(f"LLM parsing failed for {faculty_name}: {e}")
            return []

    async def scrape_scisoc(self, base_url: str) -> List[Organization]:
        """Scrape Science Society clubs using BeautifulSoup"""
        organizations = []
        
        async with aiohttp.ClientSession() as session:
            try:
                # Fetch the page content
                async with session.get(base_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch {base_url}: HTTP {response.status}")
                        return []
                    
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Find all club sections
                    summaries = soup.find_all(class_='details__summary')
                    contents = soup.find_all(class_='details__content')
                    
                    if len(summaries) != len(contents):
                        logger.warning(f"Mismatched summaries ({len(summaries)}) and contents ({len(contents)})")
                    
                    # Process clubs concurrently
                    tasks = []
                    for summary, content in zip(summaries, contents):
                        # Get club name from summary (all text recursively)
                        club_name = summary.get_text(separator=' ', strip=True)
                        
                        # Get all text from content
                        content_text = content.get_text(separator='\n', strip=True)
                        
                        # Create task for concurrent processing
                        task = self.process_scisoc_club(club_name, content_text, base_url)
                        tasks.append(task)
                    
                    # Execute all tasks concurrently
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Filter successful results
                    for result in results:
                        if isinstance(result, Organization):
                            organizations.append(result)
                        elif isinstance(result, Exception):
                            logger.error(f"Error processing Science Society club: {result}")
                
            except Exception as e:
                logger.error(f"Error scraping Science Society: {e}")
        
        logger.info(f"Scraped {len(organizations)} Science Society clubs")
        return organizations
    
    async def process_scisoc_club(self, club_name: str, content_text: str, base_url: str) -> Organization:
        """Process individual Science Society club with LLM"""
        try:
            llm_result = await self.process_scisoc_with_llm(club_name, content_text)
            
            return Organization(
                name=club_name,
                slug=generate_slug(club_name),
                org_type="faculty",
                description=llm_result.get("cleaned_description", ""),
                faculty="scisoc",
                social_media=llm_result.get("social_media", {}),
                source_url=base_url,
                last_active="Current"
            )
            
        except Exception as e:
            logger.error(f"Error processing Science Society club {club_name}: {e}")
            raise
    
    async def process_scisoc_with_llm(self, club_name: str, content_text: str) -> Dict[str, any]:
        """Use LLM to clean and extract information from Science Society club content"""
        
        prompt = f"""
You are tasked with cleaning and formatting club information for {club_name}. Please:

1. Clean the description text by fixing any spacing errors, but DO NOT change the wording or content
2. Extract ALL social media links and contact information
3. Return a JSON object with the following structure:

{{
    "cleaned_description": "cleaned description text with fixed spacing but same wording",
    "social_media": {{
        "instagram": ["list of instagram URLs"],
        "facebook": ["list of facebook URLs"], 
        "twitter": ["list of twitter/x URLs"],
        "linkedin": ["list of linkedin URLs"],
        "discord": ["list of discord URLs"],
        "website": ["list of other website URLs"],
        "youtube": ["list of youtube URLs"],
        "email": ["list of email addresses"]
    }}
}}

Important rules:
- Convert ALL @usernames to full URLs for social platforms
- Remove ALL contact information from the cleaned_description
- Only include social_media categories that have actual content
- Remove duplicates
- If there are obvious typos in description and social media links, fix them
- Extract email addresses even if they're written as "email: example@uwaterloo.ca"

Club Name: {club_name}

Content to process:
{content_text}
"""

        try:
            client = AsyncOpenAI()
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that cleans and formats club information. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            response_content = response.choices[0].message.content
            
            if not response_content or response_content.strip() == "":
                logger.warning(f"Empty response from LLM for {club_name}")
                raise ValueError("Empty response from LLM")
            
            # Clean JSON from markdown if present
            if "```json" in response_content:
                start = response_content.find("```json") + 7
                end = response_content.find("```", start)
                if end != -1:
                    response_content = response_content[start:end].strip()
            elif "```" in response_content:
                start = response_content.find("```") + 3
                end = response_content.find("```", start)
                if end != -1:
                    response_content = response_content[start:end].strip()
            
            result = json.loads(response_content)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {club_name}: {e}. Response was: {response_content}")
            return {
                "cleaned_description": content_text,
                "social_media": {}
            }
        except Exception as e:
            logger.error(f"Error processing {club_name} with LLM: {str(e)}")
            return {
                "cleaned_description": content_text,
                "social_media": {}
            }


async def main():
    """Test the Faculty scraper"""
    logger.info("Starting Faculty scraper test")
    
    scraper = FacultyScraper()
    organizations = await scraper.run()
    
    logger.info(f"Test complete: {len(organizations)} organizations scraped")
    
    # Print first few results
    for i, org in enumerate(organizations[:3]):
        logger.info(f"Sample {i+1}: {org.name}")


if __name__ == "__main__":
    asyncio.run(main())