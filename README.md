# Local-NotebookLM

A local AI-powered tool that converts PDF documents into engaging podcasts, using local LLMs and TTS models.

## Features

- PDF text extraction and processing
- Customizable podcast generation with different styles and lengths
- Local LLM support through various providers (LMStudio, Ollama, etc.)
- Text-to-Speech conversion with voice cloning capabilities
- Fully configurable pipeline

## Installation

1: Clone the repository:

```bash
git clone https://github.com/yourusername/Local-NotebookLM.git
cd Local-NotebookLM
```

2: Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3: Install the required packages:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `config.yaml` file in the root directory with the following structure:

```yaml
Global:
  output_dir: "./resources"
  provider_format: 'openai'  # Options: ['openai', 'mlx_lm']
  provider: "lmstudio"       # Options: ['openai', 'lmstudio', 'ollama', 'groq', 'other']
  base_url: ''              # Required only if provider is 'other'
  api_key: ''               # Required for 'other', 'openai', and 'groq' providers

Step1:
  model_name: "mlx-community/Josiefied-Qwen2.5-1.5B-Instruct-abliterated-v1-4bit"
  max_tokens: 512
  temperature: 0.7
  chunk_size: 1000
  max_chars: 100000

Step2:
  model_name: "mlx-community/Josiefied-Qwen2.5-14B-Instruct-abliterated-v4-4-bit"
  max_tokens: 8126
  temperature: 1
  length: "long"           # Options: ["short", "medium", "long", "very-long"]
  style: "academic"        # Options: ["friendly", "professional", "academic", "casual", "technical", "funny"]

Step3:
  model_name: "mlx-community/Josiefied-Qwen2.5-14B-Instruct-abliterated-v4-4-bit"
  max_tokens: 8126
  temperature: 1

Step4:
  model_name: "lucasnewman/f5-tts-mlx"
  cohost_speaker_ref_audio_path: "./voices/cohost.wav"
  cohost_speaker_ref_audio_text: "Some call me nature, others call me mother nature."
```

## Usage

1. Prepare your environment:
   - If using LMStudio: Start LMStudio and ensure the API server is running
   - If using Ollama: Install and start Ollama with your desired models
   - If using other providers: Ensure you have the necessary API keys

2. Run the script:

```bash
python main.py input.pdf [options]
```

Available options:

- `--config_path`: Path to custom config file (default: config.yaml)
- `--output_dir`: Directory for output files
- `--length`: Desired podcast length (short/medium/long/very-long)
- `--style`: Podcast style (friendly/professional/academic/casual/technical/funny)
- `--chunk_size`: Size of text chunks for processing
- `--max_chars`: Maximum characters to process from PDF

Example:

```bash
python main.py research_paper.pdf --style academic --length long
```

## Pipeline Steps

1. **PDF Processing (Step1)**
   - Extracts text from PDF
   - Cleans and formats the content
   - Splits into manageable chunks

2. **Transcript Generation (Step2)**
   - Generates initial podcast script
   - Applies specified style and length
   - Structures content for audio format

3. **TTS Optimization (Step3)**
   - Rewrites content for better TTS performance
   - Adds speech markers and formatting
   - Optimizes for natural flow

4. **Audio Generation (Step4)**
   - Converts text to speech
   - Applies voice cloning if specified
   - Generates final audio file

## Requirements

- Python 3.8+
- MLX (for local AI models)
- PDF processing libraries
- TTS dependencies
- Additional requirements listed in requirements.txt