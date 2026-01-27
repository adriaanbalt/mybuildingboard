"""
DOC Text Extractor

Extracts text from legacy DOC files using LibreOffice conversion.
"""

import logging
import subprocess
import tempfile
import os
from typing import Optional

from ..interfaces.text_extraction_service import TextExtractionService

logger = logging.getLogger(__name__)


class DOCExtractor(TextExtractionService):
    """DOC text extraction using LibreOffice conversion."""

    def supports_format(self, content_type: str, filename: Optional[str] = None) -> bool:
        """Check if file is a DOC file."""
        return (
            content_type == 'application/msword' or
            (filename and filename.lower().endswith('.doc'))
        )

    def extract_text(self, file_data: bytes, content_type: str, filename: Optional[str] = None) -> str:
        """
        Extract text from DOC file by converting to text using LibreOffice.
        
        Args:
            file_data: DOC file data as bytes
            content_type: MIME type (should be "application/msword")
            filename: Optional filename
            
        Returns:
            Extracted text
            
        Raises:
            ValueError: If file is not a DOC or conversion fails
        """
        if not self.supports_format(content_type, filename):
            raise ValueError(f"Unsupported format: {content_type}")
        
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.doc', delete=False) as input_file:
                input_file.write(file_data)
                input_file_path = input_file.name
            
            output_dir = tempfile.mkdtemp()
            output_file_path = os.path.join(output_dir, 'output.txt')
            
            try:
                # Convert DOC to TXT using LibreOffice
                # libreoffice --headless --convert-to txt --outdir <output_dir> <input_file>
                result = subprocess.run(
                    [
                        'libreoffice',
                        '--headless',
                        '--convert-to', 'txt',
                        '--outdir', output_dir,
                        input_file_path
                    ],
                    capture_output=True,
                    timeout=60,
                    check=True
                )
                
                # Read converted text file
                if os.path.exists(output_file_path):
                    with open(output_file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                else:
                    # Try to find the output file (LibreOffice may change the name)
                    txt_files = [f for f in os.listdir(output_dir) if f.endswith('.txt')]
                    if txt_files:
                        with open(os.path.join(output_dir, txt_files[0]), 'r', encoding='utf-8') as f:
                            text = f.read()
                    else:
                        raise ValueError("LibreOffice conversion did not produce output file")
                
                return text
                
            finally:
                # Cleanup
                try:
                    os.unlink(input_file_path)
                except:
                    pass
                try:
                    for f in os.listdir(output_dir):
                        os.unlink(os.path.join(output_dir, f))
                    os.rmdir(output_dir)
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            logger.error("LibreOffice conversion timed out")
            raise ValueError("DOC conversion timed out")
        except subprocess.CalledProcessError as e:
            logger.error(f"LibreOffice conversion failed: {e.stderr.decode() if e.stderr else str(e)}")
            raise ValueError(f"Failed to convert DOC file: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to extract text from DOC: {e}")
            raise ValueError(f"Failed to extract text from DOC: {str(e)}")
