from .helpers import generate, FormatType, wait_for_next_step
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
    preference_text,
    chunk_token_limit
) -> str:
    try:
        wait_for_next_step()
        
        # More conservative token estimation (3.5 chars per token)
        estimated_tokens = len(input_text) // 3.5
        
        # If input is likely too long, split it into chunks
        if estimated_tokens > chunk_token_limit:
            # Convert token count to character count for chunking
            chunk_size = int(chunk_token_limit * 3.5)
            chunks = [input_text[i:i+chunk_size] for i in range(0, len(input_text), chunk_size)]
            logger.info(f"Input split into {len(chunks)} chunks (chunk_token_limit: {chunk_token_limit})")
            
            # First chunk - generate the beginning of the transcript
            system_prompt = step3_system_prompt.format(format_type=format_type, preference_text=preference_text)
            
            conversation = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Convert this transcript to the required format (part 1/{len(chunks)}): {chunks[0]}"},
            ]
            
            result = generate(
                client=client,
                model=model_name,
                messages=conversation,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            # Check if the first chunk produced valid output
            if validate_transcript_format(result):
                # If valid, parse it to a list
                transcript_list = literal_eval(result)
            else:
                # If not valid, start with empty list
                transcript_list = []
                logger.warning("First chunk did not produce valid format, starting with empty list")
            
            # Process remaining chunks
            for i, chunk in enumerate(chunks[1:], 2):
                # Add delay between API calls
                time.sleep(3)
                
                # Very minimal prompt to save tokens
                continuation_prompt = (
                    f"Continue processing this transcript (part {i}/{len(chunks)}). "
                    f"Maintain the same format [('Speaker', 'Text'), ...] and continue from where you left off: {chunk}"
                )
                
                conversation = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": continuation_prompt}
                ]
                
                next_part = generate(
                    client=client,
                    model=model_name,
                    messages=conversation,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                
                # Try to parse the next part
                if validate_transcript_format(next_part):
                    next_list = literal_eval(next_part)
                    transcript_list.extend(next_list)
                else:
                    logger.warning(f"Chunk {i} did not produce valid format, skipping")
            
            # Convert the list back to string representation
            return str(transcript_list)
        else:
            # Original behavior for texts that fit within token limits
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
    format_type: FormatType = "podcast",
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

        # Get chunk token limit from config, with a default fallback
        chunk_token_limit = config["Step3"].get("chunk_token_limit", 2000)

        # Generate rewritten transcript
        logger.info(f"Generating rewritten transcript...")
        transcript = generate_rewritten_transcript(
            client=client,
            model_name=config["Big-Text-Model"]["model"],
            input_text=input_text,
            format_type=format_type,
            preference_text=preference_text,
            max_tokens=config["Step3"]["max_tokens"],
            temperature=config["Step3"]["temperature"],
            chunk_token_limit=chunk_token_limit
        )

        # Validate transcript format
        if not validate_transcript_format(transcript):
            raise TranscriptGenerationError("Generated transcript is not in the correct format")

        # Save transcript
        output_file = output_dir / 'podcast_ready_data'
        with open(f'{output_file}.pkl', 'wb') as file:
            pickle.dump(transcript, file)
        with open(f'{output_file}.txt', 'wb') as file:
            file.write(transcript, file)

        logger.info(f"Rewritten transcript saved to: {output_file}")
        return str(input_file), str(output_file)

    except (FileReadError, TranscriptGenerationError, InvalidParameterError) as e:
        logger.error(f"Transcript rewriting failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during transcript rewriting: {str(e)}")
        raise TranscriptError(f"Transcript rewriting failed: {str(e)}")