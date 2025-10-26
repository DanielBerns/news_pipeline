Understood. These are crucial administrative functions. We can add them to the specification as a new module focused on system management, which would likely be implemented as a set of command-line interface (CLI) scripts.

Here is the updated specification, now version 4.0, which includes your new requirements.

---

## Updated Software Specification (v4.0)

I am adding a new module to cover these administrative tasks.

### Module 4: Administration & Management (CLI)

This module defines tasks for the `Admin` role, intended to be run from the server's command line, not through the web application.

* **Story 20 (Database Init):** As an **`Admin`**, I want to run a single command (e.g., `python manage.py db_init`) that creates the database (if it doesn't exist) and all its tables, indexes, and relationships as defined in the data model.
* **Story 21 (Add User):** As an **`Admin`**, I want a CLI command to **create a new user** by providing a username, a password, and a role (`admin` or `data_analyst`).
* **Story 22 (Delete User):** As an **`Admin`**, I want a CLI command to **delete a user** by their username.
* **Story 23 (Add Source):** As an **`Admin`**, I want a CLI command to **add a new data source** by providing its `name`, `type` (RSS, URL, FILE), and `location` (the path or URL).
* **Story 24 (Toggle Source):** As an **`Admin`**, I want a CLI command to **block (deactivate)** or **unblock (reactivate)** a specific data source.

---

### Implementation Notes & Model Updates

Your new requirements have two important consequences:

**1. Consequence of Deleting a User (Story 22)**

We must decide what happens to a user's annotations when their account is deleted. When a user is deleted, their record is removed from the `User` table. This will affect the `Annotation` table.

* **Option A (Recommended):** We define the `user_id` foreign key in the `Annotation` table with `ON DELETE SET NULL`. This means when a user is deleted, all their annotations are kept, but they become "orphaned" (the `user_id` field becomes `NULL`). This preserves their work.
* **Option B (Destructive):** We use `ON DELETE CASCADE`. This means when a user is deleted, all annotations they ever made are **also permanently deleted**.

**Option A** is generally safer.

**2. Consequence of "Blocking" a Source (Story 24)**

To "block" a source, we need to modify the `Source` table to include a flag.

#### Updated Data Model (`Source` table)

* `Source`:
    * `source_id` (PK)
    * `name`
    * `type`
    * `location`
    * `last_run_timestamp`
    * **`is_active` (Boolean, default: true)**

The ingestion pipeline (Module 1) must be modified to **only fetch content from sources where `is_active` is `true`**. The CLI command (Story 24) will simply flip this flag between `true` and `false`.



#################################################################################

That's a much safer approach and a great refinement. Deactivating users (a "soft delete") is standard practice because it preserves all their historical data (like annotations) and allows you to reactivate them later if needed.

Here is the updated specification (v4.1) reflecting this change.

---

### Updated Specification (v4.1)

The main changes are in **Module 2 (Auth)**, **Module 4 (Admin CLI)**, and the **`User` Data Model**.

#### Module 2: The Content Application (Interaction)

* **Story 6 (Auth):** As a user, I want to log in with a username and password. The system must **only grant access if my account is marked as `is_active`**.
* ... (all other stories unchanged)

---

#### Module 4: Administration & Management (CLI)

* **Story 20 (Database Init):** (Unchanged) As an **`Admin`**, I want to run a single command... to create the database...
* **Story 21 (Add User):** (Unchanged) As an **`Admin`**, I want a CLI command to create a new user by providing a username, a password, and a role (`admin` or `data_analyst`).
* **Story 22 (Toggle User):** As an **`Admin`**, I want a CLI command to **deactivate (block)** or **reactivate (unblock)** a user by their username. This command will toggle their `is_active` status.
* **Story 23 (Add Source):** (Unchanged) As an **`Admin`**, I want a CLI command to add a new data source...
* **Story 24 (Toggle Source):** (Unchanged) As an **`Admin`**, I want a CLI command to block (deactivate) or unblock (reactivate) a specific data source...

---

### Updated Data Model (User Table)

This change simplifies the database logic, as we no longer need to worry about the `ON DELETE` behavior for annotations.

* `User`:
    * `user_id` (PK)
    * `username` (Unique)
    * `hashed_password`
    * `role` ('admin', 'data_analyst')
    * **`is_active` (Boolean, default: true)**

This means that when a user is deactivated, their `user_id` remains in the database, and all their existing annotations in the `Annotation` table remain perfectly intact and linked to them. They are simply blocked from logging in (Story 6).
