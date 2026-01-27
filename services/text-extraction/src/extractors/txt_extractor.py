"""
TXT Text Extractor

Extracts text from plain text files.
"""

import logging
from typing import Optional

from ..interfaces.text_extraction_service import TextExtractionService

logger = logging.getLogger(__name__)


class TXTExtractor(TextExtractionService):
    """Plain text file extraction."""

    def supports_format(self, content_type: str, filename: Optional[str] = None) -> bool:
        """Check if file is a plain text file."""
        return (
            content_type == 'text/plain' or
            (filename and filename.lower().endswith('.txt'))
        )

    def extract_text(self, file_data: bytes, content_type: str, filename: Optional[str] = None) -> str:
        """
        Extract text from plain text file.
        
        Args:
            file_data: Text file data as bytes
            content_type: MIME type (should be "text/plain")
            filename: Optional filename
            
        Returns:
            Text content
            
        Raises:
            ValueError: If file is not a text file or encoding fails
        """
        if not self.supports_format(content_type, filename):
            raise ValueError(f"Unsupported format: {content_type}")
        
        try:
            # Try UTF-8 first
            try:
                text = file_data.decode('utf-8')
            except UnicodeDecodeError:
                # Fall back to latin-1 (covers most cases)
                try:
                    text = file_data.decode('latin-1')
                except UnicodeDecodeError:
                    # Last resort: ignore errors
                    text = file_data.decode('utf-8', errors='ignore')
                    logger.warning(f"Text file {filename or 'unknown'} had encoding issues, some characters may be lost")
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text from TXT file: {e}")
            raise ValueError(f"Failed to extract text from TXT file: {str(e)}")
