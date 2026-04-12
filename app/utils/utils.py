from sqlalchemy import and_
from app.database.connection import Complaint, ComplaintUser
import numpy as np


def handle_duplicate_complaint(db_session, db_id, current_user_id):
    """
    Helper function to update an existing complaint's frequency and 
    link a new user if they haven't already reported this specific issue.
    Returns the updated frequency count.
    """
    try:
        # Fetch the existing complaint from SQL
        complaint = db_session.query(Complaint).filter(Complaint.id == db_id).first()
        
        if not complaint:
            print(f"Error: Complaint ID {db_id} not found in SQL.")
            return None

        # 1. Update global frequency
        complaint.frequency += 1
        current_freq = complaint.frequency
        
        # 2. Add user if not already linked (prevents duplicate entries for the same user)
        user_exists = db_session.query(ComplaintUser).filter(
            and_(
                ComplaintUser.complaint_id == db_id,
                ComplaintUser.user_id == current_user_id
            )
        ).first()

        if not user_exists:
            db_session.add(ComplaintUser(complaint_id=db_id, user_id=current_user_id))
        
        # Commit changes to persist frequency and the user link
        db_session.commit()
        return current_freq
        
    except Exception as sql_err:
        db_session.rollback()
        print(f"SQL Update Error in handle_duplicate_complaint: {sql_err}")
        raise sql_err

#----------------------------------------------------------------------------
def match_complaints(db_session, complaint_text, latitude, longitude, department, current_user_id, retriever):
    """
    Returns: (is_duplicate, db_id, frequency, similarity)
    """

    lat_filter = round(float(latitude), 3)
    lng_filter = round(float(longitude), 3)

    try:
        results = retriever.invoke(
            complaint_text,
            filter={
                "department": department,
                "latitude": lat_filter,
                "longitude": lng_filter
            }
        )
    except Exception as e:
        print(f"Retrieval error: {e}")
        return False, None, 0, 0.0   # 

    if not results:
        return False, None, 0, 0.0   #

    # Top match
    top_match = results[0]
    similarity_score = top_match.metadata.get("score", 0.0)
    db_id = top_match.metadata.get("db_id")

    # Duplicate case
    if similarity_score >= 0.80 and db_id:
        try:
            updated_freq = handle_duplicate_complaint(db_session, db_id, current_user_id)
            if updated_freq is not None:
                return True, db_id, updated_freq, similarity_score   
        except Exception:
            return False, None, 0, similarity_score   # already correct

    # Not duplicate
    return False, None, 0, similarity_score


#------------------------------------------------------------------------------------

def priority_calculator(complaint_text: str, department: str, frequency: int, retriever):
    """
    Core logic to calculate priority based on semantic similarity to 
    departmental urgency benchmarks and frequency volume.
    """
    sub_classes = ["High", "Medium", "Low"]
    base_weights = {"High": 6.0, "Medium": 3.0, "Low": 1.0}

    winning_label = "Low"
    max_sim = 0.0

    # Iterate through classes to find where this complaint fits best semantically
    for subclass in sub_classes:
        try:
            results = retriever.invoke(
                complaint_text,
                filter={
                    "department": department,
                    "urgency_level": subclass
                }
            )

            print(len(results))
            
            if results:
                # LangChain Document metadata usually holds the score
                # This depends on your retriever configuration (e.g., Pinecone/similarity_search_with_score)
                sim = results[0].metadata['score']
            else:
                sim = 0.0
        except Exception as e:
            print(f"Retriever error in subclass {subclass}: {e}")
            sim = 0.0

        if sim > max_sim:
            max_sim = sim
            winning_label = subclass

    # --- The Formula ---
    # 1. Start with the base weight of the semantic match
    base = base_weights[winning_label]
    
    # 2. Add a boost based on similarity strength (max +2.0)
    similarity_boost = max_sim * 2.0
    
    # 3. Add a log-based frequency boost (diminishing returns)
    # log1p handles frequency=1 (log(2) = ~0.69)
    if frequency > 1:
        frequency_boost = np.log1p(frequency)
    else:
        frequency_boost = 0.0

    # 4. Sum and Clamp
    final_score = base + similarity_boost + frequency_boost
    final_score = min(final_score, 10.0)

    return {
        "final_score": round(float(final_score), 2),
        "winning_label": winning_label,
        "similarity": round(float(max_sim), 3),
    }
#------------------------------------------------------------------------------------

