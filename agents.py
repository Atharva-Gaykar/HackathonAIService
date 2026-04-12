from langchain_groq import ChatGroq

from langchain_groq import ChatGroq
from schemas import ComplaintClassificationResponse



base_model=ChatGroq(

    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.1,
  
)
complaint_classifier_agent=base_model.with_structured_output(ComplaintClassificationResponse,method="json_schema")