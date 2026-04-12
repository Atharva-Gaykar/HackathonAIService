from app.state.state import ComplaintState
from app.database.connection import Complaint, ComplaintUser, get_session
from typing import Literal
from sqlalchemy.orm import Session
from app.vectordatabase.pinecone import matching_retriever,retriever
from app.ai_agents.agents import complaint_classifier_agent
from app.utils.utils import *

# Assuming these are available in your global environment or config
# from config import matching_retriever, get_session

def classify_complaint_node(state: ComplaintState):
    """
    Invokes the LLM to classify the complaint department.
    FIX: result is already the ComplaintClassificationResponse object.
    """
    complaint_description = state.get("complaint_description", "")
    
    # Invoke the agent configured with .with_structured_output(ComplaintClassificationResponse)
    # result is the object itself, not a dict with "parsed"
    parsed_result = complaint_classifier_agent.invoke(complaint_description)

    # Access attributes directly from the Pydantic object
    return {
        "department": parsed_result.department.value,
    }

#----------------------------------------------------------------------------------------------------------------

def group_duplicate_complaints_node(state: ComplaintState):

    complaint_text = state.get("complaint_description", "")
    latitude = state.get("latitude", None)
    longitude = state.get("longitude", None)
    department = state.get("department", None)
    current_user_id = state.get("user_id", None)

    db_session = get_session()
    
    is_duplicate, db_id, frequency, similarity = match_complaints(db_session, complaint_text, latitude, longitude, department, current_user_id,matching_retriever)

    
    
    return {"is_duplicate": is_duplicate, "db_id": db_id, "frequency": frequency, "similarity": similarity}

def router(state: ComplaintState) -> Literal["store_data", "END"]:
    """
    Directs the workflow. If frequency is 0, it means no duplicate was found 
    in the matching node, so we proceed to store it as a new complaint.
    """
    frequency = state.get("frequency", 0)
    
    if frequency == 0:
        return "store_data"
    else:
        # If frequency > 0, it was a duplicate and the DB update 
        # happened inside the match_complaints node already.
        return "END"



def store_data_node(state: ComplaintState):
    """
    1. Persists the new unique complaint to PostgreSQL.
    2. Uses the matching_retriever to add the text and metadata to the Vector DB.
    """
    # 1. Extract state data
    title = state.get("complaint_title", "")
    description = state.get("complaint_description", "")
    full_text = f"{title}: {description}"
    
    lat = state.get("latitude")
    lng = state.get("longitude")
    dept = state.get("department")
    urgency = state.get("urgency_level")
    priority = state.get("priority", 0)
    user_id = state.get("user_id")
    
    # 2. Get DB Session
    db_session = get_session()

    try:
        # --- PART A: SQL PERSISTENCE ---
        # Create new Complaint record
        new_complaint = Complaint(
            page_content=full_text,
            frequency=1,
            latitude=lat,
            longitude=lng,
            department=dept,
            urgency_level=urgency,
            priority_score=float(priority)
        )
        
        db_session.add(new_complaint)
        db_session.flush() # Flushes to DB to generate the primary key (id)
        
        new_db_id = new_complaint.id
        
        # Link the reporting user
        user_link = ComplaintUser(
            complaint_id=new_db_id,
            user_id=user_id
        )
        db_session.add(user_link)
        db_session.commit()

        # --- PART B: VECTOR DB PERSISTENCE ---
        # Strictly using matching_retriever.add_texts as requested
        matching_retriever.add_texts(
            texts=[full_text],
            metadatas=[{
                "db_id": new_db_id,
                "context": full_text,
                "department": dept,
                "urgency_level": urgency,
                "latitude": lat,
                "longitude": lng,
                "frequency": 1
            }]
        )

        print(f"Successfully stored new complaint. SQL ID: {new_db_id}")
        
        # Update state with the new DB ID
        return {"db_id": new_db_id, "frequency": 1}

    except Exception as e:
        db_session.rollback()
        print(f"Error in store_data_node: {e}")
        return {"db_id": None}
    finally:
        db_session.close()


#--------------------------------------------------------

def calculate_priority_node(state: ComplaintState):
    """
    LangGraph node to calculate the priority score (0-10) and urgency label.
    """
    # 1. Extract data from state
    complaint_title = state.get("complaint_title", "")
    complaint_desc = state.get("complaint_description", "")
    department = state.get("department", "General")
    frequency = state.get("frequency", 1)
    db_id = state.get("db_id")
    

    # 2. Get DB Session
    db_session = get_session()

    # 3. Handle Duplicate vs New
    if db_id and frequency > 1:
        # If it's an existing complaint, we might want to use the original content 
        # from the DB for the calculation or stick with the new description.
        # Here we fetch the record to ensure we have the latest SQL frequency.
        complaint_record = db_session.query(Complaint).filter(Complaint.id == db_id).first()
        if complaint_record:
            frequency = complaint_record.frequency
            # You could also use complaint_record.page_content here if preferred

    # 4. Calculate Priority
    calc_results = priority_calculator(complaint_desc, department, frequency, retriever)
    
    # 5. Return updates for the Graph State
    return {
        "priority_score": calc_results["final_score"],
        "urgency_level": calc_results["winning_label"]
    }