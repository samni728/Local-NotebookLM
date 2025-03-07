from .helpers import generate, FormatType, StyleType, LengthType, wait_for_next_step
from .prompts import step3_system_prompt
from typing import Dict, Any, Optional
import logging, pickle, time
from ast import literal_eval
from pathlib import Path


logger = logging.getLogger(__name__)

class TranscriptError(Exception):
    pass
class FileReadError(TranscriptError):
    pass
class TranscriptGenerationError(TranscriptError):
    pass
class InvalidParameterError(TranscriptError):
    pass

def read_pickle_file(filename: str) -> str:
    try:
        with open(filename, 'rb') as file:
            content = pickle.load(file)
        return content
    except FileNotFoundError:
        raise FileReadError(f"File '{filename}' not found")
    except Exception as e:
        raise FileReadError(f"Failed to read pickle file: {str(e)}")

def generate_rewritten_transcript(
    client,
    model_name,
    input_text,
    max_tokens,
    temperature,
    format_type,
    preference_text
) -> str:
    try:
        wait_for_next_step()
        conversation = [
            {"role": "system", "content": step3_system_prompt.format(format_type=format_type, preference_text=preference_text)},
            {"role": "user", "content": input_text},
        ]
        return generate(
            client=client,
            model=model_name,
            messages=conversation,
            max_tokens=max_tokens,
            temperature=temperature,
            # format=True
        )

    except Exception as e:
        raise TranscriptGenerationError(f"Failed to generate transcript: {str(e)}")

def validate_transcript_format(transcript: str) -> bool:
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

def step3(
    client = None,
    config: Optional[Dict[str, Any]] = None,
    input_file: str = None,
    output_dir: str = None,
    preference_text: str = None,
    format_type: FormatType = "summary",
) -> str:
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read input file
        logger.info(f"Reading input file: {input_file}")
        input_text = read_pickle_file(input_file)

        if not preference_text:
            preference_text = ""

        logger.info(f"Optimizing transcript for TTS...")

        # Generate rewritten transcript
        logger.info(f"Generating rewritten transcript...")
        transcript = generate_rewritten_transcript(
            client=client,
            model_name=config["Big-Text-Model"]["model"],
            input_text=input_text,
            format_type=format_type,
            preference_text=preference_text,
            max_tokens=config["Step3"]["max_tokens"],
            temperature=config["Step1"]["temperature"]
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