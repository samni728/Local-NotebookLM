from system_prompts import step3_system_prompt
from typing import Dict, Any
from ast import literal_eval
from mlx_lm import generate
from pathlib import Path
import logging
import pickle

logger = logging.getLogger(__name__)

class TranscriptError(Exception):
    """Base exception for transcript processing errors."""
    pass

class FileReadError(TranscriptError):
    """Exception raised for file reading issues."""
    pass

class TranscriptGenerationError(TranscriptError):
    """Exception raised for transcript generation issues."""
    pass

class InvalidParameterError(TranscriptError):
    """Exception raised for invalid parameter values."""
    pass

def read_pickle_file(filename: str) -> str:
    """Read input from pickle file."""
    try:
        with open(filename, 'rb') as file:
            content = pickle.load(file)
        return content
    except FileNotFoundError:
        raise FileReadError(f"File '{filename}' not found")
    except Exception as e:
        raise FileReadError(f"Failed to read pickle file: {str(e)}")

def generate_rewritten_transcript(
    model,
    tokenizer,
    client = None,
    model_name: str = None,
    input_text: str = None,
    max_tokens: int = 8126,
    temperature: float = 1
) -> str:
    """Generate rewritten podcast transcript using the model."""
    try:
        conversation = [
            {"role": "system", "content": step3_system_prompt},
            {"role": "user", "content": input_text},
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
        raise TranscriptGenerationError(f"Failed to generate transcript: {str(e)}")

def validate_transcript_format(transcript: str) -> bool:
    """Validate if the transcript is in the correct format."""
    try:
        data = literal_eval(transcript)
        if not isinstance(data, list):
            return False
        for item in data:
            if not isinstance(item, tuple) or len(item) != 2:
                return False
            if not isinstance(item[0], str) or not isinstance(item[1], str):
                return False
        return True
    except:
        return False

# Main Step3 Function
def step3(
    model,
    tokenizer,
    client = None,
    config: Dict[Any, Any] = None,
    input_file: str = None,
    model_name: str = None,
    output_dir: str = None
) -> str:
    """
    Rewrite podcast transcript for TTS pipeline.
    
    Args:
        client: Initialized API client
        input_file: Path to the input pickle file
        length: Desired transcript length ("short", "medium", "long", "very-long")
        style: Desired transcript style ("friendly", "professional", "academic", "casual", "technical", "funny")
        model_name: Name of the model to use
        output_dir: Directory for output files
        
    Returns:
        Tuple of (input_file_path, output_file_path)
        
    Raises:
        TranscriptError: For any transcript processing related errors
        InvalidParameterError: For invalid length or style parameters
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read input file
        logger.info(f"Reading input file: {input_file}")
        input_text = read_pickle_file(input_file)

        # Generate rewritten transcript
        logger.info(f"Generating rewritten transcript...")
        transcript = generate_rewritten_transcript(
            model = model,
            tokenizer = tokenizer,
            client = client,
            model_name = config.get('model_name', model_name),
            input_text = input_text,
            max_tokens = config.get('max_tokens', 8126),
            temperature = config.get('temperature', 1)
        )

        # Validate transcript format
        if not validate_transcript_format(transcript):
            raise TranscriptGenerationError("Generated transcript is not in the correct format")

        # Save transcript
        output_file = output_dir / 'podcast_ready_data.pkl'
        with open(output_file, 'wb') as file:
            pickle.dump(transcript, file)

        logger.info(f"Rewritten transcript saved to: {output_file}")
        return str(input_file), str(output_file)

    except (FileReadError, TranscriptGenerationError, InvalidParameterError) as e:
        logger.error(f"Transcript rewriting failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during transcript rewriting: {str(e)}")
        raise TranscriptError(f"Transcript rewriting failed: {str(e)}")