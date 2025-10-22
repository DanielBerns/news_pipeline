# Final Software Specification (v4.2)

Last updated: 2025-10-22  
Author: Daniel Berns  
Change log: v4.2 — integrated requested changes; added operational, security and testing details.

Purpose
This document specifies a content analysis and NLP platform that ingests data from multiple sources, transforms it into a canonical Article model, performs scheduled automated NLP analysis, and exposes the results via a web application and CLI.

High-level goals
- Reliable ingestion of documents and structured data.
- Accurate, reproducible NLP (NER, clustering, association rules).
- Fast, secure, searchable UI for analysts.
- Observable, testable, and configurable deployment.

1. Technology Stack Summary
- Backend (Core): FastAPI
- Database: SQLite (development), PostgreSQL (production)
- Database ORM & migrations: SQLAlchemy + Alembic
- NLP (Core): spaCy (with optional spaCy-Transformers)
- NLP (Models): spaCy models for English (e.g., en_core_web_sm/medium/large) and Spanish (e.g., es_core_news_sm)
- Clustering/ML: scikit-learn
- OCR: Tesseract (via pytesseract)
- Backend Task Queue & Scheduler: Celery & Redis, scheduled via Celery beat
- Full-text search: PostgreSQL native FTS (tsvector + GIN index)
- CI: GitHub Actions
- Monitoring: Prometheus + Grafana; Sentry for error tracking

2. Definitions
- Document: any raw file or feed item ingested (PDF, HTML, image, CSV row, etc.).
- Article: canonical record persisted after transformation; contains extracted normalized text and metadata.
- Job: scheduled asynchronous work (NER, clustering, association rules, word cloud, etc.).
- JobRun: recorded execution of a Job (job_run table entry).
- Extraction: text extracted from raw input using file parser and/or OCR.

3. User Personas
- Admin: configures sources, schedules and monitors jobs, runs CLI commands, manages users/sources.
- Data Analyst: searches, views, annotates, exports content and consumes NLP artifacts.

4. Functional Requirements (User Stories)

Module 1: The Data Pipeline (Ingestion & Storage)
- Story 1 (Source configuration):
  - Admin can add sources: website (URL), RSS feed, local directory, or S3 bucket. Each source stores its config (type, location, credentials, parsing hints).
  - Acceptance: UI/CLI returns 201 and persists a valid Source record.

- Story 1a (OCR):
  - For images (.jpg, .jpeg, .png, .webp) and scanned PDF pages, the pipeline runs Tesseract to extract text. Extracted text is stored in content_text and extraction metadata indicates OCR usage (e.g., extracted_via_ocr boolean).
  - Acceptance: OCR-produced text and the OCR flag are stored; failures are logged and do not abort other source processing.

- Story 1b (Parsers):
  - Use a specific parser per file type with fallbacks:
    - .pdf -> PyMuPDF (fitz) primary, fallback pdfminer or Tika.
    - .docx -> python-docx
    - .html -> BeautifulSoup (sanitize)
    - .txt/.md -> text extraction with encoding detection
    - .csv/.xlsx -> pandas for parsing, with Excel -> in-memory CSV conversion
    - images -> pytesseract
  - Acceptance: sample files for each type parse to expected text fixtures.

- Story 1c (Excel handling / CSV rows):
  - Converted .xlsx and .csv inputs produce one Article per row unless source mapping defines a single document per file. When row-mapping is used, each Article.content_text is a concatenation of the mapped columns, and Article.metadata stores row reference (row_index).
  - Acceptance: CSV with N rows results in N saved Articles when row mapping is enabled.

- Story 2 (Scheduling ingestion):
  - Admin can schedule ingestion jobs with cron expressions. Scheduler (Celery beat) triggers ingestion tasks which create JobRun records and update Source.last_run_timestamp on success.
  - Acceptance: JobRun entries are created for scheduled runs and reflected in pipeline logs.

