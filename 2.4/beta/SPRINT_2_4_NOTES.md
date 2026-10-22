# Phrase Forge Sprint 2.4 — Responsive Web Edition

Based on the user's tested Sprint 2.3.1a upload.

## Changes
- Responsive layout and mobile-first CSS adjustments in `living_prototype.py`, while preserving the existing desktop visual identity.
- Touch-friendly buttons and form inputs, mobile-friendly typography and source-word cards.
- Added editorial dictionary acceptance for ABRIDGE, with grammatical role and definition, in the Phrase Forge Lexicon; word-frequency no longer blocks this specific established word.
- Added regression tests for ABRIDGE and responsive styling.

## Run
```
python -m pip install -r requirements.txt
streamlit run living_prototype.py
```

For AI features, configure `OPENAI_API_KEY` in your environment.

## Test on a phone on the same Wi-Fi network
On the Mac, run:
```
streamlit run living_prototype.py --server.address 0.0.0.0 --server.port 8501
```
Find the Mac's LAN IP address in System Settings > Network and visit `http://MAC_LAN_IP:8501` from Safari/Chrome on your phone. Allow incoming connections through your Mac firewall if prompted. Do not expose this local development server directly to the public internet.

## Scope / limitations
- The original Streamlit UI is now styled for mobile but has not been visually verified on a physical iPhone/Android device; please test before public deployment.
- AI Word Cards and AI-generated collections remain as in 2.3.1a.
- The dictionary change is an editorial ABRIDGE correction, **not** a general AI-backed dictionary authority or automated verification workflow. Other uncommon legitimate words may still be rejected by the current lexicon profile. That broader hybrid validator is a follow-up task.
- Collections are still session-based, not persistently saved.
