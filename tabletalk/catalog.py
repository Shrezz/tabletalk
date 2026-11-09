"""The shelf: each game owns its sources, search index, and guide topics."""
import json
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


@dataclass(frozen=True)
class Game:
    id: str
    name: str
    edition: str
    players: str
    pdf: str
    digest: str
    directory: Path
    setup: tuple[str, ...]
    refresher: tuple[str, ...]
    examples: tuple[str, ...]
    decisions: tuple[str, ...]
    diagram: tuple[str, int]
    metadata_url: str | None = None

    @property
    def diagram_link(self):
        label, page = self.diagram
        return f"[{label} · p. {page} ↗]({self.pdf}#page={page})"


CATAN = Game(
    "catan", "CATAN", "2020 English rulebook", "3–4",
    "https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf",
    "3fed941bf202314ed462d4d0cdfb0384c97fe04166b48a7186833b3f6f4ac024", DATA,
    ("board", "pieces", "supply", "starting-hand"), ("win", "turn", "production", "seven"),
    ("How many players can play?", "When does a player win?", "What happens on a 7?"),
    ("How should I choose my opening settlements?", "Should I upgrade to a city or build another settlement?"),
    ("Open the beginner board diagram", 3), "https://www.catan.com/understand-catan/game-rules",
)
PANDEMIC = Game(
    "pandemic", "Pandemic", "English rulebook · © 2012", "2–4",
    "https://www.boardgamecapital.com/game_rules/pandemic.pdf",
    "d8faa02f8e0eea00dcdaa15c962ba091a24a7c4b8522c182e81d035ce3bf95cd", DATA / "pandemic",
    ("board", "seed", "starting-hand", "difficulty", "first-player"), ("win", "turn", "outbreak", "lose"),
    ("How many players can play?", "Do we need to eradicate every disease to win?", "What happens in an outbreak?"),
    ("I'm in a city with three blue cubes. Should I treat now or head for a research station?",
     "How should we decide which teammate collects the cards for a cure?"),
    ("Open the setup diagram", 2),
)
GAMES = {game.id: game for game in (CATAN, PANDEMIC)}


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    page: int
    answer: str
    queries: list[str]
    game: Game
    extra_pages: tuple[int, ...] = ()

    @property
    def url(self) -> str:
        return f"{self.game.pdf}#page={self.page}" if self.page else self.game.metadata_url

    @property
    def citation(self) -> str:
        return f"{self.title} · p. {self.page}" if self.page else f"{self.game.name} · Official rules catalog"


def load_rules(game: Game = CATAN) -> list[Rule]:
    rows = json.loads((game.directory / "rules.json").read_text())
    return [Rule(r["id"], r["title"], r["page"], r["answer"], r["queries"], game,
                 tuple(ref["page"] for ref in r.get("also", ()))) for r in rows]
