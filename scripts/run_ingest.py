import sys
from sqlalchemy.orm import Session
from news_pipeline.database import SessionLocal
from news_pipeline.pipeline.ingest import ingest_source

def main():
    """
    A simple script to run the ingestion pipeline for a source.
    """
    if len(sys.argv) < 2:
        print("Usage: python run_ingest.py <source_id>")
        sys.exit(1)

    try:
        source_id = int(sys.argv[1])
    except ValueError:
        print("Error: <source_id> must be an integer.")
        sys.exit(1)

    print(f"Connecting to database...")
    db: Session = SessionLocal()

    try:
        ingest_source(source_id=source_id, db=db)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
    finally:
        print("Closing database connection.")
        db.close()

if __name__ == "__main__":
    main()

