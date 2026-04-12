from typing import Any, Dict, List, Optional, Tuple,TypedDict,Literal,Annotated,Sequence
import os
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.tools import Tool
from langgraph.graph import StateGraph,END,START
from langgraph.types import interrupt  
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.agents.middleware import ToolCallLimitMiddleware
import uuid
import json



class ComplaintState(TypedDict):
    """
    Represents the state of a complaint within the LangGraph workflow.
    This state tracks the data from initial user input through classification 
    and eventual database persistence.
    """
    user_id: int
    urgency_level:Literal["Low", "Medium", "High"]
    complaint_title: str
    complaint_description: str
    department: str  # e.g., "Water & Sewage"
    urgency_level: str # e.g., "High"
    latitude: float
    priority_score: int
    similarity:Optional[float]
    longitude: float
    db_id: Optional[int] # The primary key from the SQL database (assigned after matching/creation)
    frequency: int # Number of times this complaint has been reported in this cluste