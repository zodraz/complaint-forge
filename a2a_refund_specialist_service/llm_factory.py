import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = (
    os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    or os.getenv("AZURE_OPENAI_DEPLOYMENT")
)
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")


def get_chat_llm(*, temperature: float = 0) -> Any:
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

    from crewai import LLM

    kwargs = {
        "model": f"azure/{AZURE_OPENAI_DEPLOYMENT_NAME}",
        "endpoint": AZURE_OPENAI_ENDPOINT,
        "api_key": AZURE_OPENAI_API_KEY,
        "temperature": temperature,
    }
    if AZURE_OPENAI_API_VERSION:
        kwargs["api_version"] = AZURE_OPENAI_API_VERSION

    return LLM(**kwargs)
