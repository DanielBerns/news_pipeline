import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables from .env file (optional, good practice)
load_dotenv()

# --- Database Configuration ---

# Get database URL from environment variable
# Example for PostgreSQL: "postgresql://user:password@host:port/database"
# Example for SQLite (dev): "sqlite:///./local_dev.db"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local_dev.db")

# For SQLite, connect_args is needed to allow multithreading if using FastAPI's async routes
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# --- SQLAlchemy Engine Setup ---

# Create the SQLAlchemy engine
# pool_pre_ping=True helps handle connections that may have timed out
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    # echo=True # Uncomment for debugging SQL statements
)

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
