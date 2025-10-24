import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables from .env file (optional, good practice)
load_dotenv()

# --- Database Configuration ---

# Read from environment, with a fallback for safety (though not recommended for prod)
DEFAULT_DB_URL = "postgresql+psycopg2://news_user:mysecretpassword@localhost:5432/news_pipeline"
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)

# --- SQLAlchemy Engine Setup ---

# Create the SQLAlchemy engine
# pool_pre_ping=True helps handle connections that may have timed out
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# --- SQLAlchemy Session Setup ---

# Create a configured "Session" class
# autocommit=False and autoflush=False are standard settings for web applications
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Dependency for FastAPI ---

def get_db() -> Session:
    """
    Dependency function for FastAPI routes to get a database session.
    Ensures the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Optional: Function to Create Tables (for initial setup without Alembic, or testing) ---
# It's generally better to use Alembic migrations ('make db-upgrade') for schema management.
# from app.models import Base # Assuming your models are in app.models

# def create_tables():
#     """Creates all tables defined in the Base metadata."""
#     Base.metadata.create_all(bind=engine)

# if __name__ == "__main__":
#     print(f"Connecting to database: {DATABASE_URL}")
#     # You could uncomment the line below to create tables directly
#     # Be careful using this if you manage migrations with Alembic
#     # create_tables()
#     print("Database engine and session configured.")