- Story 3 (Transform):
  - Sanitization: remove scripts, unsafe HTML, normalize whitespace, dedupe whitespace/newlines, and detect language. Persist canonical Article with fields described in data model.
  - Acceptance: sanitized Article text passes sanitizer tests.

- Story 4 (Load & Index):
  - After transform, Article is loaded into PostgreSQL and its tsvector column updated for FTS. GIN index ensures performant searches.
  - Acceptance: new Articles are searchable via FTS after ingestion.

- Story 5 (Audit & Logging):
  - Admin can view pipeline activity log, filterable by date, source, status (Success/Failure), and job type. Each pipeline step logs structured data; failures for a source do not abort other sources.
  - Acceptance: pipeline logs show per-source outcomes and errors with timestamps.

Module 2: The Content Application (Interaction)
- Story 6 (Auth):
  - Users log in with username/password. Only users with is_active == true are allowed. Passwords hashed with argon2 or bcrypt.
  - Acceptance: inactive users receive 403; active users can authenticate.

- Story 7 (Search):
  - Data Analyst can perform full-text search across Articles using PostgreSQL FTS with language-aware tsvector configurations.
  - Acceptance: search results return relevant documents; explanation plans show GIN index usage.

- Story 8 (Filter):
  - Filters by metadata: source, date range, tags, language, cluster membership.
  - Acceptance: combined search+filter results are correct and paginated.

- Story 9 (View):
  - Analysts can open and view the clean, transformed Article content with metadata and annotations.

- Story 10 (Annotate - Tag):
  - Analysts add tags to an Article. Tags stored in Annotation table with type 'TAG'.

- Story 11 (Annotate - Comment):
  - Analysts add free-text comments stored as 'COMMENT' annotations with user attribution and timestamp.

- Story 12 (Export):
  - Analysts can export selected Articles as CSV or JSON. Large bulk exports are run as background jobs and produce artifact URLs for download.

Module 3: The Data Analysis (Automated Processing)
- Story 13 (Job Scheduling):
  - Admin schedules major NLP jobs: NER, Clustering, Association Rules, Word Cloud. Celery workers execute tasks and create JobRun records.

- Story 14 (Job Scope & Idempotency):
  - A scheduled NLP job processes Articles with last_nlp_run_timestamp < job_run.start_time (i.e., not processed by previous run). All tasks are idempotent; writes are upserts where appropriate to avoid duplication.

- Story 15 (Job Status):
  - UI shows "Last Analysis Run" per analysis type and per Cluster, with JobRun history available for inspection.

- Story 16 (Word Cloud):
  - Analysts request word clouds for selected articles; generation happens asynchronously and artifacts stored for retrieval.

- Story 17 (NER):
  - Analysts view NER results (People, Orgs, GPE, etc.) extracted by spaCy jobs. Language detection routes documents to correct model. Entities are normalized and deduplicated before persistence.

- Story 18 (Clustering):
  - Topic/entity clusters are generated with scikit-learn pipelines. Analysts can view clusters and member Articles.

- Story 19 (Association Rules):
  - Association rules (frequent term associations) are produced for the last successful job run and exposed for browsing.

Module 4: Administration & Management (CLI)
- Story 20 (Database Init):
  - CLI command db:init runs migrations and seeds minimal required data.

- Story 21 (Add User):
  - CLI user:create supports username, password, role and --non-interactive mode for CI.

- Story 22 (Toggle User):
  - CLI user:toggle enables/disables a user by username, toggling is_active.

- Story 23 (Add Source):
  - CLI source:add creates a Source with required config flags.

- Story 24 (Toggle Source):
  - CLI source:toggle blocks/unblocks a Source.

5. Relational Data Model (PostgreSQL) — fields, types & indexes (recommended)
- User:
  - user_id: UUID PRIMARY KEY
  - username: text UNIQUE NOT NULL
  - hashed_password: text NOT NULL
  - role: text NOT NULL CHECK(role IN ('admin','data_analyst'))
  - is_active: boolean DEFAULT true
  - created_at, updated_at: timestamptz
  - Indexes: unique index on username

