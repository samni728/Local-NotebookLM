# Local-NotebookLM

A local AI-powered tool that converts PDF documents into engaging podcasts, using local LLMs and TTS models.

## Features

- PDF text extraction and processing
- Customizable podcast generation with different styles and lengths
- Support for various LLM providers (OpenAI, Groq, LMStudio, Ollama, Azure)
- Text-to-Speech conversion with voice selection
- Fully configurable pipeline
- Preference-based content focus
- Programmatic API for integration in other projects
- FastAPI server for web-based access
- Example podcast included for demonstration

## Prerequisites

- Python 3.12+
- Local LLM server (optional, for local inference)
- Local TTS server (optional, for local audio generation)
- At least 8GB RAM (16GB+ recommended for local models)
- 10GB+ free disk space

## Installation

### From PyPI

```bash
pip install Local-NotebookLM
```

### From source

1. Clone the repository:

```bash
git clone https://github.com/Goekdeniz-Guelmez/Local-NotebookLM.git
cd Local-NotebookLM
```

2. Create and activate a virtual environment (conda works too):

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Example Output

The repository includes an example podcast in `examples/podcast.wav` to demonstrate the quality and format of the output. The models used are: gpt4o and Mini with tts-hs on Azure. You can listen to this example to get a sense of what Local-NotebookLM can produce before running it on your own PDFs.

## Configuration

You can use the default configuration or create a custom JSON config file with the following structure:

```json
{
    "Co-Host-Speaker-Voice": "af_sky+af_bella",
    "Host-Speaker-Voice": "af_alloy",

    "Small-Text-Model": {
        "provider": {
            "name": "groq",
            "key": "your-api-key"
        },
        "model": "llama-3.2-90b-vision-preview"
    },

    "Big-Text-Model": {
        "provider": {
            "name": "groq",
            "key": "your-api-key"
        },
        "model": "llama-3.2-90b-vision-preview"
    },

    "Text-To-Speech-Model": {
        "provider": {
            "name": "custom",
            "endpoint": "http://localhost:8880/v1",
            "key": "not-needed"
        },
        "model": "kokoro",
        "audio_format": "wav"
    },

    "Step1": {
        "max_tokens": 1028,
        "temperature": 0.7,
        "chunk_size": 1000,
        "max_chars": 100000
    },

    "Step2": {
        "max_tokens": 8126,
        "temperature": 1
    },

    "Step3": {
        "max_tokens": 8126,
        "temperature": 1
    }
}
```

### Provider Options

The following provider options are supported:

- **OpenAI**: Use OpenAI's API
  ```json
  "provider": {
      "name": "openai",
      "key": "your-openai-api-key"
  }
  ```

- **Groq**: Use Groq's API for faster inference
  ```json
  "provider": {
      "name": "groq",
      "key": "your-groq-api-key"
  }
  ```

- **Azure OpenAI**: Use Azure's OpenAI service
  ```json
  "provider": {
      "name": "azure",
      "key": "your-azure-api-key",
      "endpoint": "your-azure-endpoint",
      "version": "api-version"
  }
  ```

- **LMStudio**: Use a local LMStudio server
  ```json
  "provider": {
      "name": "lmstudio",
      "endpoint": "http://localhost:1234/v1",
      "key": "not-needed"
  }
  ```

- **Ollama**: Use a local Ollama server
  ```json
  "provider": {
      "name": "ollama",
      "endpoint": "http://localhost:11434",
      "key": "not-needed"
  }
  ```

- **Custom**: Use any OpenAI-compatible API
  ```json
  "provider": {
      "name": "custom",
      "endpoint": "your-custom-endpoint",
      "key": "your-api-key-or-not-needed"
  }
  ```

## Usage

### Command Line Interface

Run the script with the following command:

```bash
python -m local_notebooklm.start --pdf PATH_TO_PDF [options]
```

#### Available Options

| Option | Description | Default |
|--------|-------------|---------|
| `--pdf` | Path to the PDF file (required) | - |
| `--config` | Path to custom config file | Uses base_config |
| `--format` | Output format type (summary, podcast, article, interview) | podcast |
| `--length` | Content length (short, medium, long, very-long) | medium |
| `--style` | Content style (normal, casual, formal, technical, academic) | normal |
| `--preference` | Additional focus preferences or instructions | None |
| `--output-dir` | Directory to store output files | ./output |

#### Example Commands

Basic usage:
```bash
python -m local_notebooklm.start --pdf documents/research_paper.pdf
```

