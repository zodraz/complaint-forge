import os
from typing import Any

from dotenv import load_dotenv

from crewai import LLM

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = (
    os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    or os.getenv("AZURE_OPENAI_DEPLOYMENT")
)
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

USE_LITELLM = os.getenv("USE_LITELLM", "false").lower() == "true"
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "sk-1234")
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "gpt-4o")


def get_chat_llm(*, temperature: float = 0) -> Any:
    if USE_LITELLM:
        kwargs = {
            "model": LITELLM_MODEL,
            "base_url": LITELLM_BASE_URL,
            "api_key": LITELLM_API_KEY,
            "default_headers": {"x-litellm-model": LITELLM_MODEL},
            "temperature": temperature,
        }
        if AZURE_OPENAI_API_VERSION:
            kwargs["api_version"] = AZURE_OPENAI_API_VERSION
        return LLM(**kwargs)

    missing = [
        name
        for name, value in {
            "AZURE_OPENAI_API_KEY": AZURE_OPENAI_API_KEY,
            "AZURE_OPENAI_ENDPOINT": AZURE_OPENAI_ENDPOINT,
            "AZURE_OPENAI_DEPLOYMENT_NAME": AZURE_OPENAI_DEPLOYMENT_NAME,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing Azure OpenAI configuration: " + ", ".join(missing)
        )

    kwargs = {
        "model": f"azure/{AZURE_OPENAI_DEPLOYMENT_NAME}",
        "endpoint": AZURE_OPENAI_ENDPOINT,
        "api_key": AZURE_OPENAI_API_KEY,
        "temperature": temperature,
    }
    if AZURE_OPENAI_API_VERSION:
        kwargs["api_version"] = AZURE_OPENAI_API_VERSION

    return LLM(**kwargs)
