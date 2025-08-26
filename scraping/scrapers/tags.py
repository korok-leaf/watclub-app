import asyncio
import argparse
import json
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

TAGS = [
    # Academic
    "Academic",
    "Science", 
    "Math",
    
    # Tech
    "Software",
    "AI",
    "Robotics",
    "Hardware",
    
    # Business
    "Business",
    "Finance",
    "Consulting",
    "Entrepreneurship",
    
    # Environment & Health
    "Sustainability",
    "Wellness",
    "Mental Health",
    
    # Sports & Recreation
    "Sports",
    "Recreation",
    "Outdoors",
    
    # Arts & Media
    "Arts",
    "Music",
    "Dance",
    "Theatre",
    "Media",
    
    # Gaming
    "Gaming",
    "Esports",
    "Boardgames",
    
    # Community & Culture
    "Volunteer",
    "Advocacy",
    "Cultural",
    "LGBTQ",
    "Leadership",
]

def save_data(type_name, clubs):
    data_dir = Path(f"data/{type_name}")
    output = {
        "scraper": type_name,
        "scraped_at": datetime.now().isoformat(),
        "count": len(clubs),
        "data": clubs
    }
    
    with open(data_dir / f"{type_name}_data.json", 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
async def tag_club(client, club):
    prompt = f"""
Assign 1-3 tags to this University of Waterloo club.
Allowed tags: {', '.join(TAGS)}

Guidelines:
- Focus on the PRIMARY purpose and core activities
- Consider what members actually DO in the club
- Choose tags that best represent the club's main function
- Avoid tags that only loosely relate to secondary aspects

Club: {json.dumps(club)}

Return JSON only: {{"tags": ["Tag1", "Tag2"]}}
"""
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    try:
        content = response.choices[0].message.content
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        return json.loads(content).get("tags", [])
    except:
        return []

async def process_type(type_name):
    logger.info(f"Processing {type_name}")
    data_file = Path(f"data/{type_name}/{type_name}_data.json")
    
    if not data_file.exists():
        print(f"No data for {type_name}")
        return
    
    with open(data_file) as f:
        data = json.load(f)
    
    clubs = data["data"]
    client = AsyncOpenAI()
    
    async def add_tags(club):
        club["tags"] = await tag_club(client, club)
    
    await asyncio.gather(*[add_tags(club) for club in clubs])
    
    save_data(type_name, clubs)
    print(f"Tagged {len(clubs)} {type_name} clubs")

async def main(types):
    await asyncio.gather(*[process_type(t) for t in types])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--types", nargs="+", choices=["wusa", "design", "faculty"], 
                       default=["wusa", "design", "faculty"])
    args = parser.parse_args()
    
    asyncio.run(main(args.types))


