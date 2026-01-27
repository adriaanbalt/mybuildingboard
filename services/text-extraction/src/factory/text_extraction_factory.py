"""
Text Extraction Factory

Creates text extraction service instances based on file format.
"""

from typing import Optional
from ..interfaces.text_extraction_service import TextExtractionService
from ..extractors.pdf_extractor import PDFExtractor
from ..extractors.docx_extractor import DOCXExtractor
from ..extractors.doc_extractor import DOCExtractor
from ..extractors.image_extractor import ImageExtractor
from ..extractors.txt_extractor import TXTExtractor


class TextExtractionFactory:
    """
    Factory for creating text extraction service instances.
    
    Automatically selects the appropriate extractor based on file format.
    """

    def __init__(self):
        """Initialize factory with all available extractors."""
        self.extractors = [
            PDFExtractor(),
            DOCXExtractor(),
            DOCExtractor(),
            ImageExtractor(),
            TXTExtractor(),
        ]

    def get_extractor(self, content_type: str, filename: Optional[str] = None) -> TextExtractionService:
        """
        Get appropriate extractor for the given file format.
        
        Args:
            content_type: MIME type of the file
            filename: Optional filename
            
        Returns:
            TextExtractionService instance
            
        Raises:
            ValueError: If no extractor supports the format
        """
        for extractor in self.extractors:
            if extractor.supports_format(content_type, filename):
                return extractor
        
        raise ValueError(f"No extractor available for format: {content_type}")

    def extract_text(self, file_data: bytes, content_type: str, filename: Optional[str] = None) -> str:
        """
        Extract text from file using appropriate extractor.
        
        Args:
            file_data: File data as bytes
            content_type: MIME type of the file
            filename: Optional filename
            
        Returns:
            Extracted text
            
        Raises:
            ValueError: If format is unsupported or extraction fails
        """
        extractor = self.get_extractor(content_type, filename)
        return extractor.extract_text(file_data, content_type, filename)
