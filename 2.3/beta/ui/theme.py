from __future__ import annotations
import streamlit as st


def inject_theme() -> None:
    st.markdown("""
    <style>
      .block-container {padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1180px;}
      .pf-hero {padding: 1.2rem 1.35rem; border: 1px solid rgba(128,128,128,.22); border-radius: 18px; margin-bottom: 1rem; background: rgba(128,128,128,.035);}
      .pf-hero h1 {margin: 0; font-size: 2.05rem; letter-spacing: -.03em;}
      .pf-tagline {margin-top: .25rem; opacity: .72; font-size: 1rem;}
      .pf-kicker {font-size: .78rem; text-transform: uppercase; letter-spacing: .09em; opacity: .62; margin-bottom: .25rem;}
      .pf-card {border: 1px solid rgba(128,128,128,.22); border-radius: 16px; padding: 1rem 1.1rem; margin: .45rem 0 .85rem 0; background: rgba(128,128,128,.025);}
      .pf-card h3 {margin-top: 0; margin-bottom: .35rem;}
      .pf-phrase {font-size: 2rem; font-weight: 700; letter-spacing: .025em; text-align: center; margin: .35rem 0 .6rem;}
      .pf-muted {opacity: .68;}
      .pf-pill {display:inline-block; padding:.2rem .55rem; border-radius:999px; border:1px solid rgba(128,128,128,.24); margin:.12rem .18rem .12rem 0; font-size:.82rem;}
      .pf-success {border:1px solid rgba(25,135,84,.35); border-radius:16px; padding:1rem 1.1rem; background:rgba(25,135,84,.07); text-align:center;}
      .pf-success-word {font-size:1.8rem; font-weight:700; margin:.25rem 0;}
      .pf-section-title {margin-top:1rem; margin-bottom:.35rem;}
      div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.18); border-radius: 14px; padding: .65rem .8rem;}
      div.stButton > button {border-radius: 12px;}
      div[data-testid="stTextInput"] input, textarea {border-radius: 12px !important;}
      @media (max-width: 640px) {
        .block-container {padding-left: .8rem; padding-right: .8rem;}
        .pf-hero h1 {font-size: 1.65rem;}
        .pf-phrase {font-size:1.55rem;}
      }
    </style>
    """, unsafe_allow_html=True)
