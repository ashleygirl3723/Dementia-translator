# Dementia Translator

A quick communication aid for caregivers, including other caregivers and families.

What it does, in plain terms:
1. **What they said / did** — type a phrase or behaviour and get the likely need behind it, what to try first, what to say, and what to avoid saying.
2. **Simplify what I say** — turn a long instruction into short, one-step lines.
3. **English ↔ Spanish, with audio** — caregiver phrases in Spanish (respectful usted form, with a read-aloud guide AND a tap-to-play audio file), plus what common resident Spanish phrases mean and a spoken reply in Spanish. This is for residents reverting to Spanish as a first language, and for caregivers who do not speak Spanish: you do not have to pronounce it, the phone speaks it for you. A phone-voice button is included as a fallback if an audio file is missing.

What it does not do:
- It does not diagnose, read minds, or replace a nurse or doctor.
- A sudden change, new pain, fever, or distress should be checked with the care team promptly.
- It is a phrasebook and pattern guide, not a full free-text translator. It covers the care phrases that come up most, not every sentence.
- Never enter resident names, photos, or health records. The "my note" box is session-only and is not saved.

## Deploy (no secrets needed)

This app needs no API key.

1. Create a public GitHub repo (the owner creates the repo; the assistant pushes the code).
2. Deploy on share.streamlit.io: pick the repo, branch `main`, main file `app.py`.
3. In the app dashboard, go to Settings → Sharing and set sharing to Public, so other caregivers can open it without signing in.
4. Verify it opens for a stranger, with no sign-in prompt, before calling it live.

Files in the repo: `app.py`, `translator.py` (all patterns and Spanish phrases, no Streamlit import so it can be tested plainly), `requirements.txt`, `README.md`.

Audio note: the local copy also has `audio/` (51 pre-recorded Spanish MP3s, generated with gTTS). Those MP3s are NOT in the GitHub repo, because the GitHub push tool only accepts UTF-8 text files and rejects binary files. The deployed app instead generates the same Spanish voice on demand with gTTS (listed in `requirements.txt`) and caches it for that visit, with the phone-voice button as a fallback. If the live voice is ever blocked on Streamlit Cloud, the `audio/` folder can be uploaded through the GitHub website and the app will use those files first.