- Source:
  - source_id: UUID PRIMARY KEY
  - name: text NOT NULL
  - type: text NOT NULL CHECK(type IN ('rss','website','local','s3'))
  - location: text NOT NULL
  - config: jsonb
  - last_run_timestamp: timestamptz
  - created_at, updated_at

- Article:
  - article_id: UUID PRIMARY KEY
  - source_id: UUID REFERENCES Source(source_id) ON DELETE SET NULL
  - title: text
  - content_text: text
  - original_url: text
  - source_format: text (e.g., 'pdf', 'rss', 'csv-row', 'png')
  - extraction_date: timestamptz
  - language: text (e.g., 'en', 'es')
  - checksum: text UNIQUE
  - content_text_vector: tsvector (generated or maintained via trigger)
  - last_nlp_run_timestamp: timestamptz NULLABLE
  - extracted_via_ocr: boolean DEFAULT false
  - created_at, updated_at
  - Indexes:
    - GIN index on content_text_vector
    - btree on source_id
    - btree on last_nlp_run_timestamp
    - btree on extraction_date

- Annotation:
  - annotation_id: UUID PRIMARY KEY
  - article_id: UUID REFERENCES Article(article_id) ON DELETE CASCADE
  - user_id: UUID REFERENCES User(user_id) ON DELETE SET NULL
  - type: text CHECK(type IN ('TAG','COMMENT'))
  - content: text
  - created_at: timestamptz

- NamedEntity:
  - entity_id: UUID PRIMARY KEY
  - entity_text: text NOT NULL
  - normalized_form: text NOT NULL
  - entity_type: text NOT NULL (e.g., 'PERSON','ORG','GPE')
  - language: text
  - external_link: text NULLABLE
  - created_at, updated_at
  - Unique index on (normalized_form, entity_type, language)

- ArticleEntity (join):
  - article_id: UUID REFERENCES Article(article_id) ON DELETE CASCADE
  - entity_id: UUID REFERENCES NamedEntity(entity_id) ON DELETE CASCADE
  - count: integer DEFAULT 1
  - PRIMARY KEY (article_id, entity_id)

- Cluster:
  - cluster_id: UUID PRIMARY KEY
  - cluster_name: text
  - cluster_type: text CHECK(cluster_type IN ('TOPIC','ENTITY'))
  - last_run_id: UUID REFERENCES JobRun(job_run_id) NULLABLE
  - metadata: jsonb NULLABLE
  - created_at, updated_at

- ArticleCluster (join):
  - article_id: UUID REFERENCES Article(article_id) ON DELETE CASCADE
  - cluster_id: UUID REFERENCES Cluster(cluster_id) ON DELETE CASCADE
  - score: numeric
  - PRIMARY KEY(article_id, cluster_id)

- JobRun / PipelineLog:
  - job_run_id: UUID PRIMARY KEY
  - job_name: text
  - started_at: timestamptz
  - finished_at: timestamptz NULLABLE
  - status: text CHECK(status IN ('PENDING','RUNNING','SUCCESS','FAILED','PARTIAL'))
  - processed_count: integer DEFAULT 0
  - error_count: integer DEFAULT 0
  - details: jsonb NULLABLE (for errors, summaries)
  - created_at, updated_at
  - Indexes: btree on job_name and started_at

