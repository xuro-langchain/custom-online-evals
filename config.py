import os
import requests
from typing import Dict
from dotenv import load_dotenv
from langsmith import Client, traceable

load_dotenv(".env")

client = Client()

LANGSMITH_API_URL = os.getenv("LANGSMITH_API_URL", "https://api.smith.langchain.com")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def auth_headers() -> Dict[str, str]:
    if not LANGSMITH_API_KEY:
        raise RuntimeError("LANGSMITH_API_KEY is required in environment.")
    return {
        "x-api-key": LANGSMITH_API_KEY,
        "Content-Type": "application/json",
    }

def parse_judge_model(model_string: str) -> tuple[str, str]:
    """
    Parse judge model string in format 'provider:model' or just 'model'.
    Returns (provider, model_name).
    Only 'openai' provider is supported.
    """
    if ":" in model_string:
        provider, model_name = model_string.split(":", 1)
        provider = provider.lower().strip()
        model_name = model_name.strip()
        
        if provider != "openai":
            raise ValueError(
                f"Unsupported provider '{provider}'. Only 'openai' is supported. "
                f"Format: 'openai:model-name' or just 'model-name'"
            )
        return provider, model_name
    else:
        # Default to OpenAI if no provider specified
        return "openai", model_string.strip()
