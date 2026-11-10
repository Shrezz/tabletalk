"""LangChain generation boundary for the local strategy coach."""
import os
from functools import lru_cache

from httpx import RequestError
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from langsmith import tracing_context
from ollama import ResponseError

BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "gemma4:12b"


class CoachError(Exception):
    """A problem the UI can explain without showing a traceback."""


@lru_cache(maxsize=1)
def _model(name: str) -> ChatOllama:
    return ChatOllama(model=name, base_url=BASE_URL, reasoning=False,
                      temperature=0.1, num_predict=500, num_ctx=4096,
                      client_kwargs={"timeout": 90, "trust_env": False})


def generate(messages: list[BaseMessage], schema: dict) -> dict:
    name = os.environ.get("TABLETALK_OLLAMA_MODEL", "").strip() or DEFAULT_MODEL
    if name.endswith((":cloud", "-cloud")):
        raise CoachError("Choose an installed local model with TABLETALK_OLLAMA_MODEL.")
    try:
        # Bind per turn: valid source IDs and any affordable plans depend on this position.
        with tracing_context(enabled=False):
            chain = _model(name).with_structured_output(schema, method="json_schema", include_raw=True)
            response = chain.invoke(messages)
    except ResponseError as exc:
        if exc.status_code == 404:
            raise CoachError(f"Ollama couldn’t find {name}. Install it or set TABLETALK_OLLAMA_MODEL to an installed chat model.") from exc
        raise CoachError(f"Ollama couldn’t run {name} (HTTP {exc.status_code}). Check that the model loads in Ollama.") from exc
    except (RequestError, OSError) as exc:
        raise CoachError("The local coach didn’t respond. Check that Ollama is running and try again.") from exc
    except ValueError as exc:
        raise CoachError("The model returned an unreadable response. Please try again.") from exc

    if response["raw"].response_metadata.get("done_reason") == "length":
        raise CoachError("The coach ran out of space. Try one decision at a time.")
    if response["parsing_error"] or not isinstance(response["parsed"], dict):
        raise CoachError("The model returned an unreadable response. Please try again.")
    return response["parsed"]
