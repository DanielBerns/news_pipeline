import uuid
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func

# Assuming your models and schemas are in these locations relative to crud.py
from . import models, schemas
# You'll need a way to hash passwords, assuming a utility function exists
# from app.core.security import get_password_hash # Import this when available

# --- User CRUD ---

def get_user(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    """Retrieves a single user by their ID."""
    return db.get(models.User, user_id)

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Retrieves a single user by their username."""
    statement = select(models.User).where(models.User.username == username)
    return db.execute(statement).scalar_one_or_none()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Retrieves a list of users with pagination."""
    statement = select(models.User).offset(skip).limit(limit)
    return list(db.execute(statement).scalars().all())

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Creates a new user."""
    # Replace with actual password hashing function when implemented
    # fake_hashed_password = user.password + "_hashed" # Placeholder
    # Replace placeholder with:
    # hashed_password = get_password_hash(user.password)
    hashed_password = user.password + "_hashed" # TEMPORARY PLACEHOLDER

    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Source CRUD ---

def get_source(db: Session, source_id: uuid.UUID) -> Optional[models.Source]:
    """Retrieves a single source by its ID."""
    return db.get(models.Source, source_id)

def get_sources(db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[models.Source]:
    """Retrieves a list of sources with pagination and optional active filter."""
    statement = select(models.Source)
    if is_active is not None:
        statement = statement.where(models.Source.is_active == is_active)
    statement = statement.offset(skip).limit(limit)
    return list(db.execute(statement).scalars().all())

def create_source(db: Session, source: schemas.SourceCreate) -> models.Source:
    """Creates a new source."""
    db_source = models.Source(
        name=source.name,
        type=source.type,
        location=source.location,
        config=source.config,
        is_active=source.is_active
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

# --- Article CRUD ---

def get_article(db: Session, article_id: uuid.UUID) -> Optional[models.Article]:
    """Retrieves a single article by its ID."""
    return db.get(models.Article, article_id)

def get_articles(db: Session, skip: int = 0, limit: int = 100) -> List[models.Article]:
    """Retrieves a list of articles with pagination."""
    statement = select(models.Article).offset(skip).limit(limit)
    return list(db.execute(statement).scalars().all())

def create_article(db: Session, article: schemas.ArticleCreate) -> models.Article:
    """Creates a new article. Primarily used by the ingestion pipeline."""
    db_article = models.Article(
        source_id=article.source_id,
        title=article.title,
        content_text=article.content_text,
        original_url=str(article.original_url) if article.original_url else None,
        source_format=article.source_format,
        metadata=article.metadata,
        # extraction_date is server_default
        # content_text_vector requires DB trigger or specific update logic
        # last_nlp_run_timestamp starts as NULL
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


# --- Annotation CRUD (Basic Create/Get needed later) ---

def create_annotation(db: Session, annotation: schemas.AnnotationCreate, user_id: uuid.UUID) -> models.Annotation:
    """Creates a new annotation for an article by a user."""
    db_annotation = models.Annotation(
        **annotation.model_dump(),
        user_id=user_id # Add the user ID from the authenticated context
    )
    db.add(db_annotation)
    db.commit()
    db.refresh(db_annotation)
    return db_annotation

def get_annotations_for_article(db: Session, article_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[models.Annotation]:
    """Retrieves annotations for a specific article."""
    statement = (
        select(models.Annotation)
        .where(models.Annotation.article_id == article_id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(statement).scalars().all())


# --- Named Entity / ArticleEntity CRUD (Primarily for NLP pipeline) ---
# These often involve more complex "get or create" logic

def get_or_create_named_entity(db: Session, entity: schemas.NamedEntityCreate) -> models.NamedEntity:
    """Finds an existing NamedEntity or creates a new one."""
    statement = select(models.NamedEntity).where(
        models.NamedEntity.normalized_form == entity.normalized_form,
        models.NamedEntity.entity_type == entity.entity_type,
        models.NamedEntity.language == entity.language
    )
    db_entity = db.execute(statement).scalar_one_or_none()
    if db_entity is None:
        db_entity = models.NamedEntity(**entity.model_dump())
        db.add(db_entity)
        # Commit might happen in batches in the pipeline, or here
        db.commit()
        db.refresh(db_entity)
    return db_entity

def link_article_to_entity(db: Session, article_id: uuid.UUID, entity_id: uuid.UUID, count: int = 1):
    """Creates or updates the count in the ArticleEntity association."""
    # This might use direct SQL or ORM upsert depending on dialect/preference
    # For simplicity, showing a basic add, assuming pipeline handles upsert logic if needed
    db_link = models.ArticleEntity(article_id=article_id, entity_id=entity_id, count=count)
    # A real implementation would likely use db.merge() or handle potential IntegrityErrors
    # if the link already exists, possibly incrementing the count.
    try:
        db.add(db_link)
        db.commit()
    except Exception: # Catch IntegrityError for existing links, potentially update count
        db.rollback()
        # Add logic here to update the count if the link exists


# --- JobRun CRUD (Basic Create/Get needed later) ---

def create_job_run(db: Session, job_run: schemas.JobRunCreate) -> models.JobRun:
    """Creates a new job run entry, usually in PENDING or RUNNING state."""
    db_job_run = models.JobRun(**job_run.model_dump())
    db.add(db_job_run)
    db.commit()
    db.refresh(db_job_run)
    return db_job_run

def update_job_run_status(db: Session, job_run_id: uuid.UUID, status: str, finished_at: Optional[datetime] = None, details: Optional[dict] = None) -> Optional[models.JobRun]:
    """Updates the status and optionally finish time/details of a job run."""
    db_job_run = db.get(models.JobRun, job_run_id)
    if db_job_run:
        db_job_run.status = status
        if finished_at:
            db_job_run.finished_at = finished_at
        if details is not None:
             # Merge details instead of overwriting? Depends on requirements.
            db_job_run.details = details
        db.commit()
        db.refresh(db_job_run)
    return db_job_run


# Add CRUD for Cluster / ArticleCluster as needed later
