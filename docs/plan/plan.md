# Implementation Plan — Incremental, test-driven rollout (for spec v4.2)

Last updated: 2025-10-22  
Prepared by: GitHub Copilot (@copilot)

This document is a step-by-step implementation plan for the content-analysis / NLP platform specified in specs/spec.md (v4.2). It breaks the work into small, testable increments. Each increment contains:
- objective and short description
- concrete tasks and files to add
- automated tests to validate the increment
- branch & PR naming guidance
- estimated effort (rough)
- acceptance criteria

Follow the plan in order. Each increment should be a small pull request that can be reviewed and merged quickly.

Overview of phases
- Phase 0 — Repository & developer environment setup
- Phase 1 — Core backend, models, migrations, and basic API
- Phase 2 — Ingestion pipeline: simple text and CSV parsing
- Phase 3 — NLP: language detection and spaCy NER pipeline
- Phase 4 — Full-text search (Postgres FTS) & indexing
- Phase 5 — Background jobs (Celery) + job-run tracking
- Phase 6 — Parsers expansion (PDF, DOCX, Images/OCR)
- Phase 7 — Clustering & association rules
- Phase 8 — Web UI basics: auth, search, view, annotate
- Phase 9 — Tests, CI, monitoring, and deployment notes

Each phase is broken into increments (small commits / PRs).

---

PHASE 0 — Repo & dev environment (foundation)
Goal: Make the repository easy to develop, run tests locally, and build on.

Increment 0.1 — Basic repo structure and tooling
- Tasks:
  - Add / update pyproject.toml (or requirements.txt) with pinned dev dependencies: fastapi, uvicorn, sqlalchemy, alembic, pytest, pytest-asyncio, httpx, pydantic, python-dotenv, psycopg2-binary (or asyncpg if used), celery, redis, spaCy, scikit-learn, pytesseract, pymupdf, python-docx, pandas, playwright.
  - Add .editorconfig, .github/ISSUE_TEMPLATE and PR_TEMPLATE, .gitignore.
  - Add Makefile / task runner (invoke) with common tasks: install-dev, format, lint, test, run.
  - Add README/CONTRIBUTING with setup steps.
- Files to add:
  - pyproject.toml or requirements-dev.txt
  - Makefile
  - .github/PULL_REQUEST_TEMPLATE.md
  - README.md (dev setup)
- Tests:
  - A smoke test that imports `fastapi` and `sqlalchemy` to ensure dependencies installed.
  - pytest test: tests/test_env.py
    - assert "fastapi" importable
- Branch/PR: branch `bootstrap/env-setup`, PR title: "chore: repo bootstrapping and dev tooling"
- Estimated: 1-2 days
- Acceptance: `make install-dev` and `pytest` succeed locally.

Increment 0.2 — Basic CI skeleton
- Tasks:
  - Add GitHub Actions workflow `ci/test.yml` which:
    - installs python, sets up dependencies
    - runs pytest (unit)
    - runs linters (flake8 / black check)
    - optionally caches pip
  - Add small matrix for python versions (3.10, 3.11)
- Tests:
  - Ensure CI passes on PR for the env-setup branch.
- Branch/PR: `ci/add-github-actions`, PR title: "ci: add basic CI for tests and lint"
- Estimated: 0.5 day
- Acceptance: Actions pass after merge.

Narrative: I prepared the repository scaffold, CI baseline, and dev docs so the team can make small, testable changes quickly.

---

PHASE 1 — Core backend, data models, and migrations
Goal: Implement the canonical data model and make simple endpoints to create/list users, sources, and articles. Add Alembic migrations.

Increment 1.1 — SQLAlchemy models + Alembic
- Tasks:
  - Add an `app/` package with modules: models.py, database.py, schemas.py, crud.py, main.py (minimal FastAPI app).
  - Implement models in models.py using SQLAlchemy ORM matching the spec (User, Source, Article, Annotation, NamedEntity, ArticleEntity, Cluster, ArticleCluster, JobRun). Use UUID PKs.
  - Add `alembic/` with env.py configured to use app.models metadata.
  - Add initial migration creating the tables.
