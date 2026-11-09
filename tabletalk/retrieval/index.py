"""Exact cosine search and BM25 over a small, edition-specific index."""
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math

import numpy as np
from tabletalk.retrieval.encoder import Encoder

from tabletalk.catalog import GAMES, Rule, load_rules
from tabletalk.retrieval.words import words


@dataclass(frozen=True)
class Hit:
    rule: Rule
    score: float
    dense: float
    coverage: float
    unfamiliar: int


class RuleIndex:
    def __init__(self, game_id="catan"):
        self.game = GAMES[game_id]
        self.rules = load_rules(self.game)
        self.by_id = {r.id: r for r in self.rules}
        self.model = Encoder()
        with np.load(self.game.directory / "index.npz", allow_pickle=False) as index:
            if str(index["catalog_hash"]) != hashlib.sha256((self.game.directory / "rules.json").read_bytes()).hexdigest():
                raise ValueError("Rule catalog changed; rebuild the index before starting the app.")
            self.vectors = index["vectors"]
            self.owners = index["owners"]
            self.counts = json.loads(str(index["counts"]))
        n = len(self.rules)
        document_frequency = Counter(w for counts in self.counts for w in counts)
        self.idf = {w: math.log1p((n - df + .5) / (df + .5))
                    for w, df in document_frequency.items()}
        self.lengths = [sum(c.values()) for c in self.counts]
        self.avg_length = sum(self.lengths) / n

    def search(self, query: str, k: int = 3) -> list[Hit]:
        terms = set(words(query, self.game.id))
        if not terms:
            return []
        v = self.model.encode([query])[0]
        scores = self.vectors @ v
        dense = np.zeros(len(self.rules))
        np.maximum.at(dense, self.owners, scores)
        total_idf = sum(self.idf.get(w, 2.5) for w in terms)
        unfamiliar = len(terms.difference(self.idf))
        hits = []
        for i, (rule, counts) in enumerate(zip(self.rules, self.counts)):
            matched = terms.intersection(counts)
            norm = 1.2 * (.25 + .75 * self.lengths[i] / self.avg_length)
            bm25 = sum(self.idf[w] * counts[w] * 2.2 / (counts[w] + norm) for w in matched)
            coverage = sum(self.idf[w] for w in matched) / total_idf
            score = .63 * dense[i] + .37 * bm25 / (2.2 * total_idf)
            hits.append(Hit(rule, float(score), float(dense[i]), coverage, unfamiliar))
        return sorted(hits, key=lambda h: -h.score)[:k]
