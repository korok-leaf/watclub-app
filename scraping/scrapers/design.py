"""Design teams scraper with concurrent processing."""
import asyncio
import aiohttp
import json
import aiofiles
import os
from typing import List, Dict
from bs4 import BeautifulSoup
import logging
from pathlib import Path
from urllib.parse import urlparse
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
            
            # Extract and download team image
            image_path = await self.download_team_image(session, section, team_name)
            
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

    async def download_team_image(self, session: aiohttp.ClientSession, section: BeautifulSoup, team_name: str) -> str:
        """Download team image from section and save to watclub/public/design/{name}"""
        try:
            # Find the first (and only) img tag in this section
            img_tag = section.find('img')
            if not img_tag:
                logger.warning(f"No image found for team: {team_name}")
                return None
            
            img_src = img_tag.get('src')
            if not img_src:
                logger.warning(f"No src attribute in img tag for team: {team_name}")
                return None
            
            # Handle relative URLs
            if img_src.startswith('/'):
                img_src = f"https://uwaterloo.ca{img_src}"
            elif not img_src.startswith('http'):
                img_src = f"https://uwaterloo.ca/{img_src}"
            
            # Create safe filename
            safe_name = "".join(c if c.isalnum() or c in ('-', '_', ' ') else '' for c in team_name)
            safe_name = safe_name.replace(' ', '-').lower().strip('-')
            
            # Use pathlib to find the project root and create the path
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            image_dir = project_root / "watclub" / "public" / "design"
            image_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine file extension from image URL
            parsed_url = urlparse(img_src)
            ext = os.path.splitext(parsed_url.path)[1]
            
            # Default to .jpg if no extension or unknown extension
            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                ext = '.jpg'
            
            filename = f"{safe_name}{ext}"
            filepath = image_dir / filename
            
            # Check if file already exists
            if filepath.exists():
                logger.info(f"Image already exists for {team_name}: {filename}")
                return f"/design/{filename}"
            
            # Download the image
            async with session.get(img_src) as response:
                if response.status == 200:
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    logger.info(f"Saved image for {team_name}: {filename}")
                    return f"/design/{filename}"
                else:
                    logger.error(f"Failed to download image: HTTP {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error downloading image for {team_name}: {e}")
            return None


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
