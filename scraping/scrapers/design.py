"""Design teams scraper with concurrent processing."""
import asyncio
import aiohttp
import json
from typing import List, Dict
from bs4 import BeautifulSoup
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

from .base import BaseScraper
from models.organization import Organization

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DesignScraper(BaseScraper):
    def __init__(self):
        super().__init__("design")
        self.base_url = "https://uwaterloo.ca/sedra-student-design-centre/directory-teams"
    
    async def scrape(self) -> List[Organization]:
        """Main scraping: get all design teams and process them concurrently"""
        all_organizations = []
        
        async with aiohttp.ClientSession() as session:
            logger.info("Fetching design teams directory")
            team_sections, team_summary = await self.get_team_sections(session)
            
            if not team_sections:
                logger.warning("No design teams found")
                return []
            
            logger.info(f"Found {len(team_sections)} design teams")
            organizations = await self.process_teams_concurrent(session, team_sections, team_summary)
            all_organizations.extend(organizations)
        
        logger.info(f"Total design teams scraped: {len(all_organizations)}")
        return all_organizations
    
    async def get_team_sections(self, session: aiohttp.ClientSession) -> List[BeautifulSoup]:
        """Extract all design team sections from the main page"""
        async with session.get(self.base_url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all div elements with class 'details__content'
            team_sections = soup.find_all('div', class_='details__content')
            team_summary = soup.find_all('summary', class_='details__summary')
            
            logger.info(f"Found {len(team_sections)} team sections")
            return team_sections, team_summary
    
    async def process_teams_concurrent(self, session: aiohttp.ClientSession, team_sections: List[BeautifulSoup], team_summary: List[BeautifulSoup]) -> List[Organization]:
        """Process multiple design teams concurrently"""
        tasks = [self.scrape_single_team(session, section, summary) for section, summary in zip(team_sections, team_summary)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        organizations = [org for org in results if isinstance(org, Organization)]
        
        # Log any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing team {i}: {result}")
        
        return organizations
    
    async def scrape_single_team(self, session: aiohttp.ClientSession, section: BeautifulSoup, summary: BeautifulSoup) -> Organization:
        """Scrape individual design team section"""
        try:
            section_text = section.get_text(separator=' ', strip=True)

            team_name = summary.get_text(separator=' ', strip=True)
            
            llm_result = await self.process_with_llm(section_text)
            
            if not llm_result:
                logger.warning("LLM failed to process section, skipping")
                return None
            
            description = llm_result.get("description", "")
            social_media = llm_result.get("social_media", {})
            
            logger.info(f"Scraped design team: {team_name}")
            
            return Organization(
                name=team_name,
                org_type="design_team",
                description=description,
                social_media=social_media,
                source_url=self.base_url,
                last_active="Current"
            )
            
        except Exception as e:
            logger.error(f"Error scraping design team section: {str(e)}")
            return None

    async def process_with_llm(self, section_text: str) -> Dict[str, any]:
        """
        Use LLM to extract team information from section text.
        Returns: dict with name, description, and social_media
        """
        
        prompt = f"""
You are tasked with extracting design team information from university website content. Please:

1. Extract the team name (should be clear from headings/context)
2. Extract a clean description (remove any contact info from description)
3. Extract ALL contact/social media information

Return a JSON object with the following structure:

{{
    "description": "Clean description without contact information",
    "social_media": {{
        "website": ["list of website URLs"],
        "email": ["list of email addresses"],
        "facebook": ["list of facebook URLs"],
        "instagram": ["list of instagram URLs"],
        "twitter": ["list of twitter/x URLs"],
        "linkedin": ["list of linkedin URLs"],
        "youtube": ["list of youtube URLs"],
        "discord": ["list of discord URLs"]
    }}
}}

Important rules:
- Convert ALL @usernames to full URLs for social platforms
- Remove ALL contact information from the description
- Only include social_media categories that have actual content
- Remove duplicates
- Fix obvious typos in URLs

Content to process:
{section_text}
"""

        try:
            client = AsyncOpenAI()
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts design team information. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            response_content = response.choices[0].message.content
            
            if not response_content or response_content.strip() == "":
                logger.warning("Empty response from LLM")
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
            logger.error(f"JSON decode error: {e}. Response was: {response_content}")
            return {
                "name": "Unknown Team",
                "description": section_text[:500],  # Fallback to truncated text
                "social_media": {}
            }
        except Exception as e:
            logger.error(f"Error processing with LLM: {str(e)}")
            return {
                "name": "Unknown Team", 
                "description": section_text[:500],  # Fallback to truncated text
                "social_media": {}
            }


async def main():
    """Test the Design scraper"""
    logger.info("Starting Design scraper test")
    
    scraper = DesignScraper()
    organizations = await scraper.run()
    
    logger.info(f"Test complete: {len(organizations)} organizations scraped")
    
    # Print first few results
    for i, org in enumerate(organizations[:3]):
        logger.info(f"Sample {i+1}: {org.name}")


if __name__ == "__main__":
    asyncio.run(main())