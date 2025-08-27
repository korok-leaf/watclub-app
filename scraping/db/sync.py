# watclub-app/scraping/db/sync.py

import asyncio
import json
from pathlib import Path
from typing import List, Dict
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class SupabaseSync:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.client: Client = create_client(url, key)
    
    async def upsert_clubs(self, clubs: List[Dict], org_type: str):
        """Upsert clubs - insert new or update existing based on unique constraint"""
        # Add org_type to each club if not present
        for club in clubs:
            club["org_type"] = org_type
        
        # Supabase upsert handles insert/update automatically
        # Assumes you have unique constraint on (name, org_type)
        response = self.client.table("clubs").upsert(
            clubs,
            on_conflict="name,org_type"  # Update if name+org_type exists
        ).execute()
        
        logger.info(f"Upserted {len(clubs)} {org_type} clubs")
        return response
    
    async def sync_type(self, type_name: str):
        """Load JSON and sync to Supabase"""
        data_file = Path(f"data/{type_name}/{type_name}_data.json")

        with open(data_file, encoding='utf-8') as f:
            data = json.load(f)
        
        clubs = data["data"]
        await self.upsert_clubs(clubs, type_name)
    
    async def sync_all(self, types: List[str]):
        """Sync all types concurrently"""
        tasks = [self.sync_type(t) for t in types]
        await asyncio.gather(*tasks)

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--types", nargs="+", 
                       choices=["wusa", "design", "faculty", "sports"],
                       default=["wusa", "design", "faculty", "sports"])
    args = parser.parse_args()
    
    sync = SupabaseSync()
    await sync.sync_all(args.types)

if __name__ == "__main__":
    asyncio.run(main())