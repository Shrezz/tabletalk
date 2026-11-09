"""Rebuild: python -m tabletalk.ingestion.build /path/to/catan-2020.pdf"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from tabletalk.retrieval.encoder import Encoder

from tabletalk.catalog import CATAN, GAMES, Game
from tabletalk.ingestion.pdf import extract_span, read_pages
from tabletalk.retrieval.words import words


def build(pdf: Path, game: Game = CATAN) -> None:
    pages = read_pages(pdf, game)
    catalog = (game.directory / "rules.json").read_bytes()
    records = json.loads(catalog)
    texts, owners, counts = [], [], []
    for i, row in enumerate(records):
        if row["page"]:
            try:
                spans = [extract_span(pages[ref["page"] - 1], ref["start"], ref["end"])
                         for ref in (row, *row.get("also", ()))]
            except (ValueError, IndexError) as error:
                raise ValueError(f"Missing source for {row['id']} on page {row['page']}") from error
        elif game == CATAN:
            # Reviewed publisher metadata, not a claim extracted from the PDF.
            spans = ["CATAN Game Rules and Almanac (3-4 Players); Game Rules 5/6 Players"]
        else:
            raise ValueError(f"Missing PDF page for {row['id']}")
        samples = [row["title"], row["answer"], *spans, *row["queries"]]
        texts.extend(samples)
        owners.extend([i] * len(samples))
        counts.append(dict(Counter(words(" ".join(samples), game.id))))

    encoder = Encoder()
    vectors = encoder.encode(texts)
    np.savez_compressed(game.directory / "index.npz", vectors=vectors, owners=owners,
                        counts=json.dumps(counts), catalog_hash=hashlib.sha256(catalog).hexdigest())
    print(f"Indexed {len(records)} rules, {len(pages)} PDF pages, {vectors.shape[1]}-dimensional embeddings.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--game", choices=GAMES, default="catan")
    args = parser.parse_args()
    build(args.pdf, GAMES[args.game])
