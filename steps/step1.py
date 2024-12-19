from system_prompts import step1_system_prompt
from typing import Optional, List, Dict, Any
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
        model_name: str = None,
        max_tokens: int = 512,
        temperature: float = 0.7
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
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        else:
            prompt = tokenizer.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
            processed_text = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=prompt,
                max_tokens=max_tokens,
                temp=temperature,
            )
            return processed_text

    except Exception as e:
        raise ChunkProcessingError(f"Failed to process chunk {chunk_num}: {str(e)}")
    

# Main Step1 Function
def step1(
    pdf_path: str,
    model,
    tokenizer,
    client = None,
    config: Dict[Any, Any] = None,
    model_name: str = None,
    output_dir: str = None,
    chunk_size: int = 1000,
    max_chars: int = 100000,
) -> str:
    """
    Process PDF and generate clean text output.
    
    Args:
        pdf_path: Path to the input PDF file
        client: Initialized API client
        model_name: Name of the model to use for processing
        output_dir: Directory for output files
        chunk_size: Size of text chunks for processing
        max_chars: Maximum characters to process from PDF
        
    Returns:
        string of output_file_path
        
    Raises:
        PDFProcessingError: For any PDF processing related errors
        ChunkProcessingError: For text chunk processing errors
        OSError: For file system related errors
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get metadata (optional, won't stop processing if it fails)
        try:
            metadata = get_pdf_metadata(pdf_path)
            if metadata:
                logger.info(f"PDF Pages: {metadata['num_pages']}")
        except PDFExtractionError as e:
            logger.warning(f"Failed to extract metadata: {e}")

        # Extract text
        extracted_text = extract_text_from_pdf(pdf_path, max_chars)
        if not extracted_text:
            raise PDFExtractionError("No text extracted from PDF")

        # Save extracted text
        input_file = output_dir / 'extracted_text.txt'
        input_file.write_text(extracted_text, encoding='utf-8')

        # Process text in chunks
        chunks = create_word_bounded_chunks(extracted_text, chunk_size)
        output_file = output_dir / f"clean_{input_file.name}"
        
        logger.info(f"Processing {len(chunks)} chunks")
        
        with open(output_file, 'w', encoding='utf-8') as out_file:
            processed_text = ""
            for chunk_num, chunk in enumerate(tqdm(chunks, desc="Processing chunks", disable=None)):
                processed_chunk = process_chunk(
                    model,
                    tokenizer,
                    client,
                    chunk,
                    chunk_num,
                    step1_system_prompt,
                    model_name
                )
                processed_text += processed_chunk + "\n"
                out_file.write(processed_chunk + "\n")
                out_file.flush()

        logger.info("Processing complete")
        return str(output_file)

    except (PDFProcessingError, ChunkProcessingError) as e:
        logger.error(f"Processing failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during processing: {str(e)}")
        raise PDFProcessingError(f"PDF processing failed: {str(e)}")