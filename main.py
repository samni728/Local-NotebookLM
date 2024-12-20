from steps.helpers import read_config, get_client_or_model_and_tokenizer
from typing import Optional
from pathlib import Path
import argparse
import logging

from steps.step1 import step1
from steps.step2 import step2
from steps.step3 import step3
from steps.step4 import step4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Convert PDF to Podcast with AI')
    
    # Required arguments
    parser.add_argument('pdf_path', type=str, help='Path to the input PDF file')
    
    # Optional arguments
    parser.add_argument('--config_path', type=str, default='config.yaml',
                       help='Path to the configuration file (default: config.yaml)')
    parser.add_argument('--output_dir', type=str, 
                       help='Directory for output files')
    parser.add_argument('--length', type=str,
                       choices=['short', 'medium', 'long', 'very-long'],
                       help='Desired podcast length')
    parser.add_argument('--style', type=str,
                       choices=['friendly', 'professional', 'academic', 'casual', 'technical', "funny"],
                       help='Desired podcast style')
    parser.add_argument('--chunk_size', type=int,
                       help='Size of text chunks for processing')
    parser.add_argument('--max_chars', type=int,
                       help='Maximum characters to process from PDF')
    
    return parser.parse_args()

def get_config_with_args(args, config):
    """
    Merge command line arguments with config file values, prioritizing command line arguments.
    
    Args:
        args: Parsed command line arguments
        config: Configuration dictionary from yaml file
    
    Returns:
        Updated configuration dictionary
    """
    # Create a copy of the config to modify
    updated_config = config.copy()
    
    # Update output directory if provided
    if args.output_dir is not None:
        updated_config['Global']['output_dir'] = args.output_dir
    
    # Update Step1 configurations
    if args.chunk_size is not None:
        updated_config['Step1']['chunk_size'] = args.chunk_size
    if args.max_chars is not None:
        updated_config['Step1']['max_chars'] = args.max_chars
    
    # Update Step2 configurations
    if args.length is not None:
        updated_config['Step2']['length'] = args.length
    if args.style is not None:
        updated_config['Step2']['style'] = args.style
    
    return updated_config

def main():
    """Main function to run the PDF to Podcast pipeline."""
    args = parse_args()
    
    try:
        # Load config from specified path and merge with command line arguments
        logger.info(f"Loading configuration from {args.config_path}")
        config = read_config(args.config_path)
        config = get_config_with_args(args, config)
        
        # Create output directory
        output_dir = Path(config['Global']['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize API client
        logger.info(f"Initializing models...")
        client, model, tokenizer = get_client_or_model_and_tokenizer(args)

        # Step 1: Process PDF and generate clean text
        logger.info("Step 1: Processing PDF...")
        clean_text_path = step1(
            pdf_path=args.pdf_path,
            model=model,
            tokenizer=tokenizer,
            client=client,
            config=config['Step1'],
            model_name=config['Step1']['model_name'],
            output_dir=config['Global']['output_dir'],
            chunk_size=config['Step1']['chunk_size'],
            max_chars=config['Step1']['max_chars']
        )

        # Step 2: Generate initial podcast transcript
        logger.info("Step 2: Generating podcast transcript...")
        transcript_path = step2(
            model=model,
            tokenizer=tokenizer,
            client=client,
            input_file=clean_text_path,
            config=config['Step2'],
            length=config['Step2']['length'],
            style=config['Step2']['style'],
            model_name=config['Step2']['model_name'],
            output_dir=config['Global']['output_dir']
        )

        # Step 3: Rewrite transcript for TTS
        logger.info("Step 3: Rewriting transcript for TTS...")
        tts_ready_path = step3(
            model=model,
            tokenizer=tokenizer,
            client=client,
            config=config['Step3'],
            input_file=transcript_path,
            model_name=config['Step3']['model_name'],
            output_dir=config['Global']['output_dir']
        )

        # Step 4: Generate audio
        logger.info("Step 4: Generating audio...")
        final_audio_path = step4(
            cohost_speaker_ref_audio_path=config['Step4']["cohost_speaker_ref_audio_path"],
            cohost_speaker_ref_audio_text=config['Step4']["cohost_speaker_ref_audio_text"],
            tts_model_name=config['Step4']["model_name"],
            output_dir=config['Global']['output_dir']
        )

        logger.info(f"Podcast generation complete! Output saved to: {final_audio_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())