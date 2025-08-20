"""WUSA clubs scraper with concurrent processing."""
import asyncio
import aiohttp
from typing import List, Dict
from bs4 import BeautifulSoup
import logging
from openai import AsyncOpenAI
import json
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import aiofiles
import os
from urllib.parse import urlparse
from pathlib import Path
import instaloader
import re

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

        # Scrape club images
        for org in organizations:
            if org.social_media:
                image_path = await self.scrape_club_image(session, org.name, org.social_media)
                await asyncio.sleep(5)

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
                    email=llm_result.get("email", [None])[0] if llm_result.get("email") else None,
                    website=llm_result.get("social_media", {}).get("website", [None])[0] if llm_result.get("social_media", {}).get("website") else None,
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
    }},
    "other_contacts": ["any other contact info that doesn't fit above categories"]
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
    
    async def scrape_club_image(self, session: aiohttp.ClientSession, club_name: str, social_media: dict) -> str:
        """
        Scrape club profile image using Instaloader for Instagram and Playwright for Facebook
        Returns the public URL path for the frontend
        """
        image_url = None
        
        # Try Instagram first with Instaloader
        if 'instagram' in social_media and social_media['instagram']:
            try:
                instagram_url = social_media['instagram'][-1]
                logger.info(f"Trying Instagram with Instaloader: {instagram_url}")
                
                # Extract username from Instagram URL
                username = None
                patterns = [
                    r'instagram\.com/([^/?]+)',
                    r'instagram\.com/([^/?]+)/',
                    r'@([a-zA-Z0-9_.]+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, instagram_url)
                    if match:
                        username = match.group(1).split('/')[0].split('?')[0]
                        break
                
                if username:
                    L = instaloader.Instaloader()
                    L.download_pictures = False
                    L.download_videos = False
                    L.download_video_thumbnails = False
                    L.download_geotags = False
                    L.download_comments = False
                    L.save_metadata = False
                    
                    try:
                        profile = instaloader.Profile.from_username(L.context, username)
                        image_url = profile.profile_pic_url
                        logger.info(f"Found Instagram image with Instaloader: {image_url[:100]}...")
                    except instaloader.exceptions.ProfileNotExistsException:
                        logger.warning(f"Instagram profile {username} does not exist")
                    except instaloader.exceptions.ConnectionException:
                        logger.error(f"Instagram connection error for {username}")
                    except Exception as e:
                        logger.error(f"Instaloader error for {username}: {e}")
                
            except Exception as e:
                logger.error(f"Instagram scraping failed for {club_name}: {e}")

        # Try Facebook if Instagram fails (keep Playwright for Facebook)
        if not image_url and 'facebook' in social_media and social_media['facebook']:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    
                    await page.set_extra_http_headers({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    facebook_url = social_media['facebook'][-1]
                    logger.info(f"Trying Facebook: {facebook_url}")
                    
                    await page.goto(facebook_url, wait_until='networkidle', timeout=15000)
                    await page.wait_for_timeout(3000)
                    
                    selectors = [
                        'img[data-imgperflogname*="profilePhoto"]',
                        '[data-pagelet="ProfilePhoto"] img',
                        '[data-pagelet="ProfilePhoto"] image', 
                        'svg image[style*="profile"]',
                        'img[alt*="profile picture"]',
                        '[role="img"][style*="profile"] image',
                        'image[data-imgperflogname*="profile"]'
                    ]
                    
                    for selector in selectors:
                        img_element = await page.query_selector(selector)
                        if img_element:
                            img_src = await img_element.get_attribute('src')
                            if img_src:
                                image_url = img_src
                                logger.info(f"Found Facebook image: {image_url[:100]}...")
                                break
                    
                    await browser.close()
                    
            except Exception as e:
                logger.error(f"Facebook scraping failed for {club_name}: {e}")

        if image_url:
            return await self.download_and_save_club_image(session, image_url, club_name)
        else:
            logger.warning(f"No profile image found for {club_name}")
            return None
    
    async def download_and_save_club_image(self, session: aiohttp.ClientSession, image_url: str, club_name: str) -> str:
        """Download and save club image to watclub/watclub/public/wusa/"""
        try:

            safe_name = "".join(c if c.isalnum() or c in ('-', '_', ' ') else '' for c in club_name)
            safe_name = safe_name.replace(' ', '-').lower().strip('-')
            
            # Use pathlib to find the project root and create the path
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            image_dir = project_root / "watclub" / "public" / "wusa"
            image_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine file extension from image URL
            parsed_url = urlparse(image_url)
            ext = os.path.splitext(parsed_url.path)[1]
            
            # Default to .jpg if no extension or unknown extension
            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ext = '.jpg'
            
            filename = f"{safe_name}{ext}"
            filepath = image_dir / filename
            
            # Download the image
            async with session.get(image_url) as response:
                if response.status == 200:
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    logger.info(f"Saved image for {club_name}: {filename}")
                    return f"/wusa/{filename}"
                else:
                    logger.error(f"Failed to download image: HTTP {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error downloading image for {club_name}: {e}")
            return None
                
                
                
                

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
            