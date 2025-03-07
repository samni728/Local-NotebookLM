from .helpers import generate, wait_for_next_step, FormatType, LengthType, StyleType
from .prompts import map_step2_system_prompt
from typing import Any, Dict, Optional
import logging, pickle, time
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

def read_input_file(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except UnicodeDecodeError:
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

def generate_transcript(
    client,
    model_name,
    input_text,
    length,
    style,
    format_type,
    preference_text,
    max_tokens,
    temperature
) -> str:
    try:
        wait_for_next_step()
        conversation = [
            {"role": "system", "content": map_step2_system_prompt(length=length, style=style, format_type=format_type, preference_text=preference_text)},
            {"role": "user", "content": input_text},
        ]
        return generate(
            client=client,
            model=model_name,
            messages=conversation,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    except Exception as e:
        raise TranscriptGenerationError(f"Failed to generate transcript: {str(e)}")

def step2(
    client: Any = None,
    config: Optional[Dict[str, Any]] = None,
    input_file: str = None,
    output_dir: str = None,
    format_type: FormatType = "podcast",
    length: LengthType = "medium",
    style: StyleType = "normal",
    preference_text: str = "nothing"
) -> str:
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Reading input file: {input_file}")
        input_text = read_input_file(input_file)

        logger.info(f"Generating {length} {style} transcript...")
        transcript = generate_transcript(
            client=client,
            model_name=config["Big-Text-Model"]["model"],
            input_text=input_text,
            format_type=format_type,
            length=length,
            style=style,
            preference_text=preference_text,
            max_tokens=config["Step2"]["max_tokens"],
            temperature=config["Step2"]["temperature"]
        )

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