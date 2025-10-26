#!/bin/bash

# ---
# A simple script to create a new "local_dir" source in the news_pipeline API.
#
# Usage:
# 1. Make it executable: chmod +x create_source.sh
# 2. Run it with the *absolute path* to your test files directory:
#    ./create_source.sh /home/user/my-test-notes
# ---

# Check if the path argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 /path/to/your/source/directory"
  echo "Please provide the *absolute path* to the directory you want to ingest."
  exit 1
fi

# --- Configuration ---
SOURCE_PATH="$1"
API_URL="http://127.0.0.1:8000/api/sources/"

# You can change the name and description here
SOURCE_NAME="My Local Test Notes"
SOURCE_KIND="local"
SOURCE_PATH="~/Info/news_pipeline/alpha"
SOURCE_DESC="A test source for ingesting local .txt and .md files from $SOURCE_PATH"

# --- Create JSON Payload ---
# We use printf to safely build the JSON string,
# which handles potential special characters in the path.
JSON_PAYLOAD=$(printf '{
  "name": "%s",
  "kind": "%s",
  "location": "%s",
  "config": {
    "created_by_script": "create_source.sh",
    "description": "%s"
  }
}' "$SOURCE_NAME" "$SOURCE_KIND" "$SOURCE_PATH" "$SOURCE_DESC")

# --- Send the Request ---
echo "Attempting to create source at: $API_URL"
echo "Payload:"
echo "$JSON_PAYLOAD"
echo "---"

curl -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -d "$JSON_PAYLOAD"

# Add a final newline for cleaner terminal output
echo
