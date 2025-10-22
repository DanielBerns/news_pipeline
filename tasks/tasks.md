# Tasks by phase

## PHASE 0 — Repo & dev environment (foundation)

**Increment 0.1 — Basic repo structure and tooling**
* **Tasks:**
    * Add / update `pyproject.toml` (or `requirements.txt`) with pinned dev dependencies: fastapi, uvicorn, sqlalchemy, alembic, pytest, pytest-asyncio, httpx, pydantic, python-dotenv, psycopg2-binary (or asyncpg if used), celery, redis, spaCy, scikit-learn, pytesseract, pymupdf, python-docx, pandas, playwright.
    * Add `.editorconfig`, `.github/ISSUE_TEMPLATE` and `PR_TEMPLATE`, `.gitignore`.
    * Add `Makefile` / task runner (invoke) with common tasks: `install-dev`, `format`, `lint`, `test`, `run`.
    * Add `README/CONTRIBUTING` with setup steps.

**Increment 0.2 — Basic CI skeleton**
* **Tasks:**
    * Add GitHub Actions workflow `.github/workflows/test.yml` which:
        * installs python, sets up dependencies
        * runs pytest (unit)
        * runs linters (flake8 / black check)
        * optionally caches pip
    * Add small matrix for python versions (3.10, 3.11).

## PHASE 1 — Core backend, data models, and migrations

**Increment 1.1 — SQLAlchemy models + Alembic**
* **Tasks:**
    * Add an `app/` package with modules: `models.py`, `database.py`, `schemas.py`, `crud.py`, `main.py` (minimal FastAPI app).
    * Implement models in `models.py` using SQLAlchemy ORM matching the spec (User, Source, Article, Annotation, NamedEntity, ArticleEntity, Cluster, ArticleCluster, JobRun). Use UUID PKs.
    * Add `alembic/` with `env.py` configured to use `app.models` metadata.
    * Add initial migration creating the tables.

**Increment 1.2 — Minimal API endpoints and authentication stub**
* **Tasks:**
    * Add FastAPI app with endpoints:
        * `POST /api/users` (create user) — for now accept plaintext password, hashed on save using argon2/bcrypt.
        * `POST /api/sources` (create source)
        * `POST /api/articles` (create article) — for ingestion testing
        * `GET /api/articles` (list)
    * Authentication: implement password hashing and a simple login endpoint returning a session cookie or simple JWT (can be temporary; final auth design in Phase 8).
    * Add Pydantic schemas for request/response.

## PHASE 2 — Ingestion: text & CSV parsing, row-mode handling

**Increment 2.1 — Parser abstraction and text parser**
* **Tasks:**
    * Create a parser interface: `app/parsers/base.py` with a Parser class and `parse(file_path)` returning canonical dict: {title, content_text, metadata}.
    * Implement a TextParser for `.txt`/`.md` with encoding detection.
    * Add a pipeline runner `app/pipeline/ingest.py` with a function `ingest_source(source_id)` that reads files or feed items (for now local directory handler) and stores Articles.

**Increment 2.2 — Row mapping configuration & metadata**
* **Tasks:**
    * Add `Source.config` JSON structure for row-mapping (e.g., `{"row_mode": true, "columns": ["title","body"]}`).
    * Ensure ingest pipeline honors config and writes `row_index` to `Article.metadata`.

## PHASE 3 — NLP: language detection and spaCy NER

**Increment 3.1 — Language detection & pipeline hook**
* **Tasks:**
    * Add a language detection utility `app/nlp/langdetect.py` using `langdetect` or `fasttext-language-detector`.
    * Update transform step in pipeline to detect and set `Article.language` before saving.

**Increment 3.2 — spaCy NER integration (first pass)**
* **Tasks:**
    * Add `app/nlp/ner.py` that:
        * loads configured spaCy models (`en_core_web_sm`, `es_core_news_sm`) lazily
        * takes Article (or text + language) and returns extracted entities with types and counts
    * Normalization of entities (lowercase / strip) and create or upsert `NamedEntity` rows and `ArticleEntity` join rows (count occurrences).

**Increment 3.3 — JobRun record & update Article.last\_nlp\_run\_timestamp**
* **Tasks:**
    * When NER job runs, create a `JobRun` row and on success update `Article.last_nlp_run_timestamp` for processed articles.
    * Make sure tasks are idempotent (e.g., upsert logic).

