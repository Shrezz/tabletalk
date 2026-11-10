# Does Tabletalk retrieve the right chunk?

On the original 24 labeled rules questions, first-place retrieval rose from **21/24 to 24/24** (top three: **23/24 to 24/24**). Each of the three repaired questions now receives the specific reviewed ruling directly in chat. A chunk is a rule topic, not a single PDF sentence.

| Original benchmark | Correct first, before → after | Correct in top 3 | MRR@3 | Correct direct answers | Wrong direct answers |
| --- | ---: | ---: | ---: | ---: | ---: |
| CATAN (12) | 10 → 12 | 11 → 12 | 0.875 → 1.000 | 5 → 7 | 0 → 0 |
| Pandemic (12) | 11 → 12 | 12 → 12 | 0.958 → 1.000 | 8 → 9 | 1 → 0 |

The original six unsupported questions still received no ruling, and all four strategy prompts still included the required evidence. These measurements use the same questions, labels, answer text and cutoffs as the [baseline](https://github.com/Shrezz/tabletalk/commit/976e4de7d34bc8fa27f8203eb39cc6aed7229ca8).

## The three misses

| Question | Expected rule and rank, before → after | What the player now gets |
| --- | --- | --- |
| CATAN: “What comes first on my turn: swapping cards or putting down a road?” | Turn order, p. 4: **4 → 1** | The normal turn sequence: roll, trade, then build. Previously, none of the three offered topics answered the question. |
| CATAN: “Someone built a village in the middle of my longest route. Who keeps the award?” | Interrupted road, p. 9: **2 → 1** | The rule for reassigning the card after a legal interruption, including ties. Previously, generic Longest Road (also p. 9) led the chooser. |
| Pandemic: “Who can hand me a City card that doesn't match the city we're standing in?” | Researcher, p. 8: **2 → 1** | The Researcher may give any City card to a player in the same city. The exception applies to cards leaving the Researcher's hand. Previously, chat answered with the ordinary sharing rule. |

We added two search descriptions per affected topic, describing the relative order of actions, the interrupted route and the direction of the card transfer. CATAN keyword normalization now treats “swapping” and “swapped” as trading. We rebuilt both indexes from their pinned PDFs; the embedding model, 63/37 search weights and confidence checks are unchanged.

## Does it transfer?

Before editing the indexes, we labeled a separate [set of paraphrases and nearby rules](retrieval_neighbors.json), including ordinary trading, ordinary card sharing and counting an uninterrupted fork. First-place matches rose from **6/12 to 8/12**; top-three matches rose from **10/12 to 12/12** (CATAN: 6/7 → 7/7; Pandemic: 4/5 → 5/5). Correct direct answers stayed at 3/12, while wrong direct answers fell from one to zero. All three unsupported variants still received no ruling.

For example, asking which role could pass the Paris card while both players are in Tokyo still ranks the Researcher second and asks the player to choose. The twelve new cases were scored separately, not used for a second tuning pass. Neither small, authored set estimates accuracy for all player questions.

## Reproduce and extend

From the project root after installing the usual requirements:

```sh
python -m tests.evaluate_retrieval           # metrics by game; show misses with ranks and actual topics
python -m tests.evaluate_retrieval --suite neighbors # separate transfer check
python -m tests.evaluate_retrieval --verbose # include successful cases
python -m tests.evaluate_retrieval --json    # machine-readable per-question results
python -m unittest tests.test_chunk_ranking # enforce the measured regression floors
```

Add player questions to [retrieval_cases.json](retrieval_cases.json). Label them from the edition **before** looking at system results. Keep evaluation questions out of the indexing aliases. The runner uses the bundled models and indexes; it needs neither a network connection nor Ollama.

- **Lookup:** Each question has one or more acceptable rule IDs, each paired with a page that must appear in its citation metadata. Either acceptable topic may count, but a different topic on the same page does not. Page 0 means the publisher catalog. Hit@1 and Hit@3 ask whether an acceptable source appears within that cutoff. MRR@3 averages 1, ½, ⅓ or 0 for first relevant rank 1, 2, 3 or absent. The displayed answer is logged separately and does not affect those scores.
- **No supporting chunk:** Raw similarity search can return neighbors even when nothing answers the question. For these six questions, measure whether rules chat avoids asserting a ruling or giving a setup guide. A clarification counts as no ruling. These cases are excluded from ranking metrics.
- **Strategy:** Each question lists evidence groups. All groups must appear in the actual prompt built by the coach; alternative rules within one group are interchangeable. Only the generation call is stubbed. This checks what evidence the model receives, not whether it chooses the right move.

The regression tests require first place on every original lookup and a direct correct ruling on the three repaired cases. For the separate paraphrase suite, the expected rule must appear in the top three; a clarification is allowed, a wrong ruling is not.
