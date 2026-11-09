"""Shared, reviewed guides for questions that need more than one rule."""
import re

# Only generic overview requests use the checklist. Unrecognized qualifiers
# (e.g. "random", "robber", or another edition) stay with normal retrieval.
OVERVIEW_WORDS = set("""
a an and are base basic basics beginner beginners board can checklist do does
equipment explain first for game get give guide help how i in instructions is it lets
list materials me my need needed needs of our please prepare preparing ready required
requirements set setting setup show standard start starting step steps supplies table
the this through to up us walk we what whats work works you
""".split())


def is_basic_setup(question: str, game_id: str) -> bool:
    tokens = set(re.findall(r"[a-z0-9]+", question.lower().replace("’", "").replace("'", "")))
    setup = bool(tokens & {"setup", "prepare", "preparing"}) or (
        "up" in tokens and bool(tokens & {"set", "setting"})
    )
    return setup and tokens <= (OVERVIEW_WORDS | {game_id})


def setup_checklist(index) -> str:
    steps = [f"{n}. {index.by_id[key].answer}" for n, key in enumerate(index.game.setup, 1)]
    intro = ("For your first game, use the beginner map (Illustration A)." if index.game.id == "catan"
             else "For your first game of Pandemic, use introductory difficulty.")
    return intro + "\n\n" + "\n\n".join(steps)
