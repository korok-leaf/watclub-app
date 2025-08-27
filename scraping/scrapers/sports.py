"""Sports clubs scraper for Warrior Recreation clubs."""
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import logging
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from openai import AsyncOpenAI
import os
import json
from pydantic import BaseModel
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


class SportsScraper(BaseScraper):
    def __init__(self):
        super().__init__("sports")
        self.base_url = "https://athletics.uwaterloo.ca/sports/2012/9/4/Warrior_Recreation_Clubs.aspx"
    
    async def scrape(self) -> List[Organization]:
        """Scrape sports clubs from Warrior Recreation website."""
        all_organizations = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(self.base_url)
            
            # Wait for accordion content to load
            await page.wait_for_selector('.c-story-blocks__structural_accordion_block__list-item-content')
            
            # Get the HTML after JS execution
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all accordion content divs (both active and inactive)
            accordion_divs = soup.find_all('div', 
                class_=['c-story-blocks__structural_accordion_block__list-item-content ui-accordion-content ui-corner-bottom ui-helper-reset ui-widget-content',
                        'c-story-blocks__structural_accordion_block__list-item-content ui-accordion-content ui-corner-bottom ui-helper-reset ui-widget-content ui-accordion-content-active']
            )

            logger.info(f"Found {len(accordion_divs)} sports club divs")
                
            # Extract club info (name and link) from these divs
            club_info = []
            for div in accordion_divs:
                links = div.find_all('a', href=True)
                for link in links:
                    club_name = link.get_text(strip=True)
                    club_url = link['href']
                    if club_name and club_url:  # Only add if both name and URL exist
                        club_info.append({
                            'name': club_name,
                            'url': club_url
                        })

            # Remove duplicates based on URL
            seen_urls = set()
            unique_clubs = []
            for club in club_info:
                if club['url'] not in seen_urls:
                    seen_urls.add(club['url'])
                    unique_clubs.append(club)
            
            logger.info(f"Found {len(unique_clubs)} unique sports clubs")
            
            # Pass browser and club info
            organizations = await self.process_clubs_concurrent(browser, unique_clubs)
            all_organizations.extend(organizations)
            
            await browser.close()
    
        logger.info(f"Total sports clubs scraped: {len(all_organizations)}")
        return all_organizations

    async def process_clubs_concurrent(self, browser, club_info: List[Dict[str, str]]) -> List[Organization]:
        """Process multiple clubs concurrently"""
        tasks = [self.scrape_single_sport(browser, club['name'], club['url']) for club in club_info]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        organizations = []
        
        # Log any exceptions with the actual link
        for i, (result, club) in enumerate(zip(results, club_info)):
            if isinstance(result, Organization):
                organizations.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Error processing {club['name']} at {club['url']}: {result}")
        
        return organizations

    async def scrape_single_sport(self, browser, club_name: str, club_url: str) -> Organization:
        """Scrape individual sports club page"""
        page = await browser.new_page()
        try:
            await page.goto(club_url)
            
            await page.wait_for_selector('.c-story-blocks')
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find the main content div
            content_div = soup.find('div', class_='c-story-blocks')
            
            if content_div:
                # Get all text (strips HTML tags)
                all_text = content_div.get_text(separator='\n', strip=True)
                
                # Get all links within this div
                links = {}
                for link in content_div.find_all('a', href=True):
                    link_text = link.get_text(strip=True)
                    link_url = link['href']
                    if link_text:
                        links[link_text] = link_url

            organization = await self.process_with_llm(club_name, all_text, links, club_url)
            return organization
        
        finally:
            await page.close()
    
    async def process_with_llm(self, club_name: str, all_text: str, links: Dict[str, str], club_url: str) -> Organization:
        """Process the text and links with LLM"""
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Get relevant fields from Organization model
        prompt = f"""
Extract sports club information for "{club_name}" and return JSON with these fields:
- description: string (main description/purpose) 
- social_media: object with keys like "instagram", "facebook", "email" mapping to arrays of URLs
- meeting_info: object with schedule/location info, or null
- membership_info: string about fees/how to join, or null

Example output:
{{
    "description": "Wrestling Club welcomes all students to participate in learning wrestling techniques and skills...",
    "social_media": {{
        "instagram": ["https://instagram.com/uw.wrestling"],
        "email": ["mailto:uwwrestling.club@uwaterloo.ca"]
    }},
    "meeting_info": {{
        "schedule": "Thursday 8-10pm",
        "location": "PAC Activity Area"
    }},
    "membership_info": "$66.00 + HST / term"
}}

Text to extract from:
{all_text}

Links found:
{json.dumps(links, indent=2)}

Return valid JSON only. Do NOT include the name field as it's already provided.
"""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        # Parse response
        extracted = json.loads(response.choices[0].message.content)
        
        # Create Organization with deterministic name
        return Organization(
            name=club_name,  # Use the name from the anchor tag
            slug=generate_slug(club_name),
            description=extracted.get('description'),
            social_media=extracted.get('social_media', {}),
            meeting_info=extracted.get('meeting_info'),
            membership_info=extracted.get('membership_info'),
            org_type="sports",
            is_active=True,
            last_active="Fall 2025",
            source_url=club_url,
            tags=[]
        )


async def main():
    """Test the Sports scraper"""
    logger.info("Starting Sports scraper test")
    
    scraper = SportsScraper()
    organizations = await scraper.run()
    
    logger.info(f"Test complete: {len(organizations)} organizations scraped")


if __name__ == "__main__":
    asyncio.run(main())
