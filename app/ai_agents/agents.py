from langchain_groq import ChatGroq
from app.core.config import settings
from app.schemas.schemas import ComplaintClassificationResponse
import os


if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY


base_model=ChatGroq(

    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.1,
  
)
complaint_classifier_agent=base_model.with_structured_output(ComplaintClassificationResponse,method="json_schema")