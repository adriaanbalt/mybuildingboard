"""
PDF Text Extractor

Extracts text from PDF files using PyMuPDF (fitz).
"""

import logging
from typing import Optional
import fitz  # PyMuPDF

from ..interfaces.text_extraction_service import TextExtractionService

logger = logging.getLogger(__name__)


class PDFExtractor(TextExtractionService):
    """PDF text extraction using PyMuPDF."""

    def supports_format(self, content_type: str, filename: Optional[str] = None) -> bool:
        """Check if file is a PDF."""
        return (
            content_type == 'application/pdf' or
            (filename and filename.lower().endswith('.pdf'))
        )

    def extract_text(self, file_data: bytes, content_type: str, filename: Optional[str] = None) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_data: PDF file data as bytes
            content_type: MIME type (should be "application/pdf")
            filename: Optional filename
            
        Returns:
            Extracted text from all pages
            
        Raises:
            ValueError: If file is not a PDF or is corrupted
        """
        if not self.supports_format(content_type, filename):
            raise ValueError(f"Unsupported format: {content_type}")
        
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=file_data, filetype="pdf")
            
            text_parts = []
            
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text:
                    text_parts.append(text)
            
            doc.close()
            
            # Join all pages with newlines
            full_text = '\n\n'.join(text_parts)
            
            if not full_text.strip():
                logger.warning(f"PDF {filename or 'unknown'} appears to be empty or image-based")
            
            return full_text
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
