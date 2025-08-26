"""Faculty clubs scraper"""
import asyncio
import aiohttp
import json
from typing import List, Dict
import logging
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

from .base import BaseScraper
from models.organization import Organization

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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