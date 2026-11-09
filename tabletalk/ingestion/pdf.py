"""Extract verified spans from this edition; reject a changed or mismatched PDF."""
import hashlib
import re
import unicodedata
from pathlib import Path

from tabletalk.catalog import Game


def clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\u00ad", "")
    text = re.sub(r"\bY\s+ou\b", "You", text)
    text = re.sub(r"\s*\bY\b(?=[.,:;!?)\s])", "", text)
    return " ".join(text.split())


def read_pages(path: Path, game: Game) -> list[str]:
    from pypdf import PdfReader  # Only needed to rebuild the index.
    if hashlib.sha256(path.read_bytes()).hexdigest() != game.digest:
        raise ValueError(f"Wrong source PDF for {game.name} ({game.edition}). Review the rules before changing editions.")
    return [clean(page.extract_text()) for page in PdfReader(path).pages]


def extract_span(page: str, start: str, end: str) -> str:
    first = page.casefold().index(start.casefold())
    last = page.casefold().index(end.casefold(), first) + len(end)
    return page[first:last]