- Files to add:
  - app/models.py
  - app/database.py (engine + session)
  - alembic/env.py and alembic/versions/XXXX_initial.py
- Tests:
  - Unit tests that use SQLite in-memory to create tables and add a sample User/Source/Article:
    - tests/test_models.py:
      - create a user and an article, assert fields persisted.
  - Use pytest fixtures for session.
- Branch/PR: `feature/models-and-migrations`, PR title: "feat: add SQLAlchemy models and initial Alembic migration"
- Estimated: 1-2 days
- Acceptance: `alembic upgrade head` creates tables in dev Postgres; tests pass with SQLite.

Increment 1.2 — Minimal API endpoints and authentication stub
- Tasks:
  - Add FastAPI app with endpoints:
    - POST /api/users (create user) — for now accept plaintext password, hashed on save using argon2/bcrypt.
    - POST /api/sources (create source)
    - POST /api/articles (create article) — for ingestion testing
    - GET /api/articles (list)
  - Authentication: implement password hashing and a simple login endpoint returning a session cookie or simple JWT (can be temporary; final auth design in Phase 8).
  - Add Pydantic schemas for request/response.
- Files to add:
  - app/api/users.py, app/api/articles.py, app/api/sources.py, app/core/security.py
  - tests/test_api_basic.py
- Tests:
  - Use `httpx.AsyncClient` and `pytest-asyncio`:
    - create user via API and assert 201
    - create source and article, then query GET /api/articles and assert the article exists
- Branch/PR: `feature/basic-api`, PR title: "feat(api): add basic API endpoints and auth stub"
- Estimated: 1-2 days
- Acceptance: API endpoints pass integration tests using test client.

Narrative: The data model and a minimal API are in place so we can persist test data and iterate on ingestion and analysis.

---

PHASE 2 — Ingestion: text & CSV parsing, row-mode handling
Goal: Implement ingestion logic for simple text files, CSVs, and the "row-as-article" behavior. Create a small pipeline runner used by tests.

Increment 2.1 — Parser abstraction and text parser
- Tasks:
  - Create a parser interface: `app/parsers/base.py` with a Parser class and `parse(file_path)` returning canonical dict: {title, content_text, metadata}.
  - Implement a TextParser for .txt/.md with encoding detection.
  - Add a pipeline runner `app/pipeline/ingest.py` with a function ingest_source(source_id) that reads files or feed items (for now local directory handler) and stores Articles.
- Files to add:
  - app/parsers/base.py, app/parsers/text_parser.py
  - app/pipeline/ingest.py
  - tests/fixtures/simple.txt and small csv
  - tests/test_parsers.py and tests/test_ingest.py
- Tests:
  - Unit tests for parser: given fixture, parse returns expected content.
  - Integration tests: pipeline ingests a directory with one txt and one csv (row-mode) and persists Articles.
- Branch/PR: `feature/parsers-text-csv`, PR title: "feat(parsers): add text and csv parsers and row-as-article ingestion"
- Estimated: 1-2 days
- Acceptance: CSV with 3 rows results in 3 Article entries when row mapping enabled.

Increment 2.2 — Row mapping configuration & metadata
- Tasks:
  - Add Source.config JSON structure for row-mapping (e.g., {"row_mode": true, "columns": ["title","body"]}).
  - Ensure ingest pipeline honors config and writes row_index to Article.metadata.
- Tests:
  - Create source with row_mode true, ingest CSV fixture, assert row_index metadata and number of Article rows equals CSV rows.
- Branch/PR: `feature/row-mapping-config`, PR title: "feat: support CSV/XLSX row-as-article mapping"
- Estimated: 0.5-1 day
- Acceptance: Metadata present and correct.

Narrative: At this point we can ingest basic textual data and structured CSV rows into the Article model and run deterministic tests around ingests.

---

