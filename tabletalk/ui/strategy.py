"""Streamlit view for the strategy conversation; rules chat keeps its own history."""
import streamlit as st

from tabletalk.ui.sources import source
from tabletalk.strategy.coach import advise
from tabletalk.strategy.ollama import CoachError

def strategy_chat(index):
    st.subheader("Strategy coach")
    st.caption("Describe your position and the moves you’re weighing. The coach suggests a play; the linked rules explain the mechanics.")
    history = st.session_state.setdefault(f"{index.game.id}:strategy-history", [])
    question = None
    if not history:
        for example in index.game.decisions:
            if st.button(example):
                question = example
    for previous, tip in history:
        with st.chat_message("user", avatar=":material/person:"):
            st.text(previous)
        with st.chat_message("assistant", avatar=":material/lightbulb:"):
            if tip.kind == "advice":
                st.markdown("**Suggested play**")
            if tip.kind == "guide":
                st.markdown(tip.move)
                st.markdown(index.game.diagram_link)
            else:
                st.text(tip.move)
            if tip.reason:
                st.text(tip.reason)
            if tip.tradeoff:
                st.markdown("**Tradeoff**")
                st.text(tip.tradeoff)
            if tip.sources:
                with st.expander("Setup rules and sources" if tip.kind == "guide" else "Rules behind this advice"):
                    for key in tip.sources:
                        rule = index.by_id[key]
                        source(rule)
                        st.write(rule.answer)
    prompt = st.chat_input("Describe a move or ask for a strategy…", key=f"{index.game.id}:strategy-input", max_chars=1000)
    question = prompt or question
    if question:
        try:
            with st.spinner("Considering your position…"):
                tip = advise(index, question, history)
        except CoachError as exc:
            st.error(str(exc))
        else:
            history.append((question, tip))
            st.rerun()
    if history and st.button("New strategy conversation", type="tertiary"):
        history.clear()
        st.rerun()