6. Non-Functional Requirements (NFRs) — expanded
1. Database: SQLite used for local development and test; PostgreSQL used for staging and production. Use Alembic for versioned migrations.
2. Search: PostgreSQL FTS with language-specific tsvector configurations; content_text_vector must be kept up-to-date using triggers or generated columns.
3. Asynchronous Processing: All Module 3 NLP jobs run as asynchronous background tasks (Celery) separate from the web app. JobRun records must be created and updated for observability.
4. Multi-language: Detect language per Article; load and execute appropriate spaCy model for English and Spanish; allow fallback to default model when detection fails.
5. OCR: Use Tesseract for all image-to-text extraction; detect scanned PDFs (image pages) and run OCR accordingly.
6. Fault-Tolerance: Ingestion must log and continue on per-source failures; transient errors retried with exponential backoff.
7. Configuration: All application settings (database, sources, queue credentials) managed externally via YAML configuration files. Sensitive secrets provided via environment variables or secret manager referenced from YAML.
8. Testing (Coverage): Maintain >80% unit test coverage; enforce in CI (fail build if below threshold).
9. Testing (Integration): Provide integration tests for all parsers with sample fixtures.
10. Testing (UI): UI tests must cover login and search workflows using Playwright or Cypress in CI.
11. Security (Auth): All web endpoints require authentication. Implement RBAC for endpoints based on user.role.
12. Security (Transport): Use SSL/TLS in production; enforce secure cookie flags and robust CORS.
13. Security (CLI): Admin CLI scripts must require credentials or API tokens; avoid storing credentials in plaintext in the repo.
14. Observability: Expose metrics (Prometheus), structured logs, and error monitoring (Sentry). Add health/readiness endpoints.
15. Backups & Recovery: Daily DB backups with 30-day retention; test restores monthly.
16. Performance Targets: Define ingestion throughput targets (e.g., N docs/min) and baseline job durations; tune workers accordingly.

7. Configuration example (YAML)
Provide an example YAML (values may reference environment variables for secrets):

app:
  host: "0.0.0.0"
  port: 8000
  secret_key: "${ENV:APP_SECRET_KEY}"

database:
  url: "postgresql://user:${DB_PASS}@db:5432/web_pipeline"

redis:
  url: "redis://redis:6379/0"

celery:
  worker_concurrency: 4
  beat_schedule: true

logging:
  level: "INFO"

sources:
  default_parsers:
    pdf: "pymupdf"
    docx: "python-docx"
  health_check_timeout_seconds: 10

storage:
  artifacts_bucket: "s3://my-bucket/path"

8. Acceptance criteria & test plan (high level)
- Unit tests for parser functions with golden fixtures.
- Integration tests for ingestion -> transform -> store -> NLP -> query flows.
- UI E2E tests for login, search, filter, annotate and export.
- CI: GitHub Actions workflow runs tests (unit + integration + UI), reports coverage, and fails when coverage < 80%.

9. Operational & deployment notes
- Containerize app + worker; use docker-compose for local dev; prepare Kubernetes manifests or Helm charts for production.
- CI: separate workflows for tests, linting and deployments; require PR checks passing before merge.
- Migrations: use Alembic; follow backward-compatible migration policy for rolling updates.
- Secrets: inject via environment variables or secret manager (do not commit secrets).
- Monitoring & Alerts: instrument critical metrics and set alerts for failed jobs and high error rates.

10. Open questions / decisions
- Preferred auth mechanism: cookie-based sessions or JWT (if not decided, recommend cookie-based HTTP-only secure session tokens).
- Production hosting target: Kubernetes vs managed host.
- Entity linking to external KB: required or deferred?
- Retention policy for raw documents and NLP artifacts.

Appendix A — Implementation notes and recommendations
- Language detection: run lightweight langdetect at transform stage to avoid loading large transformer models unnecessarily.
- spaCy models: keep models configurable and provide startup checks that validate presence of required models; fall back gracefully if absent with clear logs.
- FTS: use weighted tsvector combining title (heavy weight) and body (lower weight) to improve rank relevance.
- Idempotency: use Article.checksum (e.g., sha256 of canonical text + source URL) to detect duplicates. For row-based sources, include row index or row key in checksum computation.
- JobRun semantics: each run records its start time; job scope selects Articles with last_nlp_run_timestamp < job_run.start_time. On success update last_nlp_run_timestamp to job_run.started_at for processed Articles.
- Parsers: include integration tests with sample files checked into tests/fixtures (small corpus) and a runner that validates parser output against expected text files.