PHASE 3 — NLP: language detection and spaCy NER
Goal: Add language detection, integrate spaCy NER for English/Spanish, and persist NamedEntity and ArticleEntity.

Increment 3.1 — Language detection & pipeline hook
- Tasks:
  - Add a language detection utility `app/nlp/langdetect.py` using `langdetect` or fasttext-language-detector.
  - Update transform step in pipeline to detect and set Article.language before saving.
- Tests:
  - Unit test: feed English and Spanish sentences and assert detected language matches.
  - Integration test: ingest sample English article and assert Article.language == "en".
- Branch/PR: `feature/lang-detection`, PR title: "feat(nlp): add language detection in transform pipeline"
- Estimated: 0.5-1 day
- Acceptance: language field set for sample fixtures.

Increment 3.2 — spaCy NER integration (first pass)
- Tasks:
  - Add `app/nlp/ner.py` that:
    - loads configured spaCy models (en_core_web_sm, es_core_news_sm) lazily
    - takes Article (or text + language) and returns extracted entities with types and counts
  - Normalization of entities (lowercase / strip) and create or upsert NamedEntity rows and ArticleEntity join rows (count occurrences).
- Tests:
  - Unit tests for ner on sample text; assert expected entity types and normalized form.
  - Integration test: run NER job for one article and assert NamedEntity and ArticleEntity rows created and counts match.
- Branch/PR: `feature/ner-spacy`, PR title: "feat(nlp): basic spaCy NER extraction and persistence"
- Estimated: 1-2 days
- Acceptance: Entities persisted and queries return entity list.

Increment 3.3 — JobRun record & update Article.last_nlp_run_timestamp
- Tasks:
  - When NER job runs, create a JobRun row and on success update Article.last_nlp_run_timestamp for processed articles.
  - Make sure tasks are idempotent (e.g., upsert logic).
- Tests:
  - Simulate a JobRun and assert JobRun row created, Article.last_nlp_run_timestamp updated.
- Branch/PR: `feature/jobrun-ner`, PR title: "feat(nlp): record JobRun and update Article NLP timestamp"
- Estimated: 0.5 day
- Acceptance: JobRun exists and timestamps updated.

Narrative: We now have language-aware NER running and persisting entities with traceable JobRuns. This enables later features and tests.

---

PHASE 4 — Full-text search (Postgres FTS) and ranking
Goal: Implement Postgres FTS tsvector column, trigged updates, and search API.

Increment 4.1 — tsvector column + GIN index + migration
- Tasks:
  - Add `content_text_vector` tsvector column to Article via Alembic migration with expression or trigger for updates. Use language-specific config: e.g. to_tsvector('english', content_text).
  - Add GIN index.
- Tests:
  - Integration tests using a test Postgres (recommend GitHub Actions service or testcontainers) to apply migrations and insert sample Articles, then run SQL ts_query queries and assert results.
- Branch/PR: `feature/fts-migration`, PR title: "feat(db): add tsvector column and GIN index for FTS"
- Estimated: 1 day
- Acceptance: FTS index present and used in EXPLAIN for searches.

Increment 4.2 — Search API and ranking weights
- Tasks:
  - Add endpoint `GET /api/search?q=...&filters=...` that builds tsquery and runs weighted ranking (set weight A for title, B for body).
  - Implement pagination.
- Tests:
  - Integration test hits API and assert expected documents order for queries.
- Branch/PR: `feature/search-api`, PR title: "feat(api): add FTS search endpoint with ranking"
- Estimated: 1-2 days
- Acceptance: API returns relevant hits and uses tsvector/Gin index.

Narrative: FTS is now operational, enabling fast, ranked search over ingested content.

---

PHASE 5 — Background jobs, Celery integration, and scheduling
Goal: Run NER and other analysis jobs via Celery workers and Celery beat. Track job runs and ensure idempotency.

Increment 5.1 — Celery integration & local dev setup
- Tasks:
  - Add Celery app `app/celery_app.py`, configure broker URL from YAML/env.
  - Wire tasks for ingestion runner and NER runner.
  - Add docker-compose service example for dev with Redis, Postgres, and worker.
