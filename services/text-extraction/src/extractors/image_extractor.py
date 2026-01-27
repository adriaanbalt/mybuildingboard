"""
Image OCR Text Extractor

Extracts text from images using pytesseract OCR.
"""

import logging
from typing import Optional
from io import BytesIO
from PIL import Image
import pytesseract

from ..interfaces.text_extraction_service import TextExtractionService

logger = logging.getLogger(__name__)


class ImageExtractor(TextExtractionService):
    """Image OCR text extraction using pytesseract."""

    SUPPORTED_FORMATS = {
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/gif',
        'image/bmp',
        'image/tiff',
    }

    def supports_format(self, content_type: str, filename: Optional[str] = None) -> bool:
        """Check if file is a supported image format."""
        return (
            content_type.lower() in self.SUPPORTED_FORMATS or
            (filename and any(filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']))
        )

    def extract_text(self, file_data: bytes, content_type: str, filename: Optional[str] = None) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            file_data: Image file data as bytes
            content_type: MIME type (e.g., "image/png")
            filename: Optional filename
            
        Returns:
            Extracted text from image
            
        Raises:
            ValueError: If file is not a supported image format or OCR fails
        """
        if not self.supports_format(content_type, filename):
            raise ValueError(f"Unsupported format: {content_type}")
        
        try:
            # Open image from bytes
            image = Image.open(BytesIO(file_data))
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            if not text.strip():
                logger.warning(f"Image {filename or 'unknown'} appears to contain no text")
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from image: {e}")
            raise ValueError(f"Failed to extract text from image: {str(e)}")
