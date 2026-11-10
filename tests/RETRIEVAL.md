# Does Tabletalk retrieve the right chunk?

On these 24 labeled rules questions, the expected chunk ranked first **21/24** times and appeared in the first three **23/24** times. A chunk here is one reviewed rule topic: the retriever combines matches against its heading, source passage, answer and alternate phrasings. It doesn't return individual PDF sentences. No retrieval weights, aliases or cutoffs were changed for this evaluation.

| Game | Correct first | Correct in first 3 | MRR@3 | No ruling on unsupported questions | Complete strategy evidence |
| --- | ---: | ---: | ---: | ---: | ---: |
| CATAN | 10/12 | 11/12 | 0.875 | 3/3 | 2/2 |
| Pandemic | 11/12 | 12/12 | 0.958 | 3/3 | 2/2 |

## Where it goes wrong

| Question | Expected evidence | Retrieved result and effect |
| --- | --- | --- |
| CATAN: “What comes first on my turn: swapping cards or putting down a road?” | Turn order, p. 4 | The top three were starting resources, Longest Road and preparing the supply. Rules chat offered these topics; none resolved the question. |
| CATAN: “Someone built a village in the middle of my longest route. Who keeps the award?” | Interrupted road, p. 9 | Generic Longest Road ranked first. The specific rule ranked second and was offered in the chooser. Both are on p. 9, so a page-only test would miss the difference. |
| Pandemic: “Who can hand me a City card that doesn't match the city we're standing in?” | Researcher, p. 8 | The general Share Knowledge rule ranked first and was shown directly. It mentions the Researcher, but doesn't explain that any City card may **leave** that role's hand. The full exception ranked second. |

## Reproduce and extend

From the project root after installing the usual requirements:

```sh
python -m tests.evaluate_retrieval           # metrics by game; show misses with ranks and actual topics
python -m tests.evaluate_retrieval --verbose # include successful cases
python -m tests.evaluate_retrieval --json    # machine-readable per-question results
python -m unittest tests.test_chunk_ranking # enforce the measured regression floors
```

Add player questions to [retrieval_cases.json](retrieval_cases.json). Label them from the edition **before** looking at system results. Keep evaluation questions out of the indexing aliases. The runner uses the bundled models and indexes; it needs neither a network connection nor Ollama.

- **Lookup:** Each question has one or more acceptable rule IDs, each paired with a page that must appear in its citation metadata. Either acceptable topic may count, but a different topic on the same page does not. Page 0 means the publisher catalog. Hit@1 and Hit@3 ask whether an acceptable source appears within that cutoff. MRR@3 averages 1, ½, ⅓ or 0 for first relevant rank 1, 2, 3 or absent. The displayed answer is logged separately and does not affect those scores.
- **No supporting chunk:** Raw similarity search can return neighbors even when nothing answers the question. For these six questions, measure whether rules chat avoids asserting a ruling or giving a setup guide. A clarification counts as no ruling. These cases are excluded from ranking metrics.
- **Strategy:** Each question lists evidence groups. All groups must appear in the actual prompt built by the coach; alternative rules within one group are interchangeable. Only the generation call is stubbed. This checks what evidence the model receives, not whether it chooses the right move.

These are authored regression cases, including one known CATAN holdout miss, not an estimate over all player questions. The regression tests protect the current first-choice rate per game, each currently successful top-three lookup, unsupported questions and complete strategy prompts. Use fresh questions from real games to estimate how well retrieval generalizes.
