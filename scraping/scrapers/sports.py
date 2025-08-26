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

load_dotenv()

from .base import BaseScraper
from models.organization import Organization

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
                
            # Extract all links from these divs
            club_links = []
            for div in accordion_divs:
                links = div.find_all('a', href=True)
                for link in links:
                    club_links.append(link['href'])

            club_links = list(set(club_links))
            
            logger.info(f"Found {len(club_links)} sports club links")
            
            # Pass browser 
            organizations = await self.process_clubs_concurrent(browser, club_links)
            all_organizations.extend(organizations)
            
            await browser.close()
    
        logger.info(f"Total sports clubs scraped: {len(all_organizations)}")
        return all_organizations

    async def process_clubs_concurrent(self, browser, club_links: List[str]) -> List[Organization]:
        """Process multiple clubs concurrently"""
        tasks = [self.scrape_single_sport(browser, link) for link in club_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        organizations = []
        
        # Log any exceptions with the actual link
        for i, (result, link) in enumerate(zip(results, club_links)):
            if isinstance(result, Organization):
                organizations.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Error processing {link}: {result}")
        
        return organizations

    async def scrape_single_sport(self, browser, club_link: str) -> Organization:
        """Scrape individual sports club page"""
        page = await browser.new_page()
        try:
            await page.goto(club_link)
            
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

            organization = await self.process_with_llm(all_text, links, club_link)
            return organization
        
        finally:
            await page.close()
    
    async def process_with_llm(self, all_text: str, links: Dict[str, str], club_link: str) -> Organization:
        """Process the text and links with LLM"""
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Get relevant fields from Organization model
        prompt = f"""
Extract sports club information and return JSON with these fields:
- name: string (club name)
- description: string (main description/purpose) 
- social_media: object with keys like "instagram", "facebook", "email" mapping to arrays of URLs
- meeting_info: object with schedule/location info, or null
- membership_info: string about fees/how to join, or null

Example output:
{{
    "name": "Wrestling Club",
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

Return valid JSON only.
"""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Parse response
        extracted = json.loads(response.choices[0].message.content)
        
        # Create Organization directly
        return Organization(
            name=extracted.get('name', 'Unknown Club'),
            description=extracted.get('description'),
            social_media=extracted.get('social_media', {}),
            meeting_info=extracted.get('meeting_info'),
            membership_info=extracted.get('membership_info'),
            org_type="sports",
            is_active=True,
            last_active="Fall 2025",
            source_url=club_link,
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
