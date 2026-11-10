from base64 import b64encode
from pathlib import Path
import streamlit as st

from tabletalk.answering.agent import answer, ruling
from tabletalk.catalog import GAMES
from tabletalk.retrieval.index import RuleIndex
from tabletalk.ui.sources import source
from tabletalk.ui.strategy import strategy_chat

ASSETS = Path(__file__).parent / "assets"


@st.cache_resource
def load_rule_index(game_id: str, index_revision: int) -> RuleIndex:
    """Share the encoder and ranking data across retriever invocations for this edition."""
    return RuleIndex(game_id)


def go(game=None):
    if game:
        st.query_params["game"] = game
    else:
        st.query_params.clear()
    st.rerun()


def game_shelf():
    st.html('<div class="eyebrow">THE COLLECTION</div>')
    st.title("Your game shelf")
    st.write("Pick a game to learn the setup or settle a rule at the table.")
    # A real Streamlit button keeps the entire illustrated tile keyboard-accessible.
    for game in GAMES.values():
        if st.button(f"{game.name}  ·  Base game", key=f"pick_{game.id}", width="stretch",
                     help=f"Open the {game.name} rulebook"):
            go(game.id)
        st.caption(f"{game.players} players  ·  {game.edition}")


def guide(index, ids, step):
    rule = index.by_id[ids[step]]
    st.caption(f"STEP {step + 1} OF {len(ids)}")
    st.subheader(rule.title)
    st.write(rule.answer)
    source(rule)
    if step == 0 or (index.game.id == "catan" and rule.id in {"pieces", "starting-hand"}):
        st.markdown(index.game.diagram_link)


def chat(index):
    history = st.session_state.setdefault(f"{index.game.id}:history", [])
    quick = None
    if not history:
        st.write("What would you like to check?")
        for example in index.game.examples:
            if st.button(example, key=f"{index.game.id}:example:{example}"):
                quick = example

    query = st.chat_input(f"Ask about {index.game.name}…", key=f"{index.game.id}:rule-input", max_chars=500)
    if query or quick:
        question = query or quick
        previous = index.by_id.get(history[-1][1].rule_id) if history else None
        history.append((question, answer(index, question, previous)))
        st.rerun()

    for pos, (question, reply) in enumerate(history):
        with st.chat_message("user", avatar=":material/person:"):
            st.text(question)
        with st.chat_message("assistant", avatar=":material/menu_book:"):
            st.write(reply.text)
            if reply.rule_id:
                source(index.by_id[reply.rule_id])
            if guide_sources := getattr(reply, "guide_sources", ()):
                st.markdown(index.game.diagram_link)
                with st.expander("Setup rules and sources"):
                    for key in guide_sources:
                        source(index.by_id[key])
            if pos == len(history) - 1:
                for key in reply.suggestions:
                    rule = index.by_id[key]
                    label = "Beginner map: starting resources and first turn" if index.game.id == "catan" and key == "starting-hand" else rule.title
                    if st.button(label, key=f"topic-{pos}-{key}"):
                        history.append((rule.title, ruling(rule)))
                        st.rerun()
    if history and st.button("New conversation", type="tertiary"):
        history.clear()
        st.rerun()


def game_room(game):
    if st.button("←  Game shelf", type="tertiary"):
        go()
    st.html(f'<div class="eyebrow">BASE GAME &nbsp; / &nbsp; {game.edition.upper()}</div>')
    st.title(game.name)
    mode = st.segmented_control("Choose a mode", ("Ask a rule", "Strategy", "Set us up", "Quick refresher"),
                                default=("Strategy" if st.query_params.get("view") == "strategy" else "Ask a rule"),
                                label_visibility="collapsed",
                                key="mode")
    index = load_rule_index(game.id, (game.directory / "index.npz").stat().st_mtime_ns)
    if mode == "Strategy":
        strategy_chat(index)
    elif mode == "Set us up":
        step_key = f"{game.id}:step"
        steps = (*game.setup, "turn")
        step = st.session_state.setdefault(step_key, 0)
        with st.container(border=True):
            guide(index, steps, step)
        left, right = st.columns(2)
        if left.button("Previous", disabled=step == 0, width="stretch"):
            st.session_state[step_key] -= 1
            st.rerun()
        label = "Next step" if step < len(steps) - 1 else "Start again"
        if right.button(label, type="primary", width="stretch"):
            st.session_state[step_key] = (step + 1) % len(steps)
            st.rerun()
    elif mode == "Quick refresher":
        for key in game.refresher:
            with st.container(border=True):
                rule = index.by_id[key]
                st.subheader(rule.title)
                st.write(rule.answer)
                source(rule)
    else:
        chat(index)


def show():
    st.set_page_config(page_title="Tabletalk · Board game rules", page_icon="🎲", layout="centered")
    style = (ASSETS / "style.html").read_text()
    for key, asset in (("catan", "island.svg"), ("pandemic", "routes.svg")):
        art = b64encode((ASSETS / asset).read_bytes()).decode("ascii")
        style = style.replace(f"var(--{key}-art)", f'url("data:image/svg+xml;base64,{art}")')
    st.html(style)
    st.html('<div class="brand"><span>⬡</span> TABLETALK</div>')
    if game := GAMES.get(st.query_params.get("game")):
        game_room(game)
    else:
        game_shelf()
