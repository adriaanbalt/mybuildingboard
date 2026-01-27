"""
TextExtractionService Interface

Provider-agnostic interface for text extraction services.
"""

from typing import Optional
from abc import ABC, abstractmethod


class TextExtractionService(ABC):
    """
    Abstract interface for text extraction services.
    
    All text extraction providers must implement this interface.
    """

    @abstractmethod
    def extract_text(self, file_data: bytes, content_type: str, filename: Optional[str] = None) -> str:
        """
        Extract text from a file.
        
        Args:
            file_data: File data as bytes
            content_type: MIME type of the file (e.g., "application/pdf", "image/png")
            filename: Optional filename (useful for format detection)
            
        Returns:
            Extracted text as string
            
        Raises:
            ValueError: If file format is unsupported
            Exception: If extraction fails
        """
        pass

    @abstractmethod
    def supports_format(self, content_type: str, filename: Optional[str] = None) -> bool:
        """
        Check if the service supports the given file format.
        
        Args:
            content_type: MIME type of the file
            filename: Optional filename
            
        Returns:
            True if format is supported, False otherwise
        """
        pass
