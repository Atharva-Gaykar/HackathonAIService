from pydantic import BaseModel, Field
from enum import Enum
from typing import List

class ComplaintCategory(str, Enum):
    SANITATION = "Sanitation & Cleanliness"
    WATER_SEWAGE = "Water & Sewage"
    ROADS_INFRA = "Roads & Infrastructure"
    BUILDINGS_PLANNING = "Buildings & Planning"
    PUBLIC_HEALTH = "Public Health & Safety"
    PARKS_REC = "Parks & Recreation"
    PUBLIC_SAFETY_SECURITY = "Public Safety & Security"
    UTILITIES_SERVICES = "Utilities & Services"

# Token-efficient descriptions to guide the LLM
CATEGORY_DESCRIPTIONS = {
    ComplaintCategory.SANITATION: "Garbage, littering, sweeping, overflowing bins, public cleanliness.",
    ComplaintCategory.WATER_SEWAGE: "Water supply, leaks, drainage, sewage overflow, manholes.",
    ComplaintCategory.ROADS_INFRA: "Potholes, roads, bridges, footpaths, streetlights, signals.",
    ComplaintCategory.BUILDINGS_PLANNING: "Illegal construction, unsafe buildings, encroachments, planning violations.",
    ComplaintCategory.PUBLIC_HEALTH: "Mosquitoes, waste hazards, stray animals, disease risks.",
    ComplaintCategory.PARKS_REC: "Parks, gardens, playgrounds, broken equipment, overgrowth.",
    ComplaintCategory.PUBLIC_SAFETY_SECURITY: "CCTV, fire safety, security issues, police patrols.",
    ComplaintCategory.UTILITIES_SERVICES: "Electricity, transformers, live wires, utility faults."
}

class ComplaintClassificationResponse(BaseModel):
    """
    Simplified classification model for the LLM.
    Just department selection and the reasoning.
    """
    department: ComplaintCategory = Field(..., description="The municipal department responsible for the issue.")
    reasoning: str = Field(..., description="Short explanation for why this complaint fits the selected department.")
