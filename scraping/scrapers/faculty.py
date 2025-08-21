"""Faculty clubs scraper with social media search using Google Custom Search."""
import asyncio
import aiohttp
import aiofiles
import json
import os
from typing import List, Dict
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
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
                    
                    # Extract all images
                    images = soup.find_all('img')
                    image_data = []
                    for img in images:
                        img_src = img.get('src')
                        if img_src:
                            # Convert relative URLs to absolute
                            if img_src.startswith('/'):
                                img_src = urljoin(base_url, img_src)
                            elif not img_src.startswith('http'):
                                img_src = urljoin(base_url, img_src)
                            
                            image_data.append({
                                'src': img_src,
                                'alt': img.get('alt', ''),
                                'title': img.get('title', '')
                            })
                    
                    logger.info(f"Extracted {len(image_data)} images from {faculty_name}")
                    
                    # Use reasoning model to parse content
                    clubs_data = await self.parse_content_with_reasoning_llm(
                        faculty_name, page_text, image_data
                    )
                    
                    # Process each club
                    for club_data in clubs_data:
                        try:
                            # Download club image if available
                            image_path = None
                            if club_data.get('image_url'):
                                image_path = await self.download_club_image(
                                    session, club_data['image_url'], club_data['name'], faculty_name
                                )

                            if not image_path:
                                logger.info(f"No LLM image for {club_data['name']}, searching Google...")
                                image_path = await self.search_club_image_with_google(session, club_data['name'], faculty_name)
                            
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
    
    async def search_image_with_playwright(self, club_name: str, faculty_name: str):
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Search Google
            await page.goto("https://google.com")
            await page.fill('input[name="q"]', f"{club_name} University of Waterloo logo")
            await page.press('input[name="q"]', "Enter")
            
            # Click Images tab
            await page.click('a[href*="tbm=isch"]')
            
            # Get first image
            first_img = await page.query_selector('img[data-src]')
            img_url = await first_img.get_attribute('data-src')
            
            await browser.close()
            return img_url

    async def extract_clubs_from_page(self, faculty_name: str, html_content: str) -> List[Dict[str, str]]:
        """Extract club names and descriptions from faculty page HTML"""
        # TODO: Parse HTML to extract club information
        # Return list of dicts with 'name' and 'description' keys
        pass
    
    async def search_club_socials(self, club_name: str, club_description: str, faculty_name: str) -> Dict[str, List[str]]:
        pass
    
    async def verify_socials_with_llm(self, club_name: str, club_description: str, search_results: List[Dict]) -> Dict[str, List[str]]:
        pass
    
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

    async def parse_content_with_reasoning_llm(self, faculty_name: str, page_text: str, image_data: List[Dict]) -> List[Dict]:
        """Use reasoning model to parse faculty page content and extract club information"""
        
        # Format image data for LLM
        formatted_images = []
        for i, img in enumerate(image_data):
            formatted_images.append({
                'index': i,
                'url': img['src'],
                'alt_text': img['alt'],
                'title': img['title']
            })
        
        prompt = f"""
You are tasked with analyzing a {faculty_name} faculty page from University of Waterloo to extract student club information.

Faculty: {faculty_name}
Page Content:
{page_text}

Available Images:
{json.dumps(formatted_images, indent=2)}

Please carefully analyze this content and extract ALL student clubs/organizations mentioned. For each club, provide:

1. Club name (exact name as mentioned)
2. Description (clean, comprehensive description)
3. Social media links (if any are mentioned in the content)
4. Associated image (match club to appropriate image by index if available)

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
    }},
    "image_url": "URL from the images list above, or null if no appropriate image",
    "image_index": "Index number of the associated image, or null"
  }}
]

Important guidelines:
- Carefully separate different clubs - don't merge them
- Extract complete descriptions for each club
- Match images to clubs based on alt text, titles, or logical association
- Only include social media links that are explicitly mentioned
- Be thorough - don't miss any clubs mentioned in the content
- Use reasoning to determine which image belongs to which club
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

    async def search_club_image_with_google(self, session: aiohttp.ClientSession, club_name: str, faculty_name: str) -> str:
        """Search for club image using SerpAPI and download first result"""
        try:
            # SerpAPI configuration
            serpapi_key = os.getenv("SERPAPI_KEY")
            search_query = f"{club_name} University of Waterloo logo"
            
            # SerpAPI endpoint for Google Images
            serpapi_url = "https://serpapi.com/search"
            params = {
                "engine": "google_images",
                "q": search_query,
                "api_key": serpapi_key,
                "num": 5,  # Get first 5 results
                "safe": "active"
            }
            
            logger.info(f"Searching images for '{search_query}' using SerpAPI")
            
            async with session.get(serpapi_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"SerpAPI request failed: HTTP {response.status}")
                    return None
                
                data = await response.json()
                
                # Extract image results
                images_results = data.get("images_results", [])
                
                if not images_results:
                    logger.warning(f"No images found for {club_name}")
                    return None
                
                # Try to download the first few images until one works
                for i, image_data in enumerate(images_results[:3]):  # Try first 3 images
                    try:
                        image_url = image_data.get("original")
                        if not image_url:
                            image_url = image_data.get("thumbnail")
                        
                        if image_url:
                            logger.info(f"Trying image {i+1} for {club_name}: {image_url[:100]}...")
                            
                            # Attempt to download the image
                            downloaded_path = await self.download_club_image(
                                session, image_url, club_name, faculty_name
                            )
                            
                            if downloaded_path:
                                logger.info(f"Successfully downloaded image for {club_name}")
                                return downloaded_path
                            
                    except Exception as e:
                        logger.warning(f"Failed to download image {i+1} for {club_name}: {e}")
                        continue
                
                logger.warning(f"Could not download any images for {club_name}")
                return None
                
        except Exception as e:
            logger.error(f"SerpAPI image search failed for {club_name}: {e}")
            return None

    async def download_club_image(self, session: aiohttp.ClientSession, image_url: str, club_name: str, faculty_name: str) -> str:
        """Download club image and save to watclub/public/faculty/{faculty_name}/{club_name}"""
        try:
            # Create safe filename
            safe_name = "".join(c if c.isalnum() or c in ('-', '_', ' ') else '' for c in club_name)
            safe_name = safe_name.replace(' ', '-').lower().strip('-')
            
            # Use pathlib to find the project root and create the path
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            image_dir = project_root / "watclub" / "public" / "faculty" / faculty_name
            image_dir.mkdir(parents=True, exist_ok=True)
            
            # Download the image first to get the actual content-type
            async with session.get(image_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to download image: HTTP {response.status}")
                    return None
                
                # Get extension from content-type header (most reliable)
                content_type = response.headers.get('content-type', '').lower()
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'svg' in content_type:
                    ext = '.svg'
                else:
                    ext = '.jpg'  # Default fallback
                
                filename = f"{safe_name}{ext}"
                filepath = image_dir / filename
                
                # Check if file already exists
                if filepath.exists():
                    logger.info(f"Image already exists for {club_name}: {filename}")
                    return f"/faculty/{faculty_name}/{filename}"
                
                # Save the image
                async with aiofiles.open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                logger.info(f"Saved image for {club_name}: {filename}")
                return f"/faculty/{faculty_name}/{filename}"
        
        except Exception as e:
            logger.error(f"Error downloading image for {club_name}: {e}")
            return None


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
