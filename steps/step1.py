from typing import Optional, List, Tuple
from pathlib import Path
from tqdm import tqdm
import logging
import PyPDF2
import os

logger = logging.getLogger(__name__)

class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""
    pass
class PDFValidationError(PDFProcessingError):
    """Exception raised for PDF validation issues."""
    pass
class PDFExtractionError(PDFProcessingError):
    """Exception raised for text extraction issues."""
    pass
class ChunkProcessingError(PDFProcessingError):
    """Exception raised for chunk processing issues."""
    pass