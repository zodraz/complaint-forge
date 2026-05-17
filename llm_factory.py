from langchain_openai import ChatOpenAI

from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_ENDPOINT,
)


def _azure_openai_base_url() -> str:
    endpoint = AZURE_OPENAI_ENDPOINT.rstrip("/")
    if endpoint.endswith("/openai/v1"):
        return endpoint + "/"
    return endpoint + "/openai/v1/"


def get_chat_llm(*, temperature: float = 0) -> ChatOpenAI:
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
        "model": AZURE_OPENAI_DEPLOYMENT_NAME,
        "base_url": _azure_openai_base_url(),
        "api_key": AZURE_OPENAI_API_KEY,
        "temperature": temperature,
    }

    return ChatOpenAI(**kwargs)
