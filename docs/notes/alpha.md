```python
import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Boolean, DateTime, ForeignKey, Text,
    Integer, Enum, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

# Define the base class for declarative models
Base = declarative_base()

# --- Enum Types (if you prefer stricter type checking) ---
# import enum
# class RoleEnum(enum.Enum):
#     admin = 'admin'
#     data_analyst = 'data_analyst'

# class AnnotationTypeEnum(enum.Enum):
#     TAG = 'TAG'
#     COMMENT = 'COMMENT'

# class ClusterTypeEnum(enum.Enum):
#     TOPIC = 'TOPIC'
#     ENTITY = 'ENTITY'

# class SourceTypeEnum(enum.Enum):
#     WEBSITE = 'website'
#     RSS = 'rss'
#     LOCAL = 'local'
#     S3 = 's3' # Added based on latest spec.md (v4.2), though not in foxtrot

# --- Models ---

class User(Base):
    """Represents a user account."""
    __tablename__ = 'users' # Use plural table names convention

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    # role = Column(Enum(RoleEnum), nullable=False) # Stricter version
    role = Column(String, nullable=False) # Simpler string version
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    annotations = relationship("Annotation", back_populates="user")

    __table_args__ = (
        CheckConstraint(role.in_(['admin', 'data_analyst']), name='user_role_check'),
    )

class Source(Base):
    """Represents a data source for ingestion."""
    __tablename__ = 'sources'

    source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    # type = Column(Enum(SourceTypeEnum), nullable=False) # Stricter version
    type = Column(String, nullable=False) # Simpler string version (website, rss, local, s3)
    location = Column(String, nullable=False) # URL or path
    config = Column(JSONB) # For parser hints, credentials, row_mapping etc.
    last_run_timestamp = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False) # Added from spec v4.0+
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    articles = relationship("Article", back_populates="source")

    __table_args__ = (
        CheckConstraint(type.in_(['website', 'rss', 'local', 's3']), name='source_type_check'),
    )


class Article(Base):
    """Represents a processed piece of content."""
    __tablename__ = 'articles'

    article_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey('sources.source_id', ondelete='SET NULL'), nullable=True, index=True)
    title = Column(Text, nullable=True)
    content_text = Column(Text, nullable=True)
    original_url = Column(Text, nullable=True)
    source_format = Column(String, nullable=True) # e.g., 'pdf', 'rss', 'csv-row', 'png'
    extraction_date = Column(DateTime(timezone=True), server_default=func.now())
    # language = Column(String(2), nullable=True) # e.g., 'en', 'es' - Added based on spec v4.2 but not explicitly in plan 1.1 model
    # checksum = Column(String, unique=True, index=True, nullable=True) # Useful for deduplication - Added based on spec v4.2
    content_text_vector = Column(TSVECTOR, nullable=True) # For PostgreSQL FTS
    last_nlp_run_timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    # extracted_via_ocr = Column(Boolean, default=False) # Added based on spec v4.2
    metadata = Column(JSONB, nullable=True) # For row_index or other metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    source = relationship("Source", back_populates="articles")
    annotations = relationship("Annotation", back_populates="article", cascade="all, delete-orphan")
    entities = relationship("NamedEntity", secondary="article_entities", back_populates="articles")
    clusters = relationship("Cluster", secondary="article_clusters", back_populates="articles")


class Annotation(Base):
    """Represents a user-added tag or comment on an article."""
    __tablename__ = 'annotations'

    annotation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.article_id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True, index=True)
    # type = Column(Enum(AnnotationTypeEnum), nullable=False) # Stricter
    type = Column(String, nullable=False) # Simpler 'TAG' or 'COMMENT'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("Article", back_populates="annotations")
    user = relationship("User", back_populates="annotations")

    __table_args__ = (
        CheckConstraint(type.in_(['TAG', 'COMMENT']), name='annotation_type_check'),
    )

class NamedEntity(Base):
    """Represents a unique named entity extracted from articles."""
    __tablename__ = 'named_entities'

    entity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_text = Column(Text, nullable=False) # e.g., "Google"
    normalized_form = Column(Text, nullable=False, index=True) # e.g., "google"
    entity_type = Column(String, nullable=False, index=True) # e.g., 'ORG', 'PERSON'
    language = Column(String(2), nullable=True, index=True) # e.g., 'en', 'es'
    # external_link = Column(Text, nullable=True) # Optional link to KB like Wikipedia
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    articles = relationship("Article", secondary="article_entities", back_populates="entities")

    __table_args__ = (
        Index('ix_named_entities_uq', normalized_form, entity_type, language, unique=True),
    )

class ArticleEntity(Base):
    """Association table linking articles to the named entities they contain."""
    __tablename__ = 'article_entities'

    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.article_id', ondelete='CASCADE'), primary_key=True)
    entity_id = Column(UUID(as_uuid=True), ForeignKey('named_entities.entity_id', ondelete='CASCADE'), primary_key=True)
    count = Column(Integer, default=1) # How many times the entity appears in the article


class Cluster(Base):
    """Represents a topic or entity cluster."""
    __tablename__ = 'clusters'

    cluster_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_name = Column(String, nullable=True) # e.g., "Topic 1: Finance"
    # cluster_type = Column(Enum(ClusterTypeEnum), nullable=False) # Stricter
    cluster_type = Column(String, nullable=False) # Simpler 'TOPIC' or 'ENTITY'
    # Optional: Link to the specific job run that created/updated this cluster
    last_run_id = Column(UUID(as_uuid=True), ForeignKey('job_runs.job_run_id', ondelete='SET NULL'), nullable=True)
    metadata = Column(JSONB, nullable=True) # e.g., top terms, cluster quality score
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    articles = relationship("Article", secondary="article_clusters", back_populates="clusters")

    __table_args__ = (
        CheckConstraint(cluster_type.in_(['TOPIC', 'ENTITY']), name='cluster_type_check'),
    )

class ArticleCluster(Base):
    """Association table linking articles to the clusters they belong to."""
    __tablename__ = 'article_clusters'

    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.article_id', ondelete='CASCADE'), primary_key=True)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey('clusters.cluster_id', ondelete='CASCADE'), primary_key=True)
    score = Column(Integer, nullable=True) # e.g., similarity score or probability


class JobRun(Base):
    """Represents an execution instance of a background job (e.g., NLP run, Ingestion run).
       This aligns with PipelineLog from spec v4.2 but named JobRun in plan 1.1."""
    __tablename__ = 'job_runs' # Renamed from PipelineLog as per plan/models

    job_run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_name = Column(String, nullable=False, index=True) # e.g., 'ner_run', 'ingest_source_xyz'
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False) # e.g., 'PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL'
    processed_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    details = Column(JSONB, nullable=True) # Store error messages, summaries, output artifact links etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(status.in_(['PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL']), name='job_run_status_check'),
        Index('ix_job_runs_job_name_started_at', job_name, started_at),
    )

# --- Index Creation (Optional but recommended for performance) ---
# Alembic handles index creation defined in __table_args__, but you can explicitly define them too.
# Example GIN index for tsvector (usually created in a migration, might need specific dialect import)
# Index('ix_articles_content_text_vector', Article.content_text_vector, postgresql_using='gin')

```

