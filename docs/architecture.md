# How Tabletalk answers a question

The player picks a game and a mode. **Ask a rule** finds a reviewed answer and shows its source. **Strategy** uses retrieval-augmented generation (RAG): it retrieves rules from the same game, gives them to a local language model along with the player's position, and asks it to recommend a move.

## 1. Architecture

```mermaid
flowchart TB
    subgraph Build["Before play · build one index per game"]
        PDF["Edition-specific rulebook PDF"] --> B["Verify PDF, extract rule passages,<br/>embed with MiniLM and count terms"]
        C["Reviewed rules.json<br/>Answers, page anchors and example questions"] --> B
        B --> I[("Game's index.npz<br/>Vectors, rule mappings and word counts")]
    end
    P["Player on phone or desktop"] --> UI["Streamlit · game shelf and chat"]
    UI --> R["Rules handler"]
    UI --> S["Strategy coach"]
    UI --> G["Setup and refresher guides"]
    R --> H["Hybrid search in the selected game<br/>63% cosine similarity + 37% normalized BM25"]
    S --> H
    I --> H
    C --> H
    C --> G
    S --> LC["LangChain · ChatPromptTemplate<br/>and schema-bound ChatOllama"]
    LC <-->|"One model call"| L["Local Ollama service<br/>Default: gemma4:12b"]
```

CATAN and Pandemic have separate catalogs and indexes; both use the same MiniLM encoder. The app searches local files, so it doesn't fetch or re-embed the rulebook on each question. The catalog provides the source links, including CATAN's publisher catalog for its player-count entry. Chat history is separate for each game and for rules versus strategy.

## 2. What happens in chat

```mermaid
sequenceDiagram
    actor P as Player
    participant A as Streamlit app
    participant R as Game retriever
    participant C as LangChain
    participant L as Local Ollama
    P->>A: Select a game and mode, then ask a question
    Note over A: Known unsupported variant? Decline here.<br/>Basic setup request? Return the cited checklist here.
    alt Ask a rule
        A->>R: Search the selected game for the question
        R-->>A: Top 3 rule topics and match scores
        alt Clear match
            A-->>P: Reviewed answer and source link
        else Ambiguous, weak or missing evidence
            A-->>P: Ask for context, offer topics or decline
        end
    else Strategy
        A->>R: Search the question and each side of a comparison
        R-->>A: Relevant rule cards
        A->>C: Game instructions, rule cards, player position and recent turns
        C->>L: System and user messages + JSON schema restricted to supplied IDs
        L-->>C: Model response
        C-->>A: Parsed advice, clarification or refusal
        A->>A: Validate the response and check cited IDs against supplied rules
        A-->>P: Suggested move, reason, tradeoff and app-built citations<br/>or a question, refusal or error
    end
```

**What gets retrieved?** For rules, the app scores each topic using its best MiniLM cosine match and its normalized BM25 keyword score. For strategy, the app starts with four topics for the whole question and adds two per side of an explicit comparison. It also includes relevant prior evidence, game-specific core rules, and up to two recent strategy turns. The LLM receives reviewed rule text and IDs. It does not search the PDF or supply citation URLs.

**What does validation guarantee?** An advice response must name sources that were actually in the prompt. The app constructs the links from its catalog. That verifies which rules were cited; it does not prove the recommended move is optimal or that every generated sentence follows from those rules. If the model is unavailable or its references fail validation, the app shows an error. Rules and guides still work.

## The same Pandemic position, two different jobs

| Mode | Player asks | Where the answer comes from |
| --- | --- | --- |
| Ask a rule | “How many cards does the Scientist need for a cure?” | The app returns the reviewed Scientist rule: four City cards of one color at a research station. It links to the role on p. 8 and the cure action on p. 4. No LLM call. |
| Strategy | “I'm the Scientist at a station with four blue cards. Blue is the only uncured disease. Should I treat or cure?” | The coach can use the Scientist, cure and victory rules to recommend discovering the cure now: the fourth cure ends the game immediately. The recommendation is generated; the linked mechanics come from the rulebook. |

Implementation: [index builder](../tabletalk/ingestion/build.py) · [hybrid search](../tabletalk/retrieval/index.py) · [rules handler](../tabletalk/answering/agent.py) · [strategy coach](../tabletalk/strategy/coach.py) · [local model client](../tabletalk/strategy/ollama.py).
