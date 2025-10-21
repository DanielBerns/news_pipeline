## Revised Software Specification (v2.0)

### 1. User Personas

Your defined roles are now integrated:

* **`Admin`:** Replaces "Data Admin." This user is responsible for configuring, running, and monitoring the data ingestion pipeline.
* **`Data Analyst`:** Replaces "Content Analyst." This user is the primary consumer of the data, responsible for searching, annotating, and—critically—running analysis jobs on the content.

### 2. Functional Requirements (User Stories)

The requirements are now split into three distinct modules.

#### Module 1: The Data Pipeline (Ingestion & Storage)

* **Story 1 (Extract):** As an **`Admin`**, I want to configure sources, which can be websites, RSS feeds, or local directories containing files of various types (`.txt`, `.md`, `.csv`, `.docx`, `.xlsx`, `.pdf`, `.jpg`, `.png`, `.webp`), so that the system can ingest all required content.
    * **1a (OCR):** As an **`Admin`**, when the pipeline detects an image file (`.jpg`, `.png`, `.webp`), I want the system to automatically run **Optical Character Recognition (OCR)** on it to extract any machine-readable text.
    * **1b (Parsers):** As an **`Admin`**, I want the system to use the correct parser for each file type (e.g., a PDF parser, an Excel parser, a DOCX parser) to extract its text content.
* **Story 2 (Schedule):** (Unchanged) As an **`Admin`**, I want to be able to schedule ingestion jobs...
* **Story 3 (Transform):** (Unchanged) As an **`Admin`**, I want the system to automatically sanitize and transform all extracted content (including text from OCR) into a standardized "Article" data model...
* **Story 4 (Load):** (Unchanged) As an **`Admin`**, I want the transformed "Article" data to be automatically loaded and indexed into the **PostgreSQL database**...
* **Story 5 (Audit):** (Unchanged) As an **`Admin`**, I want to view a detailed pipeline activity log...

#### Module 2: The Content Application (Interaction)

* **Story 6 (Auth):** As a user (`Admin` or `Data Analyst`), I want to log in to the system with a username and password so that the system can identify me and my role.
* **Story 7 (Search):** As a **`Data Analyst`**, I want to perform a full-text search across the content of all articles in the **PostgreSQL database**...
* **Story 8 (Filter):** As a **`Data Analyst`**, I want to filter my search results by metadata, such as the original **source**, the **extraction date range**, and any **tags** or **annotations**.
* **Story 9 (View):** As a **`Data Analyst`**, I want to open a search result to view the clean, transformed article content...
* **Story 10 (Annotate - Tag):** As a **`Data Analyst`**, I want to be able to add one or more **tags** to any article...
* **Story 11 (Annotate - Comment):** As a **`Data Analyst`**, I want to be able to add free-text **comments** or notes to an article...
* **Story 12 (Export):** As a **`Data Analyst`**, I want to be able to select one or more articles and **export** them (e.g., as CSV or JSON)...

#### Module 3: The Data Analysis (Processing)

This new module covers your detailed definition of "process." These are all features for the **`Data Analyst`**.

* **Story 13 (Word Cloud):** As a **`Data Analyst`**, I want to select one or more articles and generate a **word cloud** to visualize the most
    frequent terms.
* **Story 14 (NER):** As a **`Data Analyst`**, I want to view a list of all **named entities** (e.g., People, Organizations, Locations) that were automatically extracted from an article.
* **Story 15 (Topic Clustering):** As a **`Data Analyst`**, I want to run a job that groups all articles into **clusters based on their topic similarity** (e.g., using TF-IDF and k-means).
* **Story 16 (Entity Clustering):** As a **`Data Analyst`**, I want to be able to find and group all articles that mention the **same set of named entities**.
* **Story 17 (Association Rules):** As a **`Data Analyst`**, I want to run a job on a set of articles to discover **association rules** between words, phrases, or entities (e.g., "Find all articles where 'Project X' is mentioned, and show what other terms or organizations are most frequently mentioned alongside it").

***

### 3. Key Entities (Relational Data Model)

This model is now explicitly designed for a relational database like PostgreSQL.

* `User`:
    * `user_id` (PK)
    * `username`
    * `hashed_password`
    * `role` ('admin', 'data_analyst')

* `Source`: (Unchanged)
    * `source_id` (PK), `name`, `type`, `location`, `last_run_timestamp`

