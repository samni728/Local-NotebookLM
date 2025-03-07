from typing import List, Tuple, Dict, Any, Optional
from .helpers import wait_for_next_step
import logging, pickle, ast, re, time
from pathlib import Path
import soundfile as sf
from tqdm import tqdm
import numpy as np


logger = logging.getLogger(__name__)

class AudioGenerationError(Exception):
    pass

def load_podcast_data(data_path: Path) -> List[Tuple[str, str]]:
    try:
        with open(data_path, 'rb') as file:
            podcast_text = pickle.load(file)
        return ast.literal_eval(podcast_text)
    except FileNotFoundError:
        raise FileNotFoundError(f"Podcast data file not found: {data_path}")
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Invalid podcast data format: {str(e)}")

def concatenate_audio_files(segment_dir: Path) -> Tuple[np.ndarray, int]:
    audio_files = sorted(
        segment_dir.glob("*podcast_segment_*.wav"),
        key=lambda x: int(re.search(r'segment_(\d+)\.wav', str(x)).group(1))
    )
    
    if not audio_files:
        raise FileNotFoundError(f"No audio segments found in {segment_dir}")
    
    # Read the first file to get the sample rate
    first_data, sample_rate = sf.read(audio_files[0])
    audio_data = [first_data]
    
    # Read the rest of the files
    for file in audio_files[1:]:
        try:
            data, _ = sf.read(file)
            audio_data.append(data)
        except Exception as e:
            logger.error(f"Failed to read audio file {file}: {str(e)}")
            continue
    
    return np.concatenate(audio_data), sample_rate

def generate_speaker_audio(
    client,
    model_name,
    text,
    output_path,
    voice,
    response_format
) -> None:
    try:
        wait_for_next_step()
        with client.audio.speech.with_streaming_response.create(
            model=model_name, 
            voice=voice,
            input=text,
            response_format=response_format
        ) as response:
            response.stream_to_file(str(output_path))
    except Exception as e:
        raise AudioGenerationError(f"Failed to generate audio: {str(e)}")

def step4(
    client: Any = None,
    config: Optional[Dict[str, Any]] = None,
    dir: str = None
) -> Path:
    model_name = config["Text-To-Speech-Model"]["model"]
    co_host = config["Co-Host-Speaker-Voice"]
    host = config["Host-Speaker-Voice"]
    response_format = config["Text-To-Speech-Model"].get("audio_format", "wav")
    
    try:
        # Convert output_dir to a Path object
        output_dir = Path(dir)
        
        # Create output directories
        segments_dir = output_dir / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        
        # Load podcast data
        podcast_data = load_podcast_data(output_dir / "podcast_ready_data.pkl")
        
        # Generate audio segments
        for i, (speaker, text) in enumerate(tqdm(podcast_data, desc="Generating podcast segments"), 1):
            output_path = segments_dir / f"podcast_segment_{i}.wav"
            
            if speaker == "Speaker 1":
                generate_speaker_audio(
                    client=client,
                    text=text,
                    model_name=model_name,
                    output_path=output_path,
                    voice=host,
                    response_format=response_format
                )
            else:
                generate_speaker_audio(
                    client=client,
                    text=text,
                    model_name=model_name,
                    output_path=output_path,
                    voice=co_host,
                    response_format=response_format
                )
        
        # Concatenate all segments
        logger.info("Concatenating audio segments...")
        final_audio, detected_sample_rate = concatenate_audio_files(segments_dir)
        
        # Save final podcast with the detected sample rate
        final_path = output_dir / "podcast.wav"
        sf.write(str(final_path), final_audio, detected_sample_rate)
        logger.info(f"Podcast generated successfully at {final_path}")
        
        return final_path
        
    except Exception as e:
        logger.error(f"Failed to generate podcast: {str(e)}")
        raise