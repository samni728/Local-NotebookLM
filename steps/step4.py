from typing import List, Tuple, Dict, Any
from helpers import set_provider
from pathlib import Path
from tqdm import tqdm
import soundfile as sf
import numpy as np
import logging
import pickle
import ast
import re

client = set_provider('kokoro')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioGenerationError(Exception):
    """Custom exception for audio generation errors."""
    pass

def load_podcast_data(data_path: Path) -> List[Tuple[str, str]]:
    """
    Load podcast text data from pickle file.
    
    Args:
        data_path: Path to the pickle file containing podcast data
        
    Returns:
        List of tuples containing (speaker, text) pairs
        
    Raises:
        FileNotFoundError: If the podcast data file doesn't exist
        ValueError: If the data format is invalid
    """
    try:
        with open(data_path, 'rb') as file:
            podcast_text = pickle.load(file)
        return ast.literal_eval(podcast_text)
    except FileNotFoundError:
        raise FileNotFoundError(f"Podcast data file not found: {data_path}")
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Invalid podcast data format: {str(e)}")

def concatenate_audio_files(segment_dir: Path) -> np.ndarray:
    """
    Concatenate multiple audio segments into a single array.
    
    Args:
        segment_dir: Directory containing audio segments
        
    Returns:
        Numpy array containing concatenated audio data
        
    Raises:
        FileNotFoundError: If no audio segments are found
    """
    audio_files = sorted(
        segment_dir.glob("*podcast_segment_*.wav"),
        key=lambda x: int(re.search(r'segment_(\d+)\.wav', str(x)).group(1))
    )
    
    if not audio_files:
        raise FileNotFoundError(f"No audio segments found in {segment_dir}")
    
    audio_data = []
    for file in audio_files:
        try:
            data, _ = sf.read(file)
            audio_data.append(data)
        except Exception as e:
            logger.error(f"Failed to read audio file {file}: {str(e)}")
            continue
    
    return np.concatenate(audio_data)

def generate_speaker_audio(
    text: str,
    output_path: str,
    voice: str = 'af_sky'
) -> None:
    """
    Generate audio for a single speaker.
    
    Args:
        text: Text to convert to speech
        voice: Name of the voice to use
        output_path: Path to save the generated audio
    
    Raises:
        AudioGenerationError: If audio generation fails
    """
    try:
        with client.audio.speech.with_streaming_response.create(
            model="kokoro", 
            voice=voice, # af_sky+af_bella single or multiple voicepack combo possible
            input=text,
            response_format="wav"
        ) as response:
            response.stream_to_file(f"{output_path}.wav")
        
    except Exception as e:
        raise AudioGenerationError(f"Failed to generate audio: {str(e)}")

# Main Step4 Function
def step4(
    cohost_speaker_ref_audio_path: str = None,
    cohost_speaker_ref_audio_text: str = None,
    config: Dict[Any, Any] = None,
    tts_model_name: str = "lucasnewman/f5-tts-mlx",
    output_dir: str = None
) -> Path:
    """
    Generate a complete podcast audio file from text with multiple speakers.
    
    Args:
        cohost_speaker_ref_audio_path: Path to reference audio for co-host
        cohost_speaker_ref_audio_text: Text corresponding to co-host reference audio
        tts_model_name: Name of the TTS model to use
        output_dir: Directory to save generated audio files
        
    Returns:
        Path to the generated podcast audio file
        
    Raises:
        AudioGenerationError: If audio generation fails
        FileNotFoundError: If required files are missing
        ValueError: If input data is invalid
    """
    try:
        # Create output directories
        segments_dir = config.output_dir / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        
        # Load podcast data
        podcast_data = load_podcast_data(config.output_dir / "podcast_ready_data.pkl")
        
        # Generate audio segments
        for i, (speaker, text) in enumerate(tqdm(podcast_data, desc="Generating podcast segments"), 1):
            output_path = segments_dir / f"_podcast_segment_{i}.wav"
            
            if speaker == "Speaker 1":
                generate_speaker_audio(
                    text=text,
                    model_name=config.get('model_name', tts_model_name),
                    output_path=config.get('output_dir', output_dir)
                )
            else:  # Speaker 2
                generate_speaker_audio(
                    text=text,
                    model_name=config.get('model_name', tts_model_name),
                    output_path=config.get('output_dir', output_dir),
                    ref_audio_path=config.get('cohost_speaker_ref_audio_path', cohost_speaker_ref_audio_path),
                    ref_audio_text=config.get('cohost_speaker_ref_audio_text', cohost_speaker_ref_audio_text)
                )
        
        # Concatenate all segments
        logger.info("Concatenating audio segments...")
        final_audio = concatenate_audio_files(segments_dir)
        
        # Save final podcast
        final_path = config.output_dir / "_podcast.wav"
        sf.write(str(final_path), final_audio, SAMPLE_RATE)
        logger.info(f"Podcast generated successfully at {final_path}")
        
        return final_path
        
    except Exception as e:
        logger.error(f"Failed to generate podcast: {str(e)}")
        raise