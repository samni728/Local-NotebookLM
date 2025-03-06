from typing import Dict, Any, Optional, Literal
from openai import OpenAI
from pathlib import Path
from mlx_lm import load
import yaml

FormatType = Literal[
    "podcast", "interview", "panel-discussion", "debate", # Conversation-based formats
    "summary", "narration", "storytelling", "explainer", # Narrative formats
    "lecture", "tutorial", "q-and-a", # Educational formats
    "news-report", "executive-brief", "meeting-minutes", "analysis", # Professional formats
]

LengthType = Literal["short", "medium", "long", "very-long"]

StyleType = Literal["normal", "friendly", "professional", "academic", "casual", "technical", "gen-z", "funny"]

def read_config(config_path: str = "config.yaml") -> Dict[Any, Any]:
    """
    Read and parse a YAML configuration file.
    
    Args:
        config_path (str): Path to the YAML configuration file. Defaults to "config.yaml"
        
    Returns:
        Dict[Any, Any]: Dictionary containing the parsed YAML content
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the YAML file is invalid or cannot be parsed
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
        if config is None:
            return {}
            
        return config
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")

def set_provider(
        provider_name: Literal['openai', 'lmstudio', 'ollama', 'groq', 'kokoro', 'other'],
        base_url: Optional[str] = None,
        api_key: Optional[str] = 'NotebookLM_but_local'
    ) -> OpenAI:
    """
    Set the provider name for the API call.

    Args:
        provider_name (str): The name of the provider. Can only be "openai", "lmstudio" "ollama", "groq", and "other".

    Returns:
        OpenAI: The OpenAI client object.
    """

    if provider_name == "openai":
        if api_key is None:
            raise ValueError("API key is required for OpenAI provider.")
        
        client = OpenAI(
            api_key=api_key,
        )
        return client
    elif provider_name == "lmstudio":
        client = OpenAI(
            base_url='http://localhost:1234/v1',
            api_key=api_key,
        )
        return client
    elif provider_name == "ollama":
        client = OpenAI(
            base_url='http://localhost:11434/v1',
            api_key=api_key,
        )
        return client
    elif provider_name == "groq":
        client = OpenAI(
            base_url='https://api.groq.com/openai/v1',
            api_key=api_key,
        )
        return client
    elif provider_name == "kokoro":
        client = OpenAI(
            base_url='http://localhost:8880/v1',
            api_key=api_key,
        )
        return client
    elif provider_name == "other":
        if base_url is None:
            raise ValueError("Base URL is required for OpenAI provider, also if it needs a key then provide it too.")
        
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        return client

def get_client_or_model_and_tokenizer(config_path: str = 'config.yaml'):
    """Get the client or model and tokenizer based on the configuration."""
    config = read_config(config_path)
    global_config = config.get('Global', {})

    provider_format: Literal['openai', 'mlx_lm'] = global_config.get('provider_format', 'openai')
    provider = global_config.get('provider', 'lmstudio')

    api_key = config.get('api_key', None)
    base_url = config.get('base_url', None)

    client = None
    model = None
    tokenizer = None

    if provider_format == 'openai':
        client = set_provider(
            provider_name=provider,
            base_url=base_url,
            api_key=api_key
        )
    else:
        model_name = global_config.get('model_name', 'gpt-3.5-turbo')
        model, tokenizer = load(model_name)

    return client, model, tokenizer