**Explanation and Notes:**

1.  **Base Class:** `declarative_base()` creates a base class that your models will inherit from.
2.  **UUID Primary Keys:** All primary keys (`user_id`, `article_id`, etc.) are defined using `UUID(as_uuid=True)` which integrates with Python's `uuid` module, and `default=uuid.uuid4` ensures a new UUID is generated automatically for new records.
3.  **Timestamps:** `created_at` uses `server_default=func.now()` to set the timestamp when the record is created in the database. `updated_at` uses `onupdate=func.now()` to automatically update the timestamp whenever the record is modified.
4.  **Relationships:** `relationship()` defines how models are connected (e.g., one-to-many between `Source` and `Article`). `back_populates` links the two sides of the relationship.
5.  **Foreign Keys & ON DELETE:** `ForeignKey()` defines the links between tables. The `ondelete` argument matches the specification:
      * `'SET NULL'` for `annotations.user_id` and `articles.source_id`.
      * `'CASCADE'` for `annotations.article_id`, `article_entities`, and `article_clusters` ensures that related detail records are automatically deleted if the parent article/entity/cluster is deleted.
6.  **Data Types:** Standard types like `String`, `Text`, `Boolean`, `DateTime`, `Integer` are used. For PostgreSQL-specific types, `UUID`, `TSVECTOR`, and `JSONB` are imported from `sqlalchemy.dialects.postgresql`.
7.  **Indexes:** `index=True` is added to frequently queried or joined columns like foreign keys and `username`. Unique constraints (`unique=True`) are added where specified. A specific unique index (`ix_named_entities_uq`) ensures entities are unique per normalized form, type, and language.
8.  **JobRun vs. PipelineLog:** The plan refers to `JobRun` while the spec uses `PipelineLog`. I've implemented it as `JobRun` based on the plan's model list for Increment 1.1, as it seems more aligned with tracking specific background task executions.
9.  **Table Arguments:** `__table_args__` is used to define multi-column indexes or check constraints (like ensuring `role` is one of the allowed values).
10. **Enum Types:** I've included commented-out code showing how you could use Python's `enum` module with SQLAlchemy's `Enum` type for stricter validation of fields like `role`, `type`, etc., if desired. The current implementation uses simple `String` columns with `CheckConstraint` for simplicity.

This file provides the necessary SQLAlchemy model definitions to proceed with creating the initial Alembic migration in Increment 1.1.


```python
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

```

**Explanation:**

1.  **Import necessary modules:** `os` for environment variables, `sqlalchemy` components, and `dotenv` (optional, for loading a `.env` file).
2.  **Load Environment Variables:** `load_dotenv()` reads key-value pairs from a `.env` file in your project root and loads them as environment variables. This is useful for storing the `DATABASE_URL` without hardcoding it.
3.  **Get `DATABASE_URL`:** It retrieves the database connection string from the `DATABASE_URL` environment variable. It defaults to a local SQLite database file (`local_dev.db`) if the variable isn't set, aligning with the spec's allowance for SQLite in development.
4.  **`connect_args` for SQLite:** Sets `{"check_same_thread": False}` only if using SQLite. This is required because FastAPI runs requests in different threads, and SQLite by default doesn't allow connections to be shared across threads.
5.  **Create Engine:** `create_engine()` sets up the core interface to the database, using the `DATABASE_URL` and connection arguments. `pool_pre_ping=True` is a good practice to check if database connections in the pool are still alive before using them.
6.  **Create `SessionLocal`:** `sessionmaker()` creates a *factory* for generating new database `Session` objects. Each session manages a transaction with the database.
7.  **`get_db` Dependency:** This is a standard pattern for FastAPI. It's a generator function that:
      * Creates a new database session (`db = SessionLocal()`).
      * `yield db`: Provides this session to the FastAPI route that depends on it.
      * `finally: db.close()`: Ensures the session is always closed after the request finishes, whether it was successful or raised an error. This returns the connection to the pool.
8.  **Optional `create_tables`:** The commented-out section shows how you *could* create tables directly using SQLAlchemy's metadata (useful for simple tests or initial setup), but the project plan rightly specifies using Alembic (`make db-upgrade`) for robust schema management.

```python
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator

# --- Base Schemas ---
# Contain fields common to both creation and reading

class UserBase(BaseModel):
    username: str
    role: str = Field(..., pattern="^(admin|data_analyst)$") # Enforce role values
    is_active: bool = True

class SourceBase(BaseModel):
    name: str
    type: str = Field(..., pattern="^(website|rss|local|s3)$") # Enforce type values
    location: str # Could be URL or path
    config: Optional[Dict[str, Any]] = None
    is_active: bool = True

class ArticleBase(BaseModel):
    title: Optional[str] = None
    content_text: Optional[str] = None
    original_url: Optional[HttpUrl | str] = None # Allow general strings too initially
    source_format: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # language: Optional[str] = Field(None, max_length=2) # e.g., 'en', 'es'
    # extracted_via_ocr: Optional[bool] = False

# --- Schemas for Creating Resources ---
# Used for request bodies when creating new items (e.g., POST requests)

class UserCreate(UserBase):
    password: str # Plain text password on creation, will be hashed before saving

class SourceCreate(SourceBase):
    pass # No extra fields needed beyond the base for creation initially

class ArticleCreate(ArticleBase):
    # Usually articles are created by the ingestion pipeline, but this
    # schema allows manual creation via API for testing (as per plan 1.2)
    source_id: Optional[uuid.UUID] = None # Allow associating with a source


# --- Schemas for Reading Resources ---
# Used for response bodies when returning items (e.g., GET requests)
# Includes fields generated by the database (like IDs, timestamps)

class User(UserBase):
    user_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Pydantic v2 alias for orm_mode

class Source(SourceBase):
    source_id: uuid.UUID
    last_run_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Article(ArticleBase):
    article_id: uuid.UUID
    source_id: Optional[uuid.UUID] = None
    extraction_date: datetime
    # checksum: Optional[str] = None
    last_nlp_run_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Schemas for other models (can be expanded later) ---

class AnnotationBase(BaseModel):
    type: str = Field(..., pattern="^(TAG|COMMENT)$")
    content: str

class AnnotationCreate(AnnotationBase):
    article_id: uuid.UUID
    # user_id will likely come from the authenticated user context

class Annotation(AnnotationBase):
    annotation_id: uuid.UUID
    article_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None # User might be deleted (SET NULL)
    created_at: datetime

    class Config:
        from_attributes = True


class NamedEntityBase(BaseModel):
    entity_text: str
    normalized_form: str
    entity_type: str
    language: Optional[str] = Field(None, max_length=2)

class NamedEntityCreate(NamedEntityBase):
    pass # Usually created by NLP pipeline

class NamedEntity(NamedEntityBase):
    entity_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobRunBase(BaseModel):
    job_name: str
    status: str = Field(..., pattern="^(PENDING|RUNNING|SUCCESS|FAILED|PARTIAL)$")
    processed_count: int = 0
    error_count: int = 0
    details: Optional[Dict[str, Any]] = None

class JobRunCreate(JobRunBase):
    # started_at is usually set on creation
    pass

class JobRun(JobRunBase):
    job_run_id: uuid.UUID
    started_at: datetime
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Add Cluster schemas if needed for API endpoints later
# class ClusterBase(BaseModel): ...
# class ClusterCreate(ClusterBase): ...
# class Cluster(ClusterBase): ...

```

