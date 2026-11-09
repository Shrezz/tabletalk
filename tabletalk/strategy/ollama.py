"""One call to a locally installed Ollama chat model. No cloud client or API key."""
import json
import os
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

ENDPOINT = "http://127.0.0.1:11434/api/chat"
DEFAULT_MODEL = "gemma4:12b"


class CoachError(Exception):
    """A problem the UI can explain without showing a traceback."""


def generate(messages: list[dict], schema: dict) -> dict:
    model = os.environ.get("TABLETALK_OLLAMA_MODEL") or DEFAULT_MODEL
    if model.endswith((":cloud", "-cloud")):
        raise CoachError("Choose an installed local model with TABLETALK_OLLAMA_MODEL.")
    body = {"model": model, "messages": messages, "format": schema, "stream": False,
            "think": False, "options": {"temperature": 0.1, "num_predict": 500, "num_ctx": 4096}}
    request = Request(ENDPOINT, data=json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    try:
        # A loopback request should never be forwarded to an HTTP proxy.
        with build_opener(ProxyHandler({})).open(request, timeout=90) as response:
            envelope = json.load(response)
        if envelope.get("done_reason") == "length":
            raise CoachError("The coach ran out of space. Try one decision at a time.")
        return json.loads(envelope["message"]["content"])
    except HTTPError as exc:
        if exc.code == 404:
            raise CoachError(f"Ollama couldn’t find {model}. Install it or set TABLETALK_OLLAMA_MODEL to an installed chat model.") from exc
        raise CoachError(f"Ollama couldn’t run {model} (HTTP {exc.code}). Check that the model loads in Ollama.") from exc
    except (HTTPException, URLError, OSError) as exc:
        raise CoachError("The local coach didn’t respond. Check that Ollama is running and try again.") from exc
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise CoachError("The model returned an unreadable response. Please try again.") from exc
