import chardet
from pathlib import Path
from typing import List
from .base import Parser, ParsedArticle

class TextParser(Parser):
    """
    Parses plain text (.txt) and Markdown (.md) files.

    It attempts to find a title in this order:
    1. A markdown H1 heading ('# Title') on the first line.
    2. The filename (with '-' and '_' replaced by spaces).
    """

    def parse(self, file_path: Path) -> ParsedArticle:
        """
        Reads a text file, detects its encoding, and extracts content.
        """
        # 1. Detect encoding
        with file_path.open("rb") as f:
            raw_data = f.read()

        detected = chardet.detect(raw_data)
        encoding = detected["encoding"] or "utf-8" # Default to utf-8

        try:
            content = raw_data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            # Fallback on 'latin-1' if chardet fails or is wrong
            encoding = "latin-1"
            content = raw_data.decode(encoding)

        lines = content.splitlines()

        # 2. Extract title
        title = ""
        content_start_line = 0

        if lines and lines[0].startswith("# "):
            # Found a markdown H1 title
            title = lines[0][2:].strip()
            content_start_line = 1 # Content starts from the next line
        else:
            # Use filename as fallback title
            title = file_path.stem.replace("-", " ").replace("_", " ").title()

        # 3. Extract content
        content_text = "\n".join(lines[content_start_line:]).strip()

        # 4. Create attributes
        attributes = {
            "source_filename": file_path.name,
            "detected_encoding": encoding,
        }

        return {
            "title": title,
            "content_text": content_text,
            "attributes": attributes,
        }

    def get_supported_extensions(self) -> List[str]:
        """Returns the extensions this parser handles."""
        return [".txt", ".md"]
