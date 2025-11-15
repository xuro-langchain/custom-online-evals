import os
import requests
from typing import Dict
from dotenv import load_dotenv
from langsmith import Client, traceable

load_dotenv(".env")

client = Client()

# LangSmith Variables
LANGSMITH_API_URL = os.getenv("LANGSMITH_API_URL", "https://api.smith.langchain.com")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Render Variables
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_OWNER_ID = os.getenv("RENDER_OWNER_ID")  # Your Render workspace ID
RENDER_API_BASE = "https://api.render.com/v1"

SERVICE_NAME = os.getenv("RENDER_SERVICE_NAME", "custom-online-evals")
SERVICE_TYPE = "web_service"  # For web services
RUNTIME = "python"  # Python runtime

REPO_URL = os.getenv("REPO_URL")
BRANCH = os.getenv("REPO_BRANCH", "main")


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
    
def validate_env_vars(check_render: bool = False) -> None:
    """
    Validate that all required environment variables are set.
    
    Args:
        check_render: If True, also validate Render-related environment variables.
                     If False (default), only validate LangSmith and OpenAI variables.
    
    Raises ValueError with descriptive message if any are missing.
    """
    missing_vars = []
    
    # Always required variables
    if not LANGSMITH_API_KEY:
        missing_vars.append("LANGSMITH_API_KEY")
    
    if not OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")
    
    # Render variables (only checked if deploying)
    if check_render:
        if not RENDER_API_KEY:
            missing_vars.append("RENDER_API_KEY")
        
        if not REPO_URL:
            missing_vars.append("REPO_URL (or RENDER_REPO_URL)")
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please set these in your .env file or environment."
        )


@traceable
def first_run(question: str) -> str:
    """Initial trace to set up the project."""
    return "Hello, world!"


def setup_project() -> None:
    first_run("Welcome to LangSmith!")
    