- Tests:
  - Unit test for tasks calling pipeline functions directly (use in-memory DB or test DB).
  - Functional test: start worker in dev and run a task locally (document how to run).
- Branch/PR: `feature/celery-setup`, PR title: "feat(worker): integrate Celery and add worker tasks"
- Estimated: 1-2 days
- Acceptance: tasks can be scheduled and executed locally.

Increment 5.2 — Celery beat schedule and incremental runs
- Tasks:
  - Add scheduled tasks for nightly NER, clustering, etc. Ensure each JobRun creates start_time and tasks process Articles with last_nlp_run_timestamp < job_run.start_time.
- Tests:
  - Unit tests for job scope selection logic.
  - Integration: schedule a run and assert only unprocessed Articles get processed.
- Branch/PR: `feature/celery-beat-schedules`, PR title: "feat(worker): add scheduled job execution and job-run scoped processing"
- Estimated: 1 day
- Acceptance: scheduled tasks process only expected articles and JobRun recorded.

Narrative: With Celery in place we can execute long-running tasks asynchronously and test that incremental processing works correctly.

---

PHASE 6 — Parsers: PDFs, DOCX, images + OCR, and parser integration tests
Goal: Expand parsers to handle PDFs (including scanned pages), DOCX, HTML cleaning, and images using Tesseract. Add integration tests (fixtures).

Increment 6.1 — DOCX and HTML parser
- Tasks:
  - Implement docx parser using python-docx, and HTML parser using BeautifulSoup with sanitizer (bleach).
- Tests:
  - Integration tests with sample fixtures, asserting normalized text outputs.
- Branch/PR: `feature/parser-docx-html`, PR title: "feat(parsers): add docx and html parsers and sanitizer"
- Estimated: 1 day

Increment 6.2 — PDF parsing (PyMuPDF + OCR fallback)
- Tasks:
  - Implement PDF parser using PyMuPDF to extract text. Detect pages with images or low extracted text and fallback to convert page to image and run Tesseract.
  - Flag Article.extracted_via_ocr when OCR used.
- Tests:
  - Integration tests with two PDF fixtures: a text-based PDF and a scanned-image PDF. Assert extracted text and OCR flag.
- Branch/PR: `feature/parser-pdf-ocr`, PR title: "feat(parsers): add PDF parsing with OCR fallback"
- Estimated: 2 days (due to OCR complexity)

Increment 6.3 — Add parser integration test harness and fixtures
- Tasks:
  - Add `tests/fixtures/parsers/` with small sample files (pdf, scanned-pdf, docx, html, csv).
  - Add harness test `tests/test_parsers_integration.py` that runs all parsers and compares outputs to golden files.
- Tests:
  - Golden-file comparison assertions.
- Branch/PR: `test/parsers-fixtures`, PR title: "test: add parser fixtures and golden-file integration tests"
- Estimated: 1 day
- Acceptance: Parser tests pass in CI (use actions with apt-get tesseract for runner).

Narrative: Parsers now cover most file types and have integration tests to prevent regressions.

---

PHASE 7 — Clustering, association rules, and artifacts
Goal: Implement clustering (topic detection) and association rules using scikit-learn and store results in Cluster & ArticleCluster. Create wordcloud artifact generation.

Increment 7.1 — Clustering pipeline
- Tasks:
  - Implement simple scikit-learn pipeline: TF-IDF -> KMeans (configurable k) -> assign cluster names heuristically (top terms).
  - Persist clusters and ArticleCluster entries (with score).
- Tests:
  - Unit test for clustering pipeline with synthetic corpus where clusters are known and membership asserted.
  - Integration test running clustering job over stored Articles and verifying ArticleCluster entries count > 0.
- Branch/PR: `feature/clustering`, PR title: "feat(ml): add clustering pipeline and persistence"
- Estimated: 1-2 days

