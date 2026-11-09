"""Page links use reviewed metadata, never model-generated URLs."""
import streamlit as st


def source(rule):
    links = [f"[{rule.citation} ↗]({rule.url})"]
    links.extend(f"[p. {page} ↗]({rule.game.pdf}#page={page})" for page in rule.extra_pages)
    st.markdown(" · ".join(links))
