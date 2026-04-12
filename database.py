from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os
from dotenv import load_dotenv

# This loads the variables from your .env file into the system environment
load_dotenv()

# Access them using os.getenv()
DB_URL= os.getenv("DB_URL")

Base = declarative_base()



# This table handles the "list of user ids" by linking users to complaints
class ComplaintUser(Base):
    __tablename__ = 'complaint_users'
    
    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey('complaints.id'))
    user_id = Column(Integer, nullable=False)

class Complaint(Base):
    __tablename__ = 'complaints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    page_content = Column(String, nullable=False)
    frequency = Column(Integer, default=1)
    
    # Location stored as high-precision floats
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    priority_score = Column(Float, default=0.0)
    department = Column(String, nullable=False)
    urgency_level = Column(String, nullable=False)

    # Relationship to get the list of users easily
    # Access via: complaint_obj.users
    users = relationship("ComplaintUser", backref="complaint", cascade="all, delete-orphan")

# --- Table Creation Logic ---


engine = create_engine(
    DB_URL, 
    echo=False, 
    pool_pre_ping=True, 
    pool_recycle=1800
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_session() -> Session:
    return SessionLocal()