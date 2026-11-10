# Tabletalk

A phone-friendly rules companion for **CATAN** and **Pandemic**, built with Streamlit. Pick a tile to ask a rule, walk through setup, get a refresher, or ask the strategy coach about a move. Each game has its own searchable rulebook, citations, conversations and setup progress.

[Architecture and request flow](docs/architecture.md) diagrams show how the rulebooks are indexed, how rules chat selects a cited answer, and where the strategy coach calls the local LLM.

| Game | Source on the shelf | Try asking |
| --- | --- | --- |
| CATAN · 3–4 players | [2020 English base-game rulebook](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf) and [publisher’s edition catalog](https://www.catan.com/understand-catan/game-rules) | “When does a person win?” → 10 or more victory points on your own turn (p. 5). |
| Pandemic · 2–4 players | [Eight-page English base-game rulebook, © 2012 Z-Man Games](https://www.boardgamecapital.com/game_rules/pandemic.pdf) | Ask the same question → everyone wins immediately on the fourth cure, even with cubes on the board (p. 7). |

## Run it

From this directory, with Python 3.12:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Open the URL printed in the terminal. If you already use **uv**, the equivalent one-command launch is:

```sh
uv run --python 3.12 --with-requirements requirements.txt streamlit run app.py --server.address 127.0.0.1
```

**To use a phone:** on your private Wi-Fi, start Streamlit with `--server.address 0.0.0.0 --server.port 8501` instead. Open `http://<your-computer-LAN-IP>:8501` in the phone’s browser on the same network. The local-only address is not reachable from a phone. Stop the server with Ctrl-C.

The embedding model and both search indexes are included. Rules chat and both guides run locally without an LLM. A citation opens the selected game’s source in your browser. Append `?game=pandemic` or `?game=catan` to the local URL to open a game directly.

## Strategy coach

Open the **Strategy** tab and describe a decision. For example: *“My entire hand is 3 ore and 2 grain. Should I upgrade my settlement on a 6 or save for another settlement?”* Follow up with a changed board condition. The coach shows a suggested play, its rationale, a tradeoff, and expandable rule references. Its recommendations are model judgments, not official rulings or a solved optimal strategy.

For Pandemic, try: *“I’m the Scientist at a research station with four blue City cards. Blue is the last uncured disease. Should I treat or discover a cure?”* The coach receives Pandemic mechanics and your team’s stated position.

Only this tab calls an LLM. The coach uses a LangChain `ChatPromptTemplate` to put the game instructions and retrieved evidence in separate messages. LangChain’s [ChatOllama integration](https://docs.langchain.com/oss/python/integrations/chat/ollama) makes one request to local Ollama at `127.0.0.1:11434` with a JSON schema specific to that turn’s sources. The app checks the result before displaying advice. Rules chat still uses the local MiniLM/BM25 retriever without invoking a language model. On a phone, the model still runs on the computer hosting Streamlit. The default local model is **gemma4:12b**; no API key is needed. On a fresh machine:

1. Start [Ollama](https://ollama.com/download) (or run `ollama serve`).
2. Run `ollama list`. If needed, install the default with `ollama pull gemma4:12b`, or choose an already installed local chat model that supports structured outputs via `export TABLETALK_OLLAMA_MODEL=<model-tag>` before starting Streamlit.
3. Run Streamlit as above. The initial model download requires internet; local inference does not. Opening the tab does not load the LLM until you submit a strategy question.

The coach retrieves the current question and each side of an explicit comparison, then supplies the reviewed mechanics and up to two recent strategy turns. In CATAN, for an explicitly enumerated complete hand, a local cost check supplies a menu for the builds under discussion. The model chooses a plan and explains its strategic value; the app writes the payment condition from the actual costs. It does not track the board or other players’ hands. The server accepts only source IDs from the provided evidence and builds links itself. This checks citation provenance, not whether every generated claim follows from the source. If the model is unavailable or returns unusable references, no strategy ruling is substituted; rules chat remains available.

## Try it in CATAN

- **How many players can play?** → 3–4 in the base game; opens the edition catalog.
- **When does a person win?** → 10 or more points on your own turn; opens page 5.
- **What happens on a 7?** → discarding, moving the robber, and stealing; opens page 5.
- **Can I build a ship in Seafarers?** → explains that the extension is outside this edition.
- **What’s needed for basic setup?** → a cited beginner checklist in either chat, including the board diagram; no model call.
- **Set us up** → five steps, including a direct link to the beginner board diagram.

## Try it in Pandemic

- **What’s needed for basic setup?** → set the board, infect nine cities, deal roles and hands, prepare the Player deck, and choose the first player. The guide links to pp. 2–3.
- **What happens in an outbreak?** → spread to connected cities and resolve chain outbreaks; the same city cannot outbreak twice from the same Infection card (p. 7).
- **How many cards does the Scientist need?** → four matching City cards at a research station, with links to the role and cure action (pp. 8 and 4).
- **How do I set up Pandemic Legacy?** → declines; the linked base-game book does not cover Legacy.

## Code map

| Location | Responsibility |
| --- | --- |
| `app.py` | Streamlit entry point. |
| `tabletalk/catalog.py` | Rule data, edition, and citation URLs. |
| `tabletalk/ingestion/` | Check the source PDF, clean text, extract rule spans, and build the search index. |
| `tabletalk/retrieval/` | Local MiniLM encoder, keyword normalization, and hybrid search. |
| `tabletalk/answering/` | Decide whether to return a reviewed ruling, offer topics, or decline. |
| `tabletalk/strategy/` | Build strategy context, check explicit hand costs, format the LangChain prompt, call local Ollama, validate advice and sources. |
| `tabletalk/ui/` | Game shelf, chat history, setup steps, refresher, and original tile artwork. |
| `data/` | Reviewed rule definitions, compressed index, and embedding model. |
| `tests/` | Streamlit flow tests, example questions, and evaluation runner. |

## Week 2 framework

**One-liner:** Tabletalk helps new and returning players set up CATAN or Pandemic and resolve rules questions from the selected base-game rulebook in a mobile chat, targeting ≥95% of direct answers fully supported by their citations and a warm rules response below two seconds at p95. Strategy generation has a separate latency budget (90-second request timeout).

| Decision | Implementation |
| --- | --- |
| Use case | Get a first table set up, refresh returning players, or settle one rule at a time. |
| Corpus | CATAN: the 16-page [Game Rules & Almanac](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf). The [CATAN edition catalog](https://www.catan.com/understand-catan/game-rules) separately supports player count and the 5–6-player extension label. Pandemic: the eight-page English base-game book linked above; setup and components, turns, actions, infection and outbreaks, victory and defeat, and the seven roles. |
| Ingestion and cleaning | Extract PDF text by page, normalize spacing and cross-reference symbols, then select reviewed start/end anchors. Diagram-dependent instructions link to the original diagram; the app does not interpret artwork as prose. |
| Freshness | The source for each game is a pinned edition, checked by SHA-256 on every rebuild. There is no scheduled refresh: a maintainer reviews changed rules and publishes the new index together with the catalog before that edition is served. |
| Chunking and embedding | CATAN has 32 curated PDF topics and one catalog topic; Pandemic has 27 PDF topics. A chunk is a complete rule or procedure with conditions; MiniLM embeds its passage, short answer, heading, and example phrasings separately so a short question need not resemble a whole paragraph. Encoder inputs are capped at 256 tokens. |
| Retrieval | Store normalized 384-dimensional vectors and per-rule word counts in a compressed NumPy index. Normalize table language on both sides of the index (for example, “swap”/“trade” and “far apart”/“distance”). Search only the selected game, combining cosine similarity (63%) with normalized BM25 (37%); keep the best three topics. |
| Answer and refusal | Return the selected rule’s reviewed wording and citation. The original score and margin cutoffs still apply. Weak or close matches and questions with multiple unrecognized terms offer topics; unclear starting setups ask which map you are using. Unsupported variants yield no ruling. Simple pronoun follow-ups can reuse the last answered topic. |
| Faithfulness and latency | Check that all factual claims **and relevant exceptions** are supported, and that the selected rule resolves the question. Track answer coverage and correct non-answers separately; a refusal does not count as a faithful answer. |

The rules path uses deterministic answer assembly and covers only indexed topics. Strategy uses retrieval-augmented generation over those same rules. Neither path validates arbitrary board positions or covers other editions. Similarity scores are routing signals, not probabilities.

## Rebuild from the source

Edit the human-readable definitions in `data/rules.json` (CATAN) or `data/pandemic/rules.json` (Pandemic) to change a ruling. Each PDF definition has a source page and a pair of extraction anchors. Optional additional spans support rulings that depend on another page. See the rule on page 5 for an example that keeps the own-turn exception attached.

```sh
python -m pip install -r requirements-ingest.txt
curl -fL https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf -o catan-2020.pdf
python -m tabletalk.ingestion.build --game catan catan-2020.pdf
curl -fL https://www.boardgamecapital.com/game_rules/pandemic.pdf -o pandemic.pdf
python -m tabletalk.ingestion.build --game pandemic pandemic.pdf
```

The builder fails if the PDF differs from the reviewed copy or an anchor is missing. The runtime checks that the index matches the rule catalog. Restart Streamlit after rebuilding. The distribution includes derived vectors and term counts, not the publisher’s PDF.

## Run the checks

To check **which rule chunks retrieval actually returns**, run `python -m tests.evaluate_retrieval`. See [retrieval quality: results, misses and how to add cases](tests/RETRIEVAL.md) for rank, source-page and strategy-prompt checks.

```sh
python -m unittest discover -s tests
python -m tests.evaluate
python -m tests.evaluate --suite calibration.json
python -m tests.evaluate --suite transfer.json
python -m tests.evaluate --suite holdout.json
python -m tests.evaluate --suite pandemic.json
```

The Pandemic regression suite has 17 supported questions and 5 unsupported cases. It measures topic and page selection, not the quality of every possible question or generated strategy. Streamlit flow tests also switch games within one session to check source and history isolation.

For CATAN, the 18 calibration and 20 original evaluation questions are regression suites. The 26-case transfer suite stresses paraphrases, ambiguity and unsupported premises; it informed the safeguards. The final 16-case holdout was scored separately. See [the seven previously missed questions and evaluation results](tests/RESULTS.md) for exact outcomes and limits.

## Model

The included local encoder is the quantized [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41) (Apache 2.0). The source artifact is `onnx/model_quint8_avx2.onnx`; the CPU runtime was exercised on Apple Silicon. See the bundled [model card](data/encoder/MODEL_CARD.md) and [license](data/encoder/LICENSE). CATAN, Pandemic and their rulebooks belong to their respective owners; this is an independent learning project.