Increment 7.2 — Association rules & wordclouds
- Tasks:
  - Implement association rule mining (e.g., using mlxtend or apriori on token sets) to produce frequent co-occurrence rules and store them under JobRun details or separate table.
  - Implement asynchronous word cloud (e.g., store image to artifacts storage or local path).
- Tests:
  - Unit test for association mining algorithm on contrived data.
  - Integration: request wordcloud generation via API, assert artifact URL present and file exists.
- Branch/PR: `feature/association-wordcloud`, PR title: "feat(ml): add association rules and async wordcloud generation"
- Estimated: 1-2 days

Narrative: Analytical features added and instrumented through JobRun records so analysts can access clusters and rules.

---

PHASE 8 — Web UI: auth, search UI, view, annotate, export
Goal: Build a minimal frontend for analysts to authenticate, search articles, view content, add tags/comments, and export selected articles.

Increment 8.1 — Auth and user flows (backend ready)
- Tasks:
  - Finalize auth mechanism (recommend cookie-based HTTPOnly session with signed cookies or short-lived JWT + refresh).
  - Implement session management endpoints (login/logout) and RBAC dependencies for routes.
- Tests:
  - API tests for login: POST /api/login returns 200 and sets cookie; 403 for inactive user.
- Branch/PR: `feature/auth-finalize`, PR title: "feat(auth): finalize auth and session management"
- Estimated: 1-2 days

Increment 8.2 — Minimal React or simple server-side UI
- Approach options:
  - Option A (fast): Build server-side rendered templates with Jinja2 in FastAPI for a minimal UI.
  - Option B (future-ready): Create a small React app under `web/` that talks to API; use Vite for dev.
- Tasks:
  - Implement login page, search page with results, article view page, annotate UI and export button (trigger background job for bulk exports).
- Tests:
  - Add Playwright E2E tests:
    - test_login_and_search_flow: login -> search -> open article -> add tag -> export small selection triggers artifact and link.
- Branch/PR: `feature/ui-basic` (pick option A or B), PR title: "feat(ui): add basic analyst UI with login, search, view, annotate"
- Estimated: 3-5 days (depending on chosen stack)
- Acceptance: Playwright tests pass in CI.

Narrative: A usable UI closes the loop enabling analysts to interact with ingestion and analysis results.

---

PHASE 9 — Tests, CI expansion, monitoring, and deployment
Goal: Harden tests, add integration CI (Postgres, Redis), configure monitoring and review deployment strategy.

Increment 9.1 — CI integration tests with services
- Tasks:
  - Extend GitHub Actions CI to include a `integration` job with services: Postgres, Redis.
  - Run migrations, start worker in the background (or run tasks synchronously), and run integration test suite (parsers, FTS, job-run flow).
- Tests:
  - All integration tests pass in CI. Enforce coverage threshold > 80% for unit tests.
- Branch/PR: `ci/integration-tests`, PR title: "ci: add integration tests with Postgres and Redis"
- Estimated: 1-2 days

Increment 9.2 — Observability & health checks
- Tasks:
  - Add `/health` and `/ready` endpoints.
  - Integrate basic Prometheus metrics (expose `/metrics`) and add Sentry integration for exception reporting.
  - Add simple dashboards/alerts docs.
- Tests:
  - Smoke tests asserting endpoints return expected statuses.
- Branch/PR: `ops/observability`, PR title: "chore: add health endpoints and basic metrics/error reporting"
- Estimated: 1 day

Increment 9.3 — Containerization & deployments
- Tasks:
  - Add Dockerfile for app and worker, docker-compose.dev for local development (Postgres, Redis, MinIO optionally).
  - Add example Kubernetes manifests or Helm chart stub.
  - Add step in CI for building images (optional).
- Tests:
  - Compose up smoke test: `docker-compose -f docker-compose.dev.yml up --build`, ensure app starts and responds to /health.
- Branch/PR: `ops/containerize`, PR title: "chore: dockerize app and worker, add docker-compose dev"
- Estimated: 1-2 days

Narrative: With CI and observability in place we can safely run integration tests and deploy with confidence.

