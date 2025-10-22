# **Content Analysis and NLP platform: a web pipeline**.

# Content Analysis Platform (Project Perla)

A high-performance content analysis and NLP platform designed to ingest, process, and analyze large volumes of documents. This platform provides tools for automated text extraction, named entity recognition, full-text search, and data clustering, all accessible via a modern web UI and REST API.

## Key Features

* **Multi-format Ingestion:** Ingests and parses a wide variety of file types, including `.pdf` (text and scanned/OCR), `.docx`, `.txt`, `.csv` (with row-as-document mapping), and `.html`.
* **NLP & ML Pipeline:** Automatically runs language detection, Named Entity Recognition (NER), clustering, and association rule mining on ingested content.
* **High-Performance Search:** Implements fast, ranked full-text search using PostgreSQL's built-in `tsvector` and GIN indexing.
* **Async Task Processing:** Uses Celery and Redis to manage long-running tasks like ingestion, OCR, and NLP analysis in the background.
* **Analyst Web UI:** A simple web interface for analysts to authenticate, search for articles, view content, and perform annotations.
* **Test-Driven:** Built with a full suite of unit, integration (with live services), and E2E tests.

## Technology Stack

* **Backend:** FastAPI, Pydantic
* **Database:** PostgreSQL
* **DB Migrations:** Alembic
* **Async Jobs:** Celery, Redis
* **NLP / ML:** spaCy, scikit-learn
* **File Parsers:** PyMuPDF, python-docx, Tesseract (OCR), Pandas
* **Testing:** Pytest, pytest-asyncio, HTTPX, Playwright (for E2E)
* **Containerization:** Docker, Docker Compose

---

## Getting Started (Local Development)

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* Python 3.10+
* uv
* Docker and Docker Compose
* Make (optional, for using the `Makefile` shortcuts)

### 1. Clone the Repository

```bash
git clone [https://github.com/DanielBerns/web_pipeline.git](https://github.com/DanielBerns/web_pipeline.git)
cd web_pipeline
```

### 2. Use makefile

#### 1. Installs all dependencies into a .venv
make install-dev

#### 2. Starts the Postgres database and Redis in Docker
make dev-services

#### 3. Applies database migrations to the new database
make db-upgrade

#### 4 Starts the FastAPI server with live-reload
make run

#### 5 Run only the fast unit tests (no DB needed)
make test-unit

#### 6 Run the integration tests (requires Docker services to be running)
make test-integration

#### 7 Run all tests (unit + integration)
make test-all

#### 8 Automatically formats all your code
make format

#### 9 Checks for formatting and style errors (without changing files)
make lint

#### 10 Auto-generate a new migration file
make db-migrate

#### 11 Apply the new migration to your database
make db-upgrade

#### 12 Deletes the .venv, __pycache__, etc.
make clean

## Appendix A: Github tips

### Is there a simple way to delete all tracking branches whose remote equivalent no longer exists?

https://stackoverflow.com/questions/7726949/remove-tracking-branches-no-longer-on-remote

git remote prune origin prunes tracking branches not on the remote.

git branch --merged lists branches that have been merged into the current branch.

xargs git branch -d deletes branches listed on standard input.

Be careful deleting branches listed by git branch --merged. The list could include master or other branches you'd prefer not to delete.

To give yourself the opportunity to edit the list before deleting branches, you could do the following in one line:

git branch --merged >/tmp/merged-branches && \
  vi /tmp/merged-branches && xargs git branch -d </tmp/merged-branches



