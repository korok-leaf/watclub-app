"""WUSA clubs scraper with concurrent processing."""
import asyncio
import aiohttp
from typing import List, Dict
from bs4 import BeautifulSoup
import logging
from openai import AsyncOpenAI
import json
from dotenv import load_dotenv

load_dotenv()

from .base import BaseScraper
from models.organization import Organization

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WUSAScraper(BaseScraper):
    def __init__(self):
        super().__init__("wusa")
        self.base_url = "https://clubs.wusa.ca"
    
    async def scrape(self) -> List[Organization]:
        """Main scraping: collect all club links across pages, then process concurrently"""
        all_organizations = []
        all_club_links: List[str] = []
        page = 1
        
        async with aiohttp.ClientSession() as session:
            while True:
                logger.info(f"Processing page {page}")
                page_url = f"{self.base_url}/club_listings?page={page}"
                club_links = await self.get_club_links_from_page(session, page_url)
                
                if not club_links:
                    logger.info(f"No clubs found on page {page}, stopping")
                    break
                
                logger.info(f"Found {len(club_links)} clubs on page {page}")
                all_club_links.extend(club_links)
                page += 1

            if all_club_links:
                logger.info(f"Processing {len(all_club_links)} clubs concurrently")
                all_organizations = await self.process_clubs_concurrent(session, all_club_links)
        
        logger.info(f"Total organizations scraped: {len(all_organizations)}")
        return all_organizations
    
    async def get_club_links_from_page(self, session: aiohttp.ClientSession, page_url: str) -> List[str]:
        """Extract club links from a listings page"""
        async with session.get(page_url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            links = []
            for link in soup.find_all('a', href=True):
                if 'Learn More' in link.text and '/clubs/' in link['href']:
                    links.append(link['href'])
            
            return links
    
    async def process_clubs_concurrent(self, session: aiohttp.ClientSession, club_links: List[str]) -> List[Organization]:
        """Process multiple clubs concurrently"""
        tasks = [self.scrape_single_club(session, link) for link in club_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        organizations = [org for org in results if isinstance(org, Organization)]
        return organizations
    
    async def scrape_single_club(self, session: aiohttp.ClientSession, club_path: str) -> Organization:
        """Scrape individual club page"""
        club_url = f"{self.base_url}{club_path}"
        logger.info(f"Scraping club: {club_url}")
        
        try:
            async with session.get(club_url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find the main container
                container = soup.find('div', class_='container mt-4')
                if not container:
                    logger.warning(f"No container found for {club_url}")
                    return None
                
                # Extract club name
                club_name = "Unknown Club"
                name_header = container.find('h5', class_='club-name-header')
                if name_header:
                    club_name = name_header.get_text(strip=True)
                else:
                    logger.warning(f"No name header found for {club_url}")
                    return None
                
                # Extract last active term
                last_active = "Unknown"
                active_button = container.find('button', class_='last-active-button')
                if active_button:
                    last_active = active_button.get_text(strip=True)
                
                # Collect all contact information for LLM processing
                contacts_for_llm = []
                
                # Get contacts
                contact_buttons = container.find_all(class_='contact-button')
                for button in contact_buttons:
                    contact_text = button.get_text(strip=True)
                    if contact_text:
                        contacts_for_llm.append(contact_text)
                    # Also check for href attribute
                    if button.get('href'):
                        contacts_for_llm.append(button['href'])
                
                # Get contacts from dashboard-icon-container divs
                icon_containers = container.find_all('div', class_='dashboard-icon-container')
                for icon_container in icon_containers:
                    # Find all links within this container
                    links = icon_container.find_all('a', href=True)
                    for link in links:
                        if link.get('title'):
                            contacts_for_llm.append(f"{link['title']}: {link['href']}")
                        else:
                            contacts_for_llm.append(link['href'])
                
                # Get description
                description_for_llm = ""
                
                full_text_element = container.find(id='full-text')
                if full_text_element:
                    description_for_llm = full_text_element.get_text(strip=True)

                # Create contacts prompt for LLM
                contacts_prompt = f"Extract contact information from: {' | '.join(contacts_for_llm)}" if contacts_for_llm else ""
                
                # Process with LLM
                llm_result = await self.process_with_llm(description_for_llm, contacts_for_llm)
                
                return Organization(
                    name=club_name,
                    org_type="wusa",
                    description=llm_result.get("cleaned_description", ""),
                    last_active=last_active,
                    source_url=club_url,
                    social_media=llm_result.get("social_media", {}),
                    membership_info="; ".join(llm_result.get("other_contacts", [])) if llm_result.get("other_contacts") else None
                )
                
        except Exception as e:
            logger.error(f"Error scraping club {club_url}: {str(e)}")
            return None

    async def process_with_llm(self, description: str, contacts_for_llm: List[str]) -> Dict[str, any]:
        """
        Use LLM to clean description and extract/format social media links.
        Returns: dict with cleaned_description and formatted socials
        """

        contacts_text = ' | '.join(contacts_for_llm) if contacts_for_llm else ""
        
        prompt = f"""
You are tasked with cleaning and formatting club information. Please:

1. Clean the description text by fixing any spacing errors, but DO NOT change the wording or content
2. Extract ALL social media links from both the description and contacts
3. Return a JSON object with the following structure:

{{
    "cleaned_description": "cleaned description text with fixed spacing but same wording",
    "cleaned_contacts": "cleaned contact information with fixed spacing but same wording",
    "social_media": {{
        "instagram": ["list of instagram URLs"],
        "facebook": ["list of facebook URLs"], 
        "twitter": ["list of twitter/x URLs"],
        "linkedin": ["list of linkedin URLs"],
        "discord": ["list of discord URLs"],
        "website": ["list of other website URLs"]
        "youtube": ["list of youtube URLs"],
        "email": ["list of email addresses"],
        ...
    }}
}}

Important rules:
- Convert ALL @usernames to full URLs for social platforms
- Remove ALL contact information from the cleaned_description
- Only include social_media categories that have actual content
- Remove duplicates
- If there are obvious typos in description and social media links, fix them


Description to clean:
{description}

Contact information to process:
{contacts_text}
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
                logger.warning("Empty response from LLM")
                raise ValueError("Empty response from LLM")
            
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
                "cleaned_description": description,
                "social_media": {},
                "email": [],
                "other_contacts": contacts_for_llm
            }
        except Exception as e:
            logger.error(f"Error processing with LLM: {str(e)}")
            return {
                "cleaned_description": description,
                "social_media": {},
                "email": [],
                "other_contacts": contacts_for_llm
            }


async def main():
    """Test the WUSA scraper"""
    logger.info("Starting WUSA scraper test")
    
    scraper = WUSAScraper()
    organizations = await scraper.run()
    
    logger.info(f"Test complete: {len(organizations)} organizations scraped")
    
    # Print first few results
    for i, org in enumerate(organizations[:3]):
        logger.info(f"Sample {i+1}: {org.name}")


if __name__ == "__main__":
    asyncio.run(main())