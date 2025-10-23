from datetime import datetime
import uuid
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Assuming your other modules are structured like this
from . import crud, models, schemas
from .database import SessionLocal, engine, get_db


# --- FastAPI App Initialization ---
app = FastAPI(
    title="News Pipeline API",
    description="API for ingesting, processing, and analyzing news articles.",
    version="0.1.0",  # Corresponds to pyproject.toml version
)

# --- Basic Root Endpoint ---


@app.get("/")
async def read_root():
    """Provides a simple welcome message for the API root."""
    return {"message": "Welcome to the News Pipeline API"}


# --- API Endpoints (as defined in Increment 1.2) ---
# These endpoints provide basic CRUD operations for testing core functionality.

# --- User Endpoints ---


@app.post(
    "/api/users/",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Creates a new user.
    - **username**: Unique username for the user.
    - **password**: User's password (will be hashed).
    - **role**: Must be 'admin' or 'data_analyst'.
    - **is_active**: Defaults to True.
    """
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.get("/api/users/", response_model=List[schemas.User], tags=["Users"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves a list of users. Supports pagination via `skip` and `limit`.
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/api/users/{user_id}", response_model=schemas.User, tags=["Users"])
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves a specific user by their UUID.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# --- Source Endpoints ---


@app.post(
    "/api/sources/",
    response_model=schemas.Source,
    status_code=status.HTTP_201_CREATED,
    tags=["Sources"],
)
def create_source(source: schemas.SourceCreate, db: Session = Depends(get_db)):
    """
    Creates a new data source.
    - **name**: Descriptive name for the source.
    - **type**: Type of source ('website', 'rss', 'local', 's3').
    - **location**: URL or path for the source.
    - **config**: Optional JSON object for source-specific settings.
    - **is_active**: Defaults to True.
    """
    # Potential future validation: check if source location already exists?
    return crud.create_source(db=db, source=source)


@app.get("/api/sources/", response_model=List[schemas.Source], tags=["Sources"])
def read_sources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves a list of sources. Supports pagination.
    """
    sources = crud.get_sources(db, skip=skip, limit=limit)
    return sources


@app.get("/api/sources/{source_id}", response_model=schemas.Source, tags=["Sources"])
def read_source(source_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves a specific source by its UUID.
    """
    db_source = crud.get_source(db, source_id=source_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return db_source


# --- Article Endpoints ---


@app.post(
    "/api/articles/",
    response_model=schemas.Article,
    status_code=status.HTTP_201_CREATED,
    tags=["Articles"],
)
def create_article(article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    """
    Creates a new article (mainly for testing the ingestion pipeline stages).
    - **source_id**: Optional UUID of the source this article came from.
    - **title**: Article title.
    - **content_text**: Main text content.
    - **original_url**: URL where the article originated.
    - **source_format**: Format of the original source (e.g., 'pdf', 'html').
    - **metadata**: Optional JSON object for extra info (like CSV row index).
    """
    # Potential future validation: Check checksum if implemented to prevent duplicates?
    return crud.create_article(db=db, article=article)


@app.get("/api/articles/", response_model=List[schemas.Article], tags=["Articles"])
def read_articles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves a list of articles. Supports pagination.
    """
    articles = crud.get_articles(db, skip=skip, limit=limit)
    return articles


@app.get(
    "/api/articles/{article_id}", response_model=schemas.Article, tags=["Articles"]
)
def read_article(article_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves a specific article by its UUID.
    """
    db_article = crud.get_article(db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return db_article


# --- Authentication Stub Endpoint (as per plan 1.2) ---
# This is a very basic placeholder and should be replaced with a proper
# security implementation (OAuth2 with password flow, JWTs, or sessions) later.


@app.post("/api/login/", tags=["Authentication"])
async def login_stub(
    username: str = "user", password: str = "pass", db: Session = Depends(get_db)
):
    """
    Placeholder login endpoint. Returns a simple token/message.
    **Note:** This is insecure and only for initial testing.
    """
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    # Add actual password verification here using bcrypt or argon2
    # if not verify_password(password, user.hashed_password):
    #     raise HTTPException(status_code=400, detail="Incorrect username or password")

    # In a real app, generate and return a JWT or session cookie here
    return {"message": f"Login successful for {username}. Token placeholder."}


# --- Optional: Include routers from app/api/ ---
# If you split endpoints into separate files (recommended)
# from .api import users, sources, articles # Example imports
# app.include_router(users.router)
# app.include_router(sources.router)
# app.include_router(articles.router)
