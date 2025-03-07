from typing import Dict, Any, List, Optional, Literal
from openai import OpenAI, AzureOpenAI
import time

FormatType = Literal[
    "podcast", "interview", "panel-discussion", "debate",
    "summary", "narration", "storytelling", "explainer",
    "lecture", "tutorial", "q-and-a",
    "news-report", "executive-brief", "meeting-minutes", "analysis",
]
LengthType = Literal["short", "medium", "long", "very-long"]
StyleType = Literal["normal", "friendly", "professional", "academic", "casual", "technical", "gen-z", "funny"]

def wait_for_next_step(seconds: float = 2):
    time.sleep(seconds)

def set_provider(
        provider_name: Optional[Literal['openai', 'lmstudio', 'ollama', 'groq', 'azure', 'custom']] = None,
        config: Optional[Dict[str, Any]] = None
    ):
    if provider_name == None:
        provider_name = config["name"]
    api_key = config["key"]
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
    elif provider_name == "azure":
        base_url = config["endpoint"]
        version = config["version"]
        if base_url is None:
            raise ValueError("Base URL is required for AzureOpenAI provider.")
        if version is None:
            raise ValueError("Version is required for AzureOpenAI provider.")
        if api_key is None:
            raise ValueError("Key is required for AzureOpenAI provider.")

        client = AzureOpenAI(
            azure_endpoint=base_url,
            api_version=version,
            api_key=api_key
        )
        return client
    elif provider_name == "custom":
        base_url = config["endpoint"]
        if base_url is None:
            raise ValueError("Base URL is required for OpenAI provider, also if it needs a key then provide it too.")
        
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        return client

def generate (
    client: Any = None,
    messages: Optional[List[Dict]] = None,
    model: str = "gpt-4o-mini",
    max_tokens: int = 512,
    temperature: float = 0.7,
    format: bool = False
) -> str:
    if format:
        response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"}
    )
    else:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    return response.choices[0].message.content