Customized podcast:
```bash
python -m local_notebooklm.start --pdf documents/research_paper.pdf --format podcast --length long --style casual
```

With custom preferences:
```bash
python -m local_notebooklm.start --pdf documents/research_paper.pdf --preference "Focus on practical applications and real-world examples"
```

Using custom config:
```bash
python -m local_notebooklm.start --pdf documents/research_paper.pdf --config custom_config.json --output-dir ./my_podcast
```

### Programmatic API

You can also use Local-NotebookLM programmatically in your Python code:

```python
from local_notebooklm.processor import podcast_processor

success, result = podcast_processor(
    pdf_path="documents/research_paper.pdf",
    config_path="config.json",
    format_type="interview",
    length="long",
    style="professional",
    preference="Focus on the key technical aspects",
    output_dir="./test_output"
)

if success:
    print(f"Successfully generated podcast: {result}")
else:
    print(f"Failed to generate podcast: {result}")
```

### FastAPI Server

Start the FastAPI server to access the functionality via a web API:

```bash
 python -m local_notebooklm.server
```

By default, the server runs on http://localhost:8000. You can access the API documentation at http://localhost:8000/docs.

## Pipeline Steps

### 1. PDF Processing (Step1)
- Extracts text from PDF documents
- Cleans and formats the content
- Removes irrelevant elements like page numbers and headers
- Handles LaTeX math expressions and special characters
- Splits content into manageable chunks for processing

### 2. Transcript Generation (Step2)
- Generates an initial podcast script based on the extracted content
- Applies the specified style (casual, formal, technical, academic)
- Formats content according to the desired length (short, medium, long, very-long)
- Structures content for a conversational format
- Incorporates user-specified format type (summary, podcast, article, interview)

### 3. TTS Optimization (Step3)
- Rewrites content specifically for better text-to-speech performance
- Creates a two-speaker conversation format
- Adds speech markers and natural conversation elements
- Optimizes for natural flow and engagement
- Incorporates user preferences for content focus
- Formats output as a list of speaker-text tuples

### 4. Audio Generation (Step4)
- Converts the optimized text to speech using the specified TTS model
- Applies different voices for each speaker
- Generates individual audio segments for each dialogue part
- Concatenates segments into a final audio file
- Maintains consistent audio quality and sample rate

## Output Files

The pipeline generates the following files:

- `step1/extracted_text.txt`: Raw text extracted from the PDF
- `step1/clean_extracted_text.txt`: Cleaned and processed text
- `step2/data.pkl`: Initial transcript data
- `step3/podcast_ready_data.pkl`: TTS-optimized conversation data
- `step3/segments/podcast_segment_*.wav`: Individual audio segments
- `step3/podcast.wav`: Final concatenated podcast audio file

## Troubleshooting

### Common Issues

1. **PDF Extraction Fails**
   - Try a different PDF file
   - Check if the PDF is password-protected
   - Ensure the PDF contains extractable text (not just images)

2. **API Connection Errors**
   - Verify your API keys are correct
   - Check your internet connection
   - Ensure the API endpoints are accessible

3. **Out of Memory Errors**
   - Reduce the chunk size in the configuration
   - Use a smaller model
   - Close other memory-intensive applications

4. **Audio Quality Issues**
   - Try different TTS voices
   - Adjust the sample rate in the configuration
   - Check if the TTS server is running correctly

### Getting Help

If you encounter issues not covered here, please:
1. Check the logs for detailed error messages
2. Open an issue on the GitHub repository with details about your problem
3. Include the error message and steps to reproduce the issue

## Requirements

- Python 3.12+
- PyPDF2
- tqdm
- numpy
- soundfile
- requests
- pathlib
- fastapi
- uvicorn

Full requirements are listed in `requirements.txt`.

## Acknowledgments

- This project uses various open-source libraries and models
- Special thanks to the developers of LLaMA, OpenAI, and other AI models that make this possible

---

For more information, visit the [GitHub repository](https://github.com/Goekdeniz-Guelmez/Local-NotebookLM).

Best
Gökdeniz Gülmez

---

## Citing Local-NotebookLM

The Local-NotebookLM software suite was developed by Gökdeniz Gülmez. If you find Local-NotebookLM useful in your research and wish to cite it, please use the following
BibTex entry:

```text
@software{
  Local-NotebookLM,
  author = {Gökdeniz Gülmez},
  title = {{Local-NotebookLM}: A Local-NotebookLM to convert PDFs into Audio.},
  url = {https://github.com/Goekdeniz-Guelmez/Local-NotebookLM},
  version = {0.1.0},
  year = {2025},
}
```