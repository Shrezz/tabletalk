# CATAN retrieval: seven fewer follow-ups

On the original 20-question evaluation, correct direct rulings rose from **7/14 to 14/14** answerable questions. All six unsupported questions still received no asserted ruling. These questions informed the change: they are regression checks, not a blind accuracy estimate.

## The seven questions

Each one previously opened a topic chooser. The rulings themselves were not rewritten; the new index finds the relevant, already reviewed passage. Page numbers below are both PDF and printed page numbers.

| Question | Why lookup hesitated before | Direct ruling now |
| --- | --- | --- |
| What order do rolling, building and trading happen in? | The turn summary ranked first, but separate actions diluted the sequence match. | Roll for production, optionally trade, then build or buy development cards. [Turn overview, p. 4](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf#page=4) |
| Who gets the first roll if we use the printed beginner board? | Beginner and variable setup were close; the type of map is decisive. | On the beginner map, the oldest player takes the first turn. [Beginner setup, p. 13](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf#page=13) |
| Do I still take wheat on somebody else's dice roll? | Turn order outranked production. The key was who may collect, not who rolls. | Yes, if your building borders a matching, unblocked producing field: 1 grain per settlement, 2 per city. [Production, p. 10](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf#page=10) |
| How far apart do two settlements have to be? | A question about distance almost tied with the piece inventory because both mention two settlements. | Build on an empty intersection; none of the neighboring intersections may have a settlement or city, even yours. [Building a settlement, p. 5](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf#page=5) |
| Can I swap three matching cards at a generic harbor? | The correct harbor topic ranked first but missed the direct-answer cutoff. | On your turn, a settlement or city on a generic harbor lets you exchange three of one resource for one of your choice. [Maritime trade, p. 4](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf#page=4) |
| If the robber is on my wheat tile, does that tile still produce? | The wheat tile matched the terrain table better than the blocking rule. | No. The occupied hex produces nothing for adjacent buildings while the robber stays there. [Robber, p. 11](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf#page=11) |
| If two of us are owed brick but the bank has too few cards, who takes them? | The shortage was a weak match, competing with supply setup. | Neither gets brick when the bank cannot pay both. If only one player is affected they take what remains; other resources still pay out. [Shortages, p. 10](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf#page=10) |

## What changed

- The same vocabulary is used on both sides of the keyword index. Trading, swapping and exchanging now match; distance, shortage, and off-turn wording retain their meaning as phrases. The encoder normalizes equivalent possessives such as “somebody else’s roll” and “another player’s roll.”
- Added short, source-supported descriptions of the decisions covered by eight entries, including the competing variable-setup rule. Rebuilt the index from the pinned PDF. No test questions were inserted verbatim; there is no new model, network call, or lower score/margin cutoff.
- When setup is unspecified, a first-player lookup offers the beginner and variable rules. A bare bank question asks about trade versus payout. Multiple unfamiliar terms can force a topic choice; an extra robber is outside the one-robber base game. These checks reduce some incorrect direct rulings; they do not recognize every unsupported premise.

## Checks and limits

A correct direct ruling must select the labeled rule and page. A wrong direct ruling includes both a wrong answer to an in-scope question and asserting a rule on an unsupported or ambiguous question. A chooser or refusal is not a direct answer. Where one topic can be chosen, the evaluation does not assume the player picked it.

| Suite | Correct direct / answerable | Correct rule in top 3 | Incorrect direct, all cases |
| --- | --- | --- | --- |
| Original evaluation (20) | 7 → **14/14** | 14 → 14/14 | 0 → 0 |
| Earlier calibration (18) | 12 → **12/12** | 12 → 12/12 | 0 → 0 |
| Additional paraphrases and ambiguity checks (26) | 2 → **5/14** | 14 → 14/14 | 3 → 0 |
| Final holdout (16), scored after changes | **3/8** | 7/8 | 0 |

The additional 26 cases were written before editing and then used to troubleshoot safeguards. The final holdout was not used to tune scores or routing. Of its five answerable questions without a direct answer, four offered the correct topic; the turn-order question about “swapping cards or putting down a road” missed it entirely. All eight unsupported or ambiguous holdout questions received no asserted ruling. The warm backend p95 on this machine was about 2 ms, excluding browser and network time.

The seven improved rulings were checked against their cited passages for conditions and exceptions. These small authored suites measure behavior on the listed examples, not a population-wide faithfulness percentage. Before broadening the direct-answer threshold, collect independently phrased questions from actual players, especially near-misses about setup, card payouts, and variants.

Run `python -m tests.evaluate` or select `--suite calibration.json`, `--suite transfer.json`, or `--suite holdout.json` for per-question results. `python -m unittest discover -s tests` also checks direct answers, clarifications, and Streamlit flows.

## Strategy coach

Strategy is evaluated separately from rule lookup. A live two-turn Streamlit session called the installed Ollama `gemma4:12b`, compared a city upgrade with saving for a settlement, and used a follow-up about a contested brick site. With a complete hand of 3 ore and 2 grain, the payment menu permitted the city upgrade and marked a new settlement as short 1 brick, 1 lumber, and 1 wool. The model selected a plan and supplied the explanation. Source links were resolved by the app from the retrieved cards (including p. 5 for build costs and p. 10 for production).

Offline regression tests exercise evidence for both sides of a choice, conversation context, fundable versus unfundable purchases, rejection of unusable citations, scope checks without an LLM call, provider errors, and isolation from rules chat. This is a functional check, not a benchmark of winning percentage, tactical optimality, or complete factual accuracy. The model’s strategic explanations can still be wrong even when its source links are valid.
