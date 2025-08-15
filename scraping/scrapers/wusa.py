"""WUSA clubs scraper with concurrent processing."""
import asyncio
import aiohttp
from typing import List
from bs4 import BeautifulSoup
import logging

from .base import BaseScraper
from models.organization import Organization

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WUSAScraper(BaseScraper):
    def __init__(self):
        super().__init__("wusa")
        self.base_url = "https://clubs.wusa.ca"
    
    async def scrape(self) -> List[Organization]:
        """Main scraping: loop through pages, process clubs concurrently"""
        all_organizations = []
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
                page_orgs = await self.process_clubs_concurrent(session, club_links)
                all_organizations.extend(page_orgs)
                
                page += 1
        
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
        
        # For now, just return a placeholder
        # TODO: implement actual scraping logic
        return Organization(
            name=f"{club_path}",
            org_type="wusa",
            description="Placeholder description",
            source_url=club_url
        )


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
            