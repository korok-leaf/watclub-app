"""Sports clubs scraper for Warrior Recreation clubs."""
import asyncio
import aiohttp
from typing import List
from bs4 import BeautifulSoup
import logging
from dotenv import load_dotenv
from playwright.async_api import async_playwright

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
        
        organizations = [org for org in results if isinstance(org, Organization)]
        
        # Log any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing club {i}: {result}")
        
        return organizations

    async def scrape_single_sport(self, browser, club_link: str) -> Organization:
        """Scrape individual sports club page"""
        page = await browser.new_page()
        try:
            await page.goto(club_link)
            # Wait for content, scrape, etc.
            # ...
        finally:
            await page.close()


async def main():
    """Test the Sports scraper"""
    logger.info("Starting Sports scraper test")
    
    scraper = SportsScraper()
    organizations = await scraper.run()
    
    logger.info(f"Test complete: {len(organizations)} organizations scraped")


if __name__ == "__main__":
    asyncio.run(main())
