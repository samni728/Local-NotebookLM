from .helpers import generate_text, FormatType, wait_for_next_step
from .prompts import map_step3_system_prompt
from typing import Dict, Any, Optional
from ast import literal_eval
from pathlib import Path
import logging, pickle


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
    system_prompt,
    max_tokens,
    temperature,
    format_type,
) -> str:
    try:
        wait_for_next_step()
        if system_prompt == None:
            system_prompt = map_step3_system_prompt(format_type=format_type)
        else:
            system_prompt = system_prompt
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ]
        return generate_text(
            client=client,
            model=model_name,
            messages=conversation,
            max_tokens=max_tokens,
            temperature=temperature
        )

    except Exception as e:
        raise TranscriptGenerationError(f"Failed to generate transcript: {str(e)}")

def generate_rewritten_transcript_with_overlap(
    client,
    model_name,
    input_text,
    max_tokens,
    temperature,
    format_type,
    system_prompt,
    chunk_size=8000,
    overlap_percent=20
) -> str:
    """Generate transcript in chunks with overlap for seamless continuation."""
    try:
        wait_for_next_step()
        
        # Calculate overlap size in characters
        overlap_size = int(chunk_size * (overlap_percent / 100))
        
        # Split the input text into chunks with overlap
        chunks = []
        start = 0
        while start < len(input_text):
            end = min(start + chunk_size, len(input_text))
            chunks.append(input_text[start:end])
            start = end - overlap_size if end < len(input_text) else end
        
        logger.info(f"Processing transcript in {len(chunks)} chunks with {overlap_percent}% overlap")
        
        # Process each chunk and combine results
        combined_transcript = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            # Add context for continuation chunks
            context = ""
            is_final_chunk = (i == len(chunks) - 1)
            
            if i > 0:
                context = f"IMPORTANT: This is a continuation of a previous transcript. The last part was:\n{combined_transcript[-3:] if len(combined_transcript) >= 3 else combined_transcript}\nContinue the conversation seamlessly from here, maintaining the same style and tone."
            
            if not is_final_chunk:
                context += "\n\nIMPORTANT: DO NOT conclude the conversation or say goodbyes. This is the middle of the conversation, not the end."
            else:
                context += "\n\nThis is the final part of the conversation. You may conclude naturally if appropriate."
            
            # Customize system prompt based on chunk position
            if system_prompt == None:
                chunk_system_prompt = map_step3_system_prompt(format_type=format_type)
            else:
                chunk_system_prompt = system_prompt
            if not is_final_chunk:
                chunk_system_prompt += "\n\nIMPORTANT: Since this is not the final part of the conversation, DO NOT include any goodbyes, conclusions, or wrap-ups. The conversation should continue naturally."
            
            conversation = [
                {"role": "system", "content": chunk_system_prompt},
                {"role": "user", "content": f"{chunk}\n\n{context}"},
            ]
            
            chunk_transcript = generate_text(
                client=client,
                model=model_name,
                messages=conversation,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            # Parse the chunk transcript
            try:
                chunk_data = literal_eval(chunk_transcript)
                
                # Filter out any goodbye-like messages in non-final chunks
                if not is_final_chunk:
                    filtered_chunk_data = []
                    for speaker, text in chunk_data:
                        goodbye_phrases = ["goodbye", "bye", "farewell", "until next time", "see you", 
                                        "thanks for listening", "that's all", "wrapping up", 
                                        "concluding", "end of", "final thoughts"]
                        
                        # Find if any goodbye phrase exists in the text
                        found_phrase = None
                        for phrase in goodbye_phrases:
                            if phrase in text.lower():
                                found_phrase = phrase
                                break
                        
                        if not found_phrase:
                            filtered_chunk_data.append((speaker, text))
                        else:
                            # Replace with a continuation prompt instead
                            modified_text = text.lower().split(found_phrase)[0]
                            filtered_chunk_data.append((speaker, modified_text + "let's continue our discussion."))
                    
                    chunk_data = filtered_chunk_data
                
                # For first chunk, add all entries
                if i == 0:
                    combined_transcript.extend(chunk_data)
                # For subsequent chunks, skip some initial entries to avoid repetition
                else:
                    # Skip first 1-2 entries as they might overlap with previous chunk
                    skip_count = min(2, len(chunk_data) // 10)  # Skip ~10% or at most 2 entries
                    combined_transcript.extend(chunk_data[skip_count:])
            except Exception as e:
                raise TranscriptGenerationError(f"Failed to parse chunk {i+1}: {str(e)}")
        
        # Convert back to string representation
        return str(combined_transcript)

    except Exception as e:
        raise TranscriptGenerationError(f"Failed to generate transcript with overlap: {str(e)}")

def validate_transcript_format(transcript: str) -> bool:
    try:
        # Clean up the transcript string to handle escape sequences
        cleaned_transcript = transcript.replace('\\(', '\\\\(').replace('\\)', '\\\\)')
        data = literal_eval(cleaned_transcript)
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
    format_type: FormatType = "podcast",
    system_prompt: str = None
) -> str:
    
    print(format_type)
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        input_path = input_file
        if not input_file.endswith('.pkl'):
            input_path = f"{input_path}.pkl"

        # Read input file
        logger.info(f"Reading input file: {input_file}")
        input_text = read_pickle_file(input_file)

        logger.info(f"Optimizing transcript for TTS...")

        # Check if we need to generate in chunks with overlap
        if len(input_text) > config["Step3"].get("chunk_size", 8000):
            logger.info("Input text is large, generating transcript in chunks with overlap...")
            transcript = generate_rewritten_transcript_with_overlap(
                client=client,
                model_name=config["Big-Text-Model"]["model"],
                input_text=input_text,
                format_type=format_type,
                system_prompt=system_prompt,
                max_tokens=config["Step3"]["max_tokens"],
                temperature=config["Step1"]["temperature"],
                chunk_size=config["Step3"].get("chunk_size", 8000),
                overlap_percent=config["Step3"].get("overlap_percent", 10)
            )
        else:
            # Generate rewritten transcript in one go
            logger.info(f"Generating rewritten transcript...")
            transcript = generate_rewritten_transcript(
                client=client,
                system_prompt=system_prompt,
                model_name=config["Big-Text-Model"]["model"],
                input_text=input_text,
                format_type=format_type,
                max_tokens=config["Step3"]["max_tokens"],
                temperature=config["Step1"]["temperature"]
            )

        # Validate transcript format
        if not validate_transcript_format(transcript):
            raise TranscriptGenerationError("Generated transcript is not in the correct format")

        # Save transcript
        output_file = output_dir / 'podcast_ready_data'
        with open(f'{output_file}.pkl', 'wb') as file:
            pickle.dump(transcript, file)

        with open(f'{output_file}.txt', 'w') as file:
            file.write(transcript)

        logger.info(f"Rewritten transcript saved to: {output_file}")
        return str(input_file), str(output_file)

    except (FileReadError, TranscriptGenerationError, InvalidParameterError) as e:
        logger.error(f"Transcript rewriting failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during transcript rewriting: {str(e)}")
        raise TranscriptError(f"Transcript rewriting failed: {str(e)}")