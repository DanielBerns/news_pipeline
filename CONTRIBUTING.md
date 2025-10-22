# How to Contribute to This Project

First off, thank you for considering contributing! We're excited to have your help. This project is a community effort, and every contribution, from a small typo fix to a new feature, is valuable.

This document outlines our guidelines for contributing. Following them helps us keep the project high-quality and makes the review process smoother for everyone.

## Table of Contents

* [Code of Conduct](#code-of-conduct)
* [How Can I Contribute?](#how-can-i-contribute)
    * [Reporting Bugs](#reporting-bugs)
    * [Suggesting Enhancements](#suggesting-enhancements)
    * [Finding an Issue to Work On](#finding-an-issue-to-work-on)
* [Local Development Setup](#local-development-setup)
* [Development Workflow](#development-workflow)
    * [1. Create a Branch](#1-create-a-branch)
    * [2. Make Your Changes](#2-make-your-changes)
    * [3. Write Good Commit Messages](#3-write-good-commit-messages)
    * [4. Run Quality Checks](#4-run-quality-checks)
    * [5. Handle Database Migrations](#5-handle-database-migrations)
    * [6. Submit a Pull Request](#6-submit-a-pull-request)
* [Pull Request Review Process](#pull-request-review-process)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please take a moment to read it. We are committed to providing a welcoming and harassment-free environment for all.

## How Can I Contribute?

### Reporting Bugs

Bugs are tracked as [GitHub Issues](https://github.com/your-org/your-repo/issues). If you find a bug, please search the existing issues to see if it's already been reported.

If you're opening a new issue, please use the **"Bug Report" template** and include:
* A clear, descriptive title (e.g., "API crashes with 500 error when ingesting empty PDF").
* Steps to reproduce the bug, as clearly as possible.
* The expected behavior (what you thought *should* happen).
* The actual behavior (what *did* happen, including any error messages and stack traces).
* Your local environment (OS, Python version, Docker version, etc.).

### Suggesting Enhancements

If you have an idea for a new feature or an improvement, please search the [GitHub Issues](https://github.com/your-org/your-repo/issues) to see if it's already being discussed.

If not, please open a new issue using the **"Feature Request" template**, describing:
* **The Problem:** What problem are you trying to solve? (e.g., "I can't tell which articles have been processed by NER.")
* **The Solution:** A clear description of the solution you'd like to see.
* **Alternatives:** Any alternative solutions or features you've considered.

### Finding an Issue to Work On

New to the project? A great way to start is by looking for issues labeled `good first issue` or `help wanted` in our [Issues tab](https://github.com/your-org/your-repo/issues). These are tasks that we've identified as good entry points for new contributors.

Feel free to comment on an issue to ask questions or to let us know you'd like to work on it!

## Local Development Setup

To get your local environment set up for development, please follow the steps in our main [README.md](./README.md) file. The short version is:

1.  **Fork & Clone:** Fork the repository to your own GitHub account and clone it locally.
    ```bash
    git clone [https://github.com/YOUR-USERNAME/your-repo.git](https://github.com/YOUR-USERNAME/your-repo.git)
    cd your-repo
    ```
2.  **Add Upstream Remote:** This lets you pull in changes from the main project.
    ```bash
    git remote add upstream [https://github.com/your-org/your-repo.git](https://github.com/your-org/your-repo.git)
    ```
3.  **Install:** Run `make install-dev`. This uses `uv` to create a virtual environment (`.venv`) and sync all dependencies from `pyproject.toml`.
4.  **Start Services:** Run `make dev-services`. This starts the PostgreSQL and Redis containers via Docker Compose.
5.  **Run Migrations:** Run `make db-upgrade` to apply the database schema.

You are now ready to start development!

## Development Workflow

### 1. Create a Branch

First, make sure your `main` branch is up-to-date:
```bash
git checkout main
git pull upstream main
```

### 2\. Make Your Changes

This is the creative part\! As you write your code, please keep these guidelines in mind:

  * **Follow Existing Style:** Try to match the coding style and patterns you see elsewhere in the project. Consistency is key.
  * **Keep Changes Focused:** A pull request should do *one thing* well. Don't mix a bug fix with a new feature and a refactor. Create separate branches and PRs for separate concerns. This makes reviewing much faster and easier.
  * **Write Tests:** New code means new tests.
      * If you add a **new feature**, add new unit or integration tests that prove it works correctly.
      * If you fix a **bug**, add a test that *fails* before your change and *passes* after. This prevents the bug from ever coming back (this is called a "regression test").
  * **Update Documentation:** If your change affects how a user or developer interacts with the project, please update the relevant documentation (like the `README.md` or API docs).

-----

### 3\. Write Good Commit Messages

Clear commit messages are essential for understanding the project's history. We follow a convention for our commit messages.

**Format:** `type: short description`

Please start your commit message with one of the following types:

  * **`feat`**: A new feature (e.g., `feat: add pdf parser with ocr fallback`)
  * **`fix`**: A bug fix (e.g., `fix: resolve divide-by-zero error in clustering`)
  * **`docs`**: Changes to documentation only (e.g., `docs: update contributing guide for commit messages`)
  * **`style`**: Formatting changes, (e.g., `style: run black on app/parsers`)
  * **`refactor`**: Code changes that neither fix a bug nor add a feature (e.g., `refactor: extract ner logic into its own service`)
  * **`test`**: Adding missing tests or correcting existing tests (e.g., `test: add unit tests for text parser`)
  * **`chore`**: General maintenance, like updating dependencies or CI config (e.g., `chore: upgrade sqlalchemy to 2.0`)

**Body of the commit (Optional):**

For more significant changes, add a blank line after the subject and write a more detailed explanation.

```
fix: correct handling of empty CSV files during ingest

Previously, an empty CSV file would cause the ingestion pipeline to
crash with an unhandled `EmptyDataError`.

This commit adds a check at the beginning of the CSV parser to
verify the file is not empty before attempting to read it.
```

-----

### 4\. Run Quality Checks

Before you submit your code, you **must** run our quality checks. Our CI (Continuous Integration) system will run these checks anyway, so running them locally first saves time.

#### Code Style & Formatting

We use **Black** for consistent code formatting and **Flake8** for linting (finding potential bugs or style errors).

```bash
# This will automatically format all your code.
make format

# This will check for any remaining style or logic errors.
make lint
```

**Your PR will be blocked from merging if `make lint` does not pass.**

#### Running Tests

We have two main test suites. All tests MUST pass.

```bash
# Run the fast unit tests (no DB or services needed)
make test-unit

# Run the integration tests (requires Docker services to be running)
make test-integration

# Or, to run everything at once:
make test-all
```

-----

### 5\. Handle Database Migrations

If your changes involve modifying a SQLAlchemy model in `app/models.py` (e.g., adding a new column or table), you **must** generate a new database migration file using Alembic.

```bash
# 1. This will ask you for a message and auto-generate the migration
#    Example message: "add last_run_timestamp to articles table"
make db-migrate

# 2. Apply your new migration to your local database to test it
make db-upgrade
```

Please **commit the new migration file** (it will be in `alembic/versions/`) along with your other code changes. Do *not* combine model changes and migration generation in the same commit.

**Good commit flow:**

1.  `refactor: add processed_at column to Article model` (Commit your model change)
2.  `chore: generate migration for processed_at column` (Commit the new migration file)

-----

### 6\. Submit a Pull Request

Once your changes are ready, tested, and linted:

1.  **Commit** your changes: `git commit -m "feat: my new feature"`
2.  **Push** your branch to your fork: `git push origin feature/my-new-feature`
3.  Go to the original project repository on GitHub.
4.  You should see a prompt to **"Compare & pull request"**. Click it.
5.  Fill out the **Pull Request (PR) template**.
      * **Title:** Use the same convention as your commit messages (e.g., `feat: add pdf parser`).
      * **Description:** Clearly describe *what* your PR does and *why* it's needed.
      * **Link Issues:** Link any GitHub Issues your PR resolves (e.g., "Closes \#123"). This automatically closes the issue when the PR is merged.

-----

## Pull Request Review Process

1.  **CI Checks:** As soon as you open your PR, our GitHub Actions workflow will automatically run. It will check your code (`make lint`) and run all tests (`make test-all`). All checks must pass (turn green). If they fail, look at the "Details" link to see the logs, fix the issue on your branch, and push the changes.
2.  **Code Review:** One or more project maintainers will review your code. We may ask for changes, suggest improvements, or ask questions. This is a normal and healthy part of the contribution process\! Please don't be discouraged.
3.  **Approval & Merge:** Once your PR is approved by a maintainer and all CI checks are passing, a maintainer will **merge** it into the `main` branch.

And that's it\! Thank you for your contribution\! 🎉
