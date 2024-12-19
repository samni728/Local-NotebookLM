from typing import Optional, List
from mlx_lm import generate
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


# PDF Processing Functions
def validate_pdf(file_path: str) -> bool:
    """Validate if the file exists and is a PDF."""
    if not os.path.exists(file_path):
        raise PDFValidationError(f"File not found at path: {file_path}")
    if not file_path.lower().endswith('.pdf'):
        raise PDFValidationError("File is not a PDF")
    return True

def get_pdf_metadata(file_path: str) -> Optional[dict]:
    """Extract metadata from PDF file."""
    try:
        if not validate_pdf(file_path):
            return None

        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata = {
                'num_pages': len(pdf_reader.pages),
                'metadata': pdf_reader.metadata
            }
            return metadata
    except PDFValidationError as e:
        raise e
    except Exception as e:
        raise PDFExtractionError(f"Failed to extract metadata: {str(e)}")

def extract_text_from_pdf(file_path: str, max_chars: int = 100000) -> str:
    """Extract text content from PDF file."""
    try:
        if not validate_pdf(file_path):
            return None

        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            logger.info(f"Processing PDF with {num_pages} pages")

            extracted_text = []
            total_chars = 0

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()

                if total_chars + len(text) > max_chars:
                    remaining_chars = max_chars - total_chars
                    extracted_text.append(text[:remaining_chars])
                    logger.info(f"Reached {max_chars} character limit at page {page_num + 1}")
                    break

                extracted_text.append(text)
                total_chars += len(text)
                logger.debug(f"Processed page {page_num + 1}/{num_pages}")

            final_text = '\n'.join(extracted_text)
            logger.info(f"Extraction complete. Total characters: {len(final_text)}")
            return final_text

    except PDFValidationError as e:
        raise e
    except PyPDF2.PdfReadError as e:
        raise PDFExtractionError(f"Invalid or corrupted PDF file: {str(e)}")
    except Exception as e:
        raise PDFExtractionError(f"Failed to extract text: {str(e)}")


# Chunk Processing Functions
def create_word_bounded_chunks(text: str, target_chunk_size: int) -> List[str]:
    """Split text into chunks at word boundaries."""
    try:
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for the space
            if current_length + word_length > target_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks
    except Exception as e:
        raise ChunkProcessingError(f"Failed to create text chunks: {str(e)}")

def process_chunk(
        model,
        tokenizer,
        client = None,
        text_chunk: str = None,
        chunk_num: int = None,
        sys_prompt: str = None,
        model_name: str = None
    ) -> str:
    """Process a chunk of text using the API client or a local mlx-model."""
    try:
        conversation = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": text_chunk},
        ]

        if client is not None:
            response = client.chat.completions.create(
                model=model_name,
                messages=conversation,
                max_tokens=512,
                temperature=0.7,
            )
            return response.choices[0].message.content
        else:
            prompt = tokenizer.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
            processed_text = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=prompt,
                max_tokens=512,
                temp=0.7,
            )
            return processed_text

    except Exception as e:
        raise ChunkProcessingError(f"Failed to process chunk {chunk_num}: {str(e)}")