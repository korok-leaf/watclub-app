from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OrgType(str, Enum):
    """Types of student organizations at Waterloo."""
    WUSA = "wusa"
    FACULTY = "faculty" 
    DESIGN_TEAM = "design_team"
    ATHLETICS = "athletics"
    ADVOCACY = "advocacy"
    ENTREPRENEURSHIP = "entrepreneurship"
    MEDIA = "media"


class Organization(BaseModel):
    """Model for a University of Waterloo student organization."""
    
    # Core fields
    name: str = Field(..., description="Organization name")
    org_type: OrgType = Field(..., description="Type of organization")
    description: Optional[str] = Field(None, description="Organization description")
    
    # Contact info
    social_media: Dict[str, list[str]] = Field(
        default_factory=dict, 
        description="Social media links (instagram: [url1, url2, ...], facebook: [url1, url2, ...])"
    )
    
    # Organization details
    faculty: Optional[str] = Field(None, description="Associated faculty")
    category: Optional[str] = Field(None, description="Category within org type")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    
    # Activity info
    meeting_info: Optional[str] = Field(None, description="Meeting details")
    membership_info: Optional[str] = Field(None, description="How to join")
    is_active: bool = Field(True, description="Currently active")
    last_active: str = Field(..., description="Last active date")
    
    # Scraping metadata
    source_url: str = Field(..., description="Where data was scraped from")
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.dict(exclude_none=True)
    
    @classmethod
    def create_wusa_club(cls, name: str, **kwargs) -> 'Organization':
        """Helper to create WUSA club."""
        return cls(
            name=name,
            org_type=OrgType.WUSA,
            **kwargs
        )
    
    @classmethod
    def create_faculty_org(cls, name: str, faculty: str, **kwargs) -> 'Organization':
        """Helper to create faculty organization."""
        return cls(
            name=name,
            org_type=OrgType.FACULTY,
            faculty=faculty,
            source_url=f"https://uwaterloo.ca/{faculty.lower()}",
            **kwargs
        )
    
    @classmethod
    def create_design_team(cls, name: str, **kwargs) -> 'Organization':
        """Helper to create design team."""
        return cls(
            name=name,
            org_type=OrgType.DESIGN_TEAM,
            source_url="https://uwaterloo.ca/future-students/student-life",
            **kwargs
        )

