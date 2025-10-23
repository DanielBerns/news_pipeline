echo "Running flake8..."
uv run flake8 ./src/news_pipeline --count --select=E9,F63,F7,F82 --show-source --statistics
echo "Running Black (check)..."
uv run black ./src/news_pipeline --check
# echo "Running Black (check)..."
# uv run pytest