* `Article`:
    * `article_id` (PK)
    * `source_id` (FK to `Source`)
    * `title`
    * `content_text` (The cleaned, extracted text)
    * `original_url`
    * `source_format` (e.g., 'pdf', 'rss', 'csv', 'png')
    * `extraction_date`
    * `content_text_vector` (A `tsvector` column for full-text search)

* `Annotation`:
    * `annotation_id` (PK)
    * `article_id` (FK to `Article`)
    * `user_id` (FK to `User`)
    * `type` ('TAG', 'COMMENT')
    * `content`
    * `created_at`

* `NamedEntity`: (New table for NLP)
    * `entity_id` (PK)
    * `entity_text` (e.g., "Google", "John Doe")
    * `entity_type` (e.g., 'ORG', 'PERSON', 'GPE')

* `ArticleEntity`: (New join table for NLP)
    * `article_id` (FK to `Article`)
    * `entity_id` (FK to `NamedEntity`)

* `Cluster`: (New table for NLP)
    * `cluster_id` (PK)
    * `cluster_name` (e.g., "Topic 1: Finance" or "Entity Group 5")
    * `cluster_type` ('TOPIC', 'ENTITY')

* `ArticleCluster`: (New join table for NLP)
    * `article_id` (FK to `Article`)
    * `cluster_id` (FK to `Cluster`)

* `PipelineLog`: (Unchanged)

***

### 4. Non-Functional Requirements (NFRs)

Your answers add these critical constraints.

1.  **Database Technology:** The system must use an SQL-compliant database. **SQLite** is acceptable for local development, but **PostgreSQL** must be the database for production.
2.  **Search Implementation:** Full-text search (Story 7) must be implemented using PostgreSQL's built-in full-text search capabilities (e.g., `tsvector`, `tsquery`, and GIN indexes).
3.  **Asynchronous Processing:** All NLP tasks (NER, clustering, association rules) are computationally expensive. They **must run as asynchronous background jobs** (e.g., using a task queue like Celery & Redis) to avoid blocking the user interface and the main application server. The `Data Analyst` should be able to start a job and get a notification when it's complete.
4.  **Error Handling:** (Unchanged) The pipeline must be fault-tolerant...
5.  **Scalability:** (Unchanged) The system must be designed to handle...
6.  **Security:** All actions, especially annotations and running analysis jobs, must be authenticated and authorized based on the user's role (`Admin` or `Data Analyst`).

***

### 5. New Key Questions to Clarify (v2.0)

This more detailed spec raises new, more specific technical questions:

1.  **OCR Tooling:** Processing images (`.jpg`, `.png`, etc.) requires an OCR engine. Do you have a preferred tool or library (e.g., **Tesseract**)?
2.  **NLP Libraries:** For Module 3 (NER, clustering), do you have preferred Python libraries (e.g., **spaCy** for NER, **scikit-learn** for clustering)?
3.  **CSV/XLSX Content Model:** How should structured data from `.csv` and `.xlsx` files be handled?
    * **Option A:** Should each **row** be treated as a separate, small "article"?
    * **Option B:** Should the **entire file** be transformed into one text document (e.g., by concatenating all cells) and stored as a single "article"?
4.  **Processing Triggers:** How should the NLP processing jobs (Module 3) be triggered?
    * **Option A (On-Demand):** The `Data Analyst` selects articles and clicks a "Run Analysis" button.
    * **Option B (On-Ingest):** Should NER (Story 14) run automatically on *every single article* as soon as it's loaded into the database? (This would consume more processing power but make data available immediately).

1.  **OCR Tooling:** Processing images (`.jpg`, `.png`, etc.) requires an OCR engine. Do you have a preferred tool or library (e.g., **Tesseract**)?    
I want to use Tesseract.
2.  **NLP Libraries:** For Module 3 (NER, clustering), do you have preferred Python libraries (e.g., **spaCy** for NER, **scikit-learn** for clustering)?
I want to use spaCy and scikit-learn. Please note that resources may be written in English or Spanish, so the respective modules of spaCy must be installed.
3. **CSV/XLSX Content Model:** How should structured data from `.csv` and `.xlsx` files be handled?
'xlsx' files must be translated to 'csv'. All the cells must be stored in a single article.
4. **Processing Triggers:** How should the NLP processing jobs (Module 3) be triggered?
NLP jobs must be running automatically, following a given schedule. Note that some documents may be excluded from a given run (documents downloaded during the execution of the NLP job). The system must show the timestamp of the last NLP and cluster job execution.
