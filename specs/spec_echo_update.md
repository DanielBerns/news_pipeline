### New Requirements: ORM and YAML Config

1.  **Gap (ORM):** The spec defines the *SQL model* but not the *application-layer* model. You want to use an **ORM**.
    * I want the **Backend (Core):** implemented as a FastAPI application, with a **SQLAlchemy** ORM to manage the database

2.  Add a new **Non-Functional Requirement (NFR)**: * `NFR 7 (Configuration):` All application settings, including database connections, source locations, and queue credentials, must be managed externally via **YAML configuration files**.

---

### Potential Gaps and Conflicts

#### 1. Conflict: "On-Demand" vs. "Asynchronous" Jobs

There is a direct conflict between one user story and a core non-functional requirement.

* **Story 16 (View Word Cloud):** States a Data Analyst can generate a word cloud **"on-demand"**.
* **NFR 3 (Asynchronous Processing):** States "All Module 3 NLP jobs **must** run as asynchronous background tasks."

Please, modify **Story 16** to be an asynchronous request. The user clicks "Generate Word Cloud," this creates a task for the **Celery** queue, and the UI updates when the result is ready. This aligns with NFR 3.

---

#### 2. Ambiguity: CSV/Excel Data Transformation (Story 3a)

* **Story 3a:** "For `.csv` and converted `.xlsx` files, all cells in the file must be **concatenated into a single text block** and stored in the `content_text` field of *one* `Article` entity."

Please, change the specification and consider 1 row = 1 Article.


---

#### 3. Missing: Testing and Security Strategies

The spec is missing two major NFR categories:

* **Gap (Testing):** There is no mention of a testing strategy. This is a critical gap. How will you ensure the parsers work, the NLP jobs are accurate, and the API is secure?
    * Please, add a section for NFRs related to testing (e.g., "The system must have >80% unit test coverage," "All pipeline parsers must have integration tests," "UI tests must cover the login and search workflows").
* **Gap (Security):** The spec mentions `hashed_password` (good) but has no other security requirements.
    * Please, add NFRs for security. (e.g., "All web application endpoints must be secured, requiring an authenticated session," "The system must use SSL/TLS in production," "Admin CLI scripts must require authenticated credentials").

---

#### 4. Missing: Data Model Details

The relational model is well-defined, but it's missing database-level logic.

* **Gap (Foreign Key Behavior):** The model defines Foreign Keys (FKs) but doesn't specify cascade rules. For example, if an `Article` is deleted, what should happen to its related `Annotation`s and `ArticleEntity` records?
    * Please, define the `ON DELETE` behavior for key relationships. For example, deleting an `Article` should probably cascade-delete all its child records in `Annotation`, `ArticleEntity`, and `ArticleCluster`.

---

