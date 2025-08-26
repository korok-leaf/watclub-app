import asyncio
import json
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

class BaseScraper(ABC):
    def __init__(self, name: str):
        self.name = name
        self.data_dir = Path(f"data/{name}")
        self.data_dir.mkdir(exist_ok=True)
    
    @abstractmethod
    async def scrape(self) -> list:
        """Implement in each scraper - return list of organizations"""
        pass
    
    def save_data(self, data: list) -> None:
        """Save to JSON file with timestamp"""
        filename = self.data_dir / f"{self.name}_data.json"
        
        serializable_data = []
        for item in data:
            if hasattr(item, 'to_dict'):
                serializable_data.append(item.to_dict())
            else:
                serializable_data.append(item)
        
        output = {
            "scraper": self.name,
            "scraped_at": datetime.now().isoformat(),
            "count": len(data),
            "data": serializable_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False, default=str)
        print(f"Saved {len(data)} items to {filename}")
    
    async def run(self) -> list:
        """Main method to run scraper"""
        print(f"Starting {self.name} scraper...")
        
        try:
            data = await self.scrape()
            self.save_data(data)
            print(f"{self.name} complete: {len(data)} items")
            return data
        except Exception as e:
            print(f"{self.name} failed: {e}")
            return []