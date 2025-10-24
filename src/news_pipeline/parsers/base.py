import abc
from pathlib import Path
from typing import List, TypedDict

# This TypedDict defines the standard, canonical output
# that all parsers must return.
class ParsedArticle(TypedDict):
    """The canonical dictionary format for a parsed article."""
    title: str
    content_text: str
    attributes: dict

class Parser(metaclass=abc.ABCMeta):
    """
    Abstract Base Class for all content parsers.

    A parser is responsible for taking a file, extracting its
    content, and returning it in the canonical ParsedArticle format.
    """

    @abc.abstractmethod
    def parse(self, file_path: Path) -> ParsedArticle:
        """
        Parses a single file.

        Args:
            file_path: A Path object pointing to the file to be parsed.

        Returns:
            A ParsedArticle dictionary.
        """
        pass

    @abc.abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Returns a list of file extensions this parser supports.

        Example: [".txt", ".md"]

        Returns:
            List of lowercase file extensions (including the dot).
        """
        pass
