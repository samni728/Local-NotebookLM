from helpers import TranscriptLength, TranscriptStyle
from system_prompts import map_step2_and_3_system_prompt
from typing import Any, Dict
from mlx_lm import generate
from pathlib import Path
import logging
import pickle

logger = logging.getLogger(__name__)

# Set up logging
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

# Step 2 Helper Functions
def read_input_file(filename: str) -> str:
    """Read input file with multiple encoding attempts."""
    try:
        # Try UTF-8 first
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except UnicodeDecodeError:
        # Try other encodings
        encodings = ['latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(filename, 'r', encoding=encoding) as file:
                    content = file.read()
                logger.info(f"Successfully read file using {encoding} encoding")
                return content
            except UnicodeDecodeError:
                continue
        raise FileReadError(f"Could not decode file '{filename}' with any common encoding")
    except FileNotFoundError:
        raise FileReadError(f"File '{filename}' not found")
    except IOError as e:
        raise FileReadError(f"Could not read file '{filename}': {str(e)}")

# Generate Transcript Function
def generate_transcript(
    model,
    tokenizer,
    client = None,
    model_name: str = None,
    input_text: str = None,
    length: TranscriptLength = None,
    style: TranscriptStyle = None,
    max_tokens: int = 8126,
    temperature: float = 1
) -> str:
    """Generate podcast transcript using the model."""
    try:
        conversation = [
            {"role": "system", "content": map_step2_and_3_system_prompt(length, style)},
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

# Main Step2 Function
def step2(
    model,
    tokenizer,
    client = None,
    config: Dict[Any, Any] = None,
    input_file: str = None,
    length: TranscriptLength = "medium",
    style: TranscriptStyle = "academic",
    model_name: str = None,
    output_dir: str = None
) -> str:
    """
    Process cleaned text into a podcast transcript.
    
    Args:
        client: Initialized API client
        input_file: Path to the input text file
        length: Desired transcript length ("short", "medium", "long", "very-long")
        style: Desired transcript style ("friendly", "professional", "academic", "casual", "technical")
        model_name: Name of the model to use
        output_dir: Directory for output files
        
    Returns:
        str of output_file_path
        
    Raises:
        TranscriptError: For any transcript processing related errors
        InvalidParameterError: For invalid length or style parameters
    """
    try:
        # Validate length and style parameters
        valid_lengths = ["short", "medium", "long", "very-long"]
        valid_styles = ["friendly", "professional", "academic", "casual", "technical", "funny"]
        
        if length not in valid_lengths:
            raise InvalidParameterError(f"Invalid length parameter. Must be one of: {valid_lengths}")
        if style not in valid_styles:
            raise InvalidParameterError(f"Invalid style parameter. Must be one of: {valid_styles}")

        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read input file
        logger.info(f"Reading input file: {input_file}")
        input_text = read_input_file(input_file)

        # Generate transcript
        logger.info(f"Generating {length} {style} transcript...")
        transcript = generate_transcript(
            model = model,
            tokenizer = tokenizer,
            client = client,
            model_name = config.get('model_name', model_name),
            input_text = input_text,
            length = config.get('length', length),
            style = config.get('style', style),
            max_tokens = config.get('max_tokens', 8126),
            temperature = config.get('temperature', 1)
        )

        # Save transcript
        output_file = output_dir / 'data.pkl'
        with open(output_file, 'wb') as file:
            pickle.dump(transcript, file)

        logger.info(f"Transcript saved to: {output_file}")
        return str(input_file), str(output_file)

    except (FileReadError, TranscriptGenerationError, InvalidParameterError) as e:
        logger.error(f"Transcript generation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during transcript generation: {str(e)}")
        raise TranscriptError(f"Transcript generation failed: {str(e)}")