**Explanation:**

1.  **Imports:** Necessary modules from `uuid`, `datetime`, `typing`, and `pydantic`.
2.  **Base Schemas (`...Base`):** These define the common fields shared between create and read operations for each model type. This promotes code reuse (DRY - Don't Repeat Yourself).
3.  **Create Schemas (`...Create`):** These inherit from the Base schemas and add fields required only during creation. For example, `UserCreate` includes the `password` field, which isn't stored directly in the database (it's hashed) and shouldn't be returned in responses.
4.  **Read Schemas (e.g., `User`, `Source`, `Article`):** These inherit from the Base schemas and add fields that are typically generated by the database upon creation or modification, such as `user_id`, `created_at`, `updated_at`. These are the schemas you'll use in FastAPI response models.
5.  **`Config` Class:**
      * `from_attributes = True`: This crucial setting (called `orm_mode = True` in Pydantic v1) allows Pydantic to read data directly from SQLAlchemy model attributes (like `my_user_orm_object.username`) when creating an instance of the Pydantic model (like `User.from_orm(my_user_orm_object)`). This makes it easy to convert your database objects into API responses.
6.  **Field Validation:** `Field(...)` is used with patterns (`pattern=...`) to enforce specific allowed values for fields like `role`, `type`, and `status`, matching the `CHECK` constraints in the database model. `max_length` could be used for fields like `language`.
7.  **Optional Fields:** Fields that can be `NULL` in the database are marked as `Optional` in Pydantic.
8.  **Future Models:** Basic schemas for `Annotation`, `NamedEntity`, and `JobRun` are included as placeholders, anticipating their use in later increments. `Cluster` schemas are mentioned but left out for brevity, as they aren't explicitly used in the initial API endpoints of Increment 1.2.

```python
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
```

**Key Points:**

1.  **Dependencies:** This file relies on `models.py` (for the database table definitions) and `schemas.py` (for the Pydantic data shapes). It also uses the `Session` object managed by `database.py`.
2.  **`Session` Object:** Each function takes `db: Session` as an argument. This session is typically provided by FastAPI's dependency injection system (using the `get_db` function from `database.py`).
3.  **Basic Operations:** It includes standard CRUD operations:
      * `get_...`: Retrieve one or multiple items.
      * `create_...`: Create a new item.
4.  **Password Hashing:** The `create_user` function includes a **placeholder** for password hashing. You need to replace the placeholder comment and line with a call to an actual hashing function (like one using `passlib` or similar) which should ideally live in a separate `core/security.py` module.
5.  **ORM Usage:** The functions use basic SQLAlchemy ORM methods:
      * `db.get(Model, id)`: Efficient way to get an object by primary key (SQLAlchemy 2.0+).
      * `select(Model).where(...)`: Build queries.
      * `db.execute(statement).scalar_one_or_none()`: Execute a query expected to return one or zero results.
      * `db.execute(statement).scalars().all()`: Execute a query and get all results as model instances.
      * `db.add(db_object)`: Stage an object to be saved.
      * `db.commit()`: Save changes to the database.
      * `db.refresh(db_object)`: Update the object with any new data generated by the database (like IDs or default timestamps).
6.  **Placeholders for Later:** Functions for Annotations, Named Entities, and JobRuns are included as they belong in `crud.py` conceptually, even if they aren't all used by the initial API endpoints in Increment 1.2. The `get_or_create_named_entity` and `link_article_to_entity` functions show the kind of logic needed by the NLP pipeline later.