---

Testing strategy (detailed)
- Unit tests: pytest, fast, use SQLite or monkeypatch external calls. Place unit tests under `tests/unit/`.
- Async tests: pytest-asyncio for FastAPI async endpoints.
- Integration tests: `tests/integration/` using Docker services via GitHub Actions or testcontainers for Postgres/Redis. Use fixtures for DB creation and Alembic migrations run programmatically before tests.
- E2E UI tests: Playwright (GitHub Action runner supports Playwright). Place under `tests/e2e/`.
- Coverage: use coverage.py and configure CI to fail when coverage < 80% (enforce for unit tests; integration coverage may be tracked separately).

Example tests (snippets)
- tests/test_models.py
  - create user, create article, query, assert fields.
- tests/test_parsers.py
  - def test_text_parser():
      - parsed = TextParser.parse(fixture)
      - assert "expected phrase" in parsed["content_text"]
- tests/test_ner.py
  - run ner.extract(text="Apple is a company", language="en")
  - assert an entity 'apple' with entity_type 'ORG' (normalized form)
- tests/test_search_api.py
  - create article "Quantum Computing" and "Classical Mechanics" and assert searching "quantum" returns the first result top.

CI job layout suggestion
- job: unit-tests
  - runs pytest unit tests, reports coverage
- job: integration-tests (requires unit-tests success)
  - runs integration test suite with postgres and redis services
- job: e2e (optional gated)
  - runs Playwright tests (may require building frontend)
- job: lint
  - runs black --check and flake8

Branching & PR guidance
- Create one small-feature branch per increment (use prefix `feature/`, `fix/`, `chore/`, `ci/`, `ops/`).
- Each PR:
  - Should be small (one responsibility)
  - Include tests that assert functionality
  - Include migration files if DB change
  - Link to spec sections and acceptance criteria in description
  - Use descriptive PR title and body, example:
    - Title: "feat(parsers): add PDF parser with OCR fallback"
    - Body: short description, files changed, how to test locally, sample curl commands

Deliverables & timeline (rough)
- Weeks 1-2: Phase 0 + Phase 1 + basic ingestion (text/csv)
- Weeks 3-4: NER + JobRun + FTS search
- Weeks 5-6: Parsers for PDF/DOCX/OCR + clustering
- Weeks 7-8: UI skeleton + E2E tests + CI integration improvements
- Week 9+: Hardening, deployment setup, observability, retention/backups

Acceptance criteria summary (project-level)
- All unit tests pass with ≥80% coverage.
- Integration tests with Postgres/Redis pass in CI.
- Ingestion pipeline can ingest text, CSV rows, PDF, DOCX, and images (OCR).
- NER extraction persists entities and JobRun records.
- Search endpoint returns ranked results using Postgres FTS.
- Celery workers can run scheduled NLP jobs idempotently.
- Basic UI allows login, search, view, annotate, and export; E2E tests cover login & search.

Appendix: Quick-run commands and conventions
- Start local dev stack (example):
  - make install-dev
  - docker-compose -f docker-compose.dev.yml up --build
  - alembic upgrade head
  - uvicorn app.main:app --reload
- Run unit tests:
  - pytest tests/unit -q
- Run integration tests (local, require services):
  - pytest tests/integration -q
- Run Playwright tests:
  - npx playwright install --with-deps
  - pytest tests/e2e -q

What I did and what comes next
I prepared this incremental, test-driven implementation plan that starts with repository bootstrapping and proceeds through ingestion, NLP, search, background jobs, parsers, UI, and operationalization. Each step includes precise tests to validate correctness and small branch/PR suggestions so work can be delivered iteratively.

If you'd like, I can:
- Create the `docs/implementation_plan.md` file in the `update-spec-v4.2` branch (or a new branch) and open a PR; or
- Start implementing Increment 0.1 (bootstrap) now and push the first PR skeleton (README, pyproject, Makefile, CI skeleton). Tell me which you'd like me to do next and which increment to start on, and I'll proceed.
