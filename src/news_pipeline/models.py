import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Integer,
    Enum,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

# Define the base class for declarative models
Base = declarative_base()

# --- Enum Types (if you prefer stricter type checking) ---
import enum


class RoleEnum(enum.Enum):
    admin = "admin"
    data_analyst = "data_analyst"


class AnnotationTypeEnum(enum.Enum):
    TAG = "TAG"
    COMMENT = "COMMENT"


class ClusterTypeEnum(enum.Enum):
    TOPIC = "TOPIC"
    ENTITY = "ENTITY"


class SourceTypeEnum(enum.Enum):
    WEBSITE = "website"
    RSS = "rss"
    LOCAL = "local"
    S3 = "s3"  # Added based on latest spec.md (v4.2), though not in foxtrot


# --- Models ---


class User(Base):
    """Represents a user account."""

    __tablename__ = "users"  # Use plural table names convention

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)  # Stricter version
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    annotations = relationship("Annotation", back_populates="user")

    __table_args__ = (
        CheckConstraint(role.in_(["admin", "data_analyst"]), name="user_role_check"),
    )


class Source(Base):
    """Represents a data source for ingestion."""

    __tablename__ = "sources"

    source_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(Enum(SourceTypeEnum), nullable=False)  # Stricter version
    location = Column(String, nullable=False)  # URL or path
    config = Column(JSONB)  # For parser hints, credentials, row_mapping etc.
    last_run_timestamp = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)  # Added from spec v4.0+
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    articles = relationship("Article", back_populates="source")

    __table_args__ = (
        CheckConstraint(
            type.in_(["website", "rss", "local", "s3"]), name="source_type_check"
        ),
    )


class Article(Base):
    """Represents a processed piece of content."""

    __tablename__ = "articles"

    article_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sources.source_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(Text, nullable=True)
    content_text = Column(Text, nullable=True)
    original_url = Column(Text, nullable=True)
    source_format = Column(
        String, nullable=True
    )  # e.g., 'pdf', 'rss', 'csv-row', 'png'
    extraction_date = Column(DateTime(timezone=True), server_default=func.now())
    language = Column(
        String(2), nullable=True
    )  # e.g., 'en', 'es' - Added based on spec v4.2 but not explicitly in plan 1.1 model
    checksum = Column(
        String, unique=True, index=True, nullable=True
    )  # Useful for deduplication - Added based on spec v4.2
    content_text_vector = Column(TSVECTOR, nullable=True)  # For PostgreSQL FTS
    last_nlp_run_timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    extracted_via_ocr = Column(Boolean, default=False)  # Added based on spec v4.2
    metadata = Column(JSONB, nullable=True)  # For row_index or other metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    source = relationship("Source", back_populates="articles")
    annotations = relationship(
        "Annotation", back_populates="article", cascade="all, delete-orphan"
    )
    entities = relationship(
        "NamedEntity", secondary="article_entities", back_populates="articles"
    )
    clusters = relationship(
        "Cluster", secondary="article_clusters", back_populates="articles"
    )


class Annotation(Base):
    """Represents a user-added tag or comment on an article."""

    __tablename__ = "annotations"

    annotation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("articles.article_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    type = Column(Enum(AnnotationTypeEnum), nullable=False)  # Stricter
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("Article", back_populates="annotations")
    user = relationship("User", back_populates="annotations")

    __table_args__ = (
        CheckConstraint(type.in_(["TAG", "COMMENT"]), name="annotation_type_check"),
    )


class NamedEntity(Base):
    """Represents a unique named entity extracted from articles."""

    __tablename__ = "named_entities"

    entity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_text = Column(Text, nullable=False)  # e.g., "Google"
    normalized_form = Column(Text, nullable=False, index=True)  # e.g., "google"
    entity_type = Column(String, nullable=False, index=True)  # e.g., 'ORG', 'PERSON'
    language = Column(String(2), nullable=True, index=True)  # e.g., 'en', 'es'
    external_link = Column(Text, nullable=True)  # Optional link to KB like Wikipedia
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    articles = relationship(
        "Article", secondary="article_entities", back_populates="entities"
    )

    __table_args__ = (
        Index(
            "ix_named_entities_uq", normalized_form, entity_type, language, unique=True
        ),
    )


class ArticleEntity(Base):
    """Association table linking articles to the named entities they contain."""

    __tablename__ = "article_entities"

    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("articles.article_id", ondelete="CASCADE"),
        primary_key=True,
    )
    entity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("named_entities.entity_id", ondelete="CASCADE"),
        primary_key=True,
    )
    count = Column(
        Integer, default=1
    )  # How many times the entity appears in the article


class Cluster(Base):
    """Represents a topic or entity cluster."""

    __tablename__ = "clusters"

    cluster_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_name = Column(String, nullable=True)  # e.g., "Topic 1: Finance"
    cluster_type = Column(Enum(ClusterTypeEnum), nullable=False)  # Stricter
    # Optional: Link to the specific job run that created/updated this cluster
    last_run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_runs.job_run_id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata = Column(JSONB, nullable=True)  # e.g., top terms, cluster quality score
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    articles = relationship(
        "Article", secondary="article_clusters", back_populates="clusters"
    )

    __table_args__ = (
        CheckConstraint(
            cluster_type.in_(["TOPIC", "ENTITY"]), name="cluster_type_check"
        ),
    )


class ArticleCluster(Base):
    """Association table linking articles to the clusters they belong to."""

    __tablename__ = "article_clusters"

    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("articles.article_id", ondelete="CASCADE"),
        primary_key=True,
    )
    cluster_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clusters.cluster_id", ondelete="CASCADE"),
        primary_key=True,
    )
    score = Column(Integer, nullable=True)  # e.g., similarity score or probability


class JobRun(Base):
    """Represents an execution instance of a background job (e.g., NLP run, Ingestion run).
    This aligns with PipelineLog from spec v4.2 but named JobRun in plan 1.1."""

    __tablename__ = "job_runs"  # Renamed from PipelineLog as per plan/models

    job_run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_name = Column(
        String, nullable=False, index=True
    )  # e.g., 'ner_run', 'ingest_source_xyz'
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        String, nullable=False
    )  # e.g., 'PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL'
    processed_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    details = Column(
        JSONB, nullable=True
    )  # Store error messages, summaries, output artifact links etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            status.in_(["PENDING", "RUNNING", "SUCCESS", "FAILED", "PARTIAL"]),
            name="job_run_status_check",
        ),
        Index("ix_job_runs_job_name_started_at", job_name, started_at),
    )


# --- Index Creation (Optional but recommended for performance) ---
# Alembic handles index creation defined in __table_args__, but you can explicitly define them too.
# Example GIN index for tsvector (usually created in a migration, might need specific dialect import)
Index(
    "ix_articles_content_text_vector",
    Article.content_text_vector,
    postgresql_using="gin",
)
