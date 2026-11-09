"""Cases where the base rulebook requires more context or has a different premise."""
import re

from tabletalk.catalog import GAMES
from tabletalk.retrieval.words import words

OUTSIDE = re.compile(r"\b(seafarers?|barbarians?|pirates?|starfarers?|house rules?|"
                     r"catan junior|cities\s*(and|&)\s*knights|chess|monopoly board game)\b", re.I)
# The component list (p. 2) contains one robber. An extra piece changes the game.
EXTRA_ROBBER = re.compile(r"\b(second|extra|additional|another) robber\b|\b(two|2|multiple) robbers\b", re.I)
FIRST_PLAYER = re.compile(r"\bwho (?:starts?|begins?|opens?)\b|\bfirst (?:turn|player|roll|move)\b|"
                          r"\b(?:go(?:es)?|rolls?|moves?|plays?) first\b", re.I)
SETUP_TYPE = re.compile(r"\b(beginner|beginners|starter|printed|fixed|recommended|random\w*|variable|experienced)\b", re.I)


def missing_context(question: str, topic: str) -> tuple[str, tuple[str, ...]] | None:
    if topic in {"starting-hand", "opening"} and FIRST_PLAYER.search(question) and not SETUP_TYPE.search(question):
        return ("Which setup are you using? The beginner map and variable setup choose the first player differently.",
                ("starting-hand", "opening"))
    if set(words(question)) == {"bank"}:
        return ("Are you asking about a bank trade or about paying out resources?",
                ("harbor", "shortage"))
    return None

PANDEMIC_VARIANTS = re.compile(
    r"\b(legacy|season [012]|on the brink|in the lab|state of emergency|hot zone|iberia|"
    r"fall of rome|reign of cthulhu|rapid response|bio.?terrorist|virulent strain|"
    r"house rules?|expansions?|chess|monopoly)\b", re.I)
CATAN_MECHANICS = re.compile(r"\b(robber|settlements?|victory points?|longest road|largest army)\b", re.I)
PANDEMIC_MECHANICS = re.compile(r"\b(epidemics?|outbreaks?|research stations?|disease cubes?)\b", re.I)


def out_of_scope(game, question: str) -> bool:
    if any(re.search(rf"\b{key}\b", question, re.I) for key in GAMES if key != game.id):
        return True
    if game.id == "catan":
        return bool(OUTSIDE.search(question) or EXTRA_ROBBER.search(question) or PANDEMIC_MECHANICS.search(question))
    return bool(PANDEMIC_VARIANTS.search(question) or CATAN_MECHANICS.search(question))
