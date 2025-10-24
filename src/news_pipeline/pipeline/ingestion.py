import sys
from pathlib import Path
from typing import Dict, Type, List
from sqlalchemy.orm import Session

# Import from parent directories using '..'
from .. import crud, schemas, models
from ..parsers.base import Parser
from ..parsers.text_parser import TextParser

# --- Parser Registry ---
# This list holds all available parser classes.
# When you add a new parser (e.g., PdfParser), just add it here.
ALL_PARSERS: List[Type[Parser]] = [
    TextParser,
]

def get_parser_registry() -> Dict[str, Type[Parser]]:
    """
    Creates a mapping from file extensions to parser classes.

    Returns:
        A dict like {".txt": TextParser, ".md": TextParser}
    """
    registry = {}
    for parser_class in ALL_PARSERS:
        # We instantiate the class just to call get_supported_extensions()
        # This is lightweight as __init__ does nothing.
        parser_instance = parser_class()
        for ext in parser_instance.get_supported_extensions():
            if ext in registry:
                print(f"Warning: Overwriting parser for extension '{ext}'", file=sys.stderr)
            registry[ext] = parser_class
    return registry
# --- End of Parser Registry ---


def ingest_source(source_id: int, db: Session):
    """
    Runs the ingestion pipeline for a single source.

    For this increment, it treats the source.url as a
    local file path or directory.
    """
    print(f"--- Starting ingestion for source_id: {source_id} ---")

    # 1. Get Source from DB
    source = crud.get_source(db, source_id=source_id)
    if not source:
        print(f"Error: Source with id {source_id} not found.", file=sys.stderr)
        return

    print(f"Ingesting source: '{source.name}' from location: {source.url}")

    # 2. Get Parser Registry
    parser_registry = get_parser_registry()
    if not parser_registry:
        print("Error: No parsers are registered.", file=sys.stderr)
        return
    print(f"Loaded {len(parser_registry)} parser extensions: {list(parser_registry.keys())}")

    # 3. Find files
    source_path = Path(source.url)
    if not source_path.exists():
        print(f"Error: Source path does not exist: {source_path}", file=sys.stderr)
        return

    files_to_process: List[Path] = []
    if source_path.is_file():
        files_to_process.append(source_path)
    elif source_path.is_dir():
        # Use rglob to find all files recursively
        files_to_process = list(source_path.rglob("*.*"))

    print(f"Found {len(files_to_process)} potential files.")

    # 4. Loop, Parse, and Store
    articles_created_count = 0
    articles_skipped_count = 0

    for file_path in files_to_process:
        file_ext = file_path.suffix.lower()

        # 4a. Find parser
        if file_ext not in parser_registry:
            # No parser for this file type, skip it
            continue

        # 4b. Check for idempotency (has it been ingested already?)
        # We use the full file path as a unique 'source_url' for the article
        file_url_str = str(file_path.resolve())
        existing_article = crud.get_article_by_source_url(db, source_url=file_url_str)

        if existing_article:
            articles_skipped_count += 1
            continue

        # 4c. Parse the file
        print(f"Parsing: {file_path.name}")
        try:
            ParserClass = parser_registry[file_ext]
            parser = ParserClass() # Instantiate the specific parser
            parsed_data = parser.parse(file_path)

            # 4d. Create Article schema
            article_in = schemas.ArticleCreate(
                title=parsed_data["title"],
                content=parsed_data["content_text"],
                source_url=file_url_str, # Use resolved path as unique ID
                metadata=parsed_data["metadata"],
            )

            # 4e. Save to DB
            crud.create_article(db=db, article=article_in, source_id=source.id)
            articles_created_count += 1

        except Exception as e:
            print(f"Failed to parse or save '{file_path.name}': {e}", file=sys.stderr)

    print(f"--- Ingestion complete ---")
    print(f"New articles created: {articles_created_count}")
    print(f"Articles skipped (already exist): {articles_skipped_count}")
