import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
# Importing internal modules
from app.core.config import settings
from app.graph import graph # The compiled LangGraph instance

app = FastAPI(title=settings.PROJECT_NAME)

# 1. Incoming Request Body (MERN Style)
class MernComplaintRequest(BaseModel):
    title: str
    description: str
    timeOfOccurrence: str
    address: str
    city: str
    state: str
    lat: float
    lng: float
    # We assume user_id is passed in headers or as part of the body
    # For this implementation, we'll include it in the body for simplicity
    user_id: int

# 2. Final Filtered Response Body
class ComplaintProcessingResponse(BaseModel):
    freq: int
    department: str
    priority_score: float
    urgency_level: str

@app.get("/")
async def health_check():
    return {"status": "CitySync AI is running", "project": settings.PROJECT_NAME}

@app.post("/process-complaint", response_model=ComplaintProcessingResponse)
async def process_complaint(request: MernComplaintRequest):
    """
    Receives a MERN-style request, maps to internal state, 
    executes the LangGraph, and returns computed metrics.
    """
    try:
        # 1. Map MERN Request to Internal ComplaintState
        initial_state = {
            "user_id": request.user_id,
            "complaint_title": request.title,
            "complaint_description": request.description,
            "latitude": request.lat,
            "longitude": request.lng,
            # Defaults for fields initialized later in the graph
            "department": "",
            "urgency_level": "Low",
            "priority": 0.0,
            "db_id": None,
            "frequency": 1,
            "is_duplicate": False
        }

        # 2. Invoke the LangGraph Workflow
        # This runs: classify -> group_duplicates -> calculate_priority
        final_state = graph.invoke(initial_state)

        # 3. Extract and return only the required computed parts
        return ComplaintProcessingResponse(
            freq=final_state.get("frequency", 1),
            department=final_state.get("department", "Unassigned"),
            priority_score=round(final_state.get("priority", 0.0), 2),
            urgency_level=final_state.get("urgency_level", "Low")
        )

    except Exception as e:
        # Standard error handling for the API
        raise HTTPException(status_code=500, detail=f"Workflow Execution Error: {str(e)}")

# if __name__ == "__main__":
#     import uvicorn
#     # In HF Spaces, the port is usually 7860
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)