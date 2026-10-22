from __future__ import annotations
import streamlit as st

NAV_ITEMS = ["Home", "Play", "Explore", "Learn", "Feedback", "Admin"]


def render_primary_navigation() -> str:
    selected = st.radio(
        "Primary navigation",
        NAV_ITEMS,
        key="main_view",
        horizontal=True,
        label_visibility="collapsed",
    )
    st.caption("▶ Play · 🌍 Explore · 📚 Learn")
    return selected