## PHASE 4 — Full-text search (Postgres FTS) and ranking

**Increment 4.1 — tsvector column + GIN index + migration**
* **Tasks:**
    * Add `content_text_vector` `tsvector` column to Article via Alembic migration with expression or trigger for updates. Use language-specific config: e.g. `to_tsvector('english', content_text)`.
    * Add GIN index.

**Increment 4.2 — Search API and ranking weights**
* **Tasks:**
    * Add endpoint `GET /api/search?q=...&filters=...` that builds `tsquery` and runs weighted ranking (set weight A for title, B for body).
    * Implement pagination.

## PHASE 5 — Background jobs, Celery integration, and scheduling

**Increment 5.1 — Celery integration & local dev setup**
* **Tasks:**
    * Add Celery app `app/celery_app.py`, configure broker URL from YAML/env.
    * Wire tasks for ingestion runner and NER runner.
    * Add docker-compose service example for dev with Redis, Postgres, and worker.

**Increment 5.2 — Celery beat schedule and incremental runs**
* **Tasks:**
    * Add scheduled tasks for nightly NER, clustering, etc. Ensure each `JobRun` creates `start_time` and tasks process Articles with `last_nlp_run_timestamp` < `job_run.start_time`.

## PHASE 6 — Parsers: PDFs, DOCX, images + OCR, and parser integration tests

**Increment 6.1 — DOCX and HTML parser**
* **Tasks:**
    * Implement `docx` parser using `python-docx`, and HTML parser using `BeautifulSoup` with sanitizer (bleach).

**Increment 6.2 — PDF parsing (PyMuPDF + OCR fallback)**
* **Tasks:**
    * Implement PDF parser using `PyMuPDF` to extract text. Detect pages with images or low extracted text and fallback to convert page to image and run Tesseract.
    * Flag `Article.extracted_via_ocr` when OCR used.

**Increment 6.3 — Add parser integration test harness and fixtures**
* **Tasks:**
    * Add `tests/fixtures/parsers/` with small sample files (pdf, scanned-pdf, docx, html, csv).
    * Add harness test `tests/test_parsers_integration.py` that runs all parsers and compares outputs to golden files.

## PHASE 7 — Clustering, association rules, and artifacts

**Increment 7.1 — Clustering pipeline**
* **Tasks:**
    * Implement simple scikit-learn pipeline: TF-IDF -> KMeans (configurable k) -> assign cluster names heuristically (top terms).
    * Persist clusters and `ArticleCluster` entries (with score).

**Increment 7.2 — Association rules & wordclouds**
* **Tasks:**
    * Implement association rule mining (e.g., using `mlxtend` or `apriori` on token sets) to produce frequent co-occurrence rules and store them under `JobRun` details or separate table.
    * Implement asynchronous word cloud (e.g., store image to artifacts storage or local path).

## PHASE 8 — Web UI: auth, search UI, view, annotate, export

**Increment 8.1 — Auth and user flows (backend ready)**
* **Tasks:**
    * Finalize auth mechanism (recommend cookie-based HTTPOnly session with signed cookies or short-lived JWT + refresh).
    * Implement session management endpoints (login/logout) and RBAC dependencies for routes.

**Increment 8.2 — Minimal React or simple server-side UI**
* **Tasks:**
    * Implement login page, search page with results, article view page, annotate UI and export button (trigger background job for bulk exports).

## PHASE 9 — Tests, CI expansion, monitoring, and deployment

**Increment 9.1 — CI integration tests with services**
* **Tasks:**
    * Extend GitHub Actions CI to include a `integration` job with services: Postgres, Redis.
    * Run migrations, start worker in the background (or run tasks synchronously), and run integration test suite (parsers, FTS, job-run flow).

**Increment 9.2 — Observability & health checks**
* **Tasks:**
    * Add `/health` and `/ready` endpoints.
    * Integrate basic Prometheus metrics (expose `/metrics`) and add Sentry integration for exception reporting.
    * Add simple dashboards/alerts docs.

**Increment 9.3 — Containerization & deployments**
* **Tasks:**
    * Add `Dockerfile` for app and worker, `docker-compose.dev` for local development (Postgres, Redis, MinIO optionally).
    * Add example Kubernetes manifests or Helm chart stub.
    * Add step in CI for building images (optional).
