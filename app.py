import hashlib
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from translator import (
    CATEGORIES,
    PATTERNS,
    RESIDENT_SPANISH,
    SPANISH_CATEGORIES,
    SPANISH_PHRASES,
    search_patterns,
    search_resident_spanish,
    search_spanish,
    simplify,
)

st.set_page_config(page_title="Dementia Translator", page_icon="💬", layout="centered")

AUDIO_DIR = Path(__file__).parent / "audio"


def play_spanish_audio(path, text):
    """Play Spanish audio, in order: pre-recorded file, live gTTS, phone voice.

    Pre-recorded files ship only in the local copy. The deployed repo is
    code-only, because the GitHub push tool rejects binary files, so on
    Streamlit Cloud the app generates the same Spanish voice on demand
    with gTTS and caches it for that visit. If that is blocked, the
    phone-voice button below is the last fallback.
    """
    if path.exists():
        st.audio(path.read_bytes(), format="audio/mp3")
    else:
        cache_key = "gtts_" + hashlib.md5(text.encode("utf-8")).hexdigest()
        if cache_key not in st.session_state:
            try:
                import io

                from gtts import gTTS

                buf = io.BytesIO()
                gTTS(text=text, lang="es").write_to_fp(buf)
                st.session_state[cache_key] = buf.getvalue()
            except Exception:
                st.session_state[cache_key] = None
        if st.session_state.get(cache_key):
            st.audio(st.session_state[cache_key], format="audio/mp3")
    uid = hashlib.md5(text.encode("utf-8")).hexdigest()[:10]
    html_code = f"""
    <button onclick="speak_{uid}()" style="font-size:18px;padding:10px 16px;border-radius:12px;border:1px solid #ccc;background:#ffffff;cursor:pointer;">🔊 Play with phone voice</button>
    <script>
    function speak_{uid}() {{
      if (!('speechSynthesis' in window)) {{ alert('This device does not support spoken audio.'); return; }}
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance({json.dumps(text)});
      u.lang = 'es-MX';
      u.rate = 0.8;
      var voices = window.speechSynthesis.getVoices();
      var v = voices.find(function(v) {{ return v.lang && v.lang.toLowerCase().startsWith('es'); }});
      if (v) {{ u.voice = v; }}
      window.speechSynthesis.speak(u);
    }}
    </script>
    """
    components.html(html_code, height=60)

st.title("💬 Dementia Translator")
st.write(
    "A quick aid for caregivers. It helps you guess the need behind what "
    "someone says or does, simplify what you need to say, and use simple "
    "Spanish when someone is reverting to their first language."
)
st.info(
    "Communication aid only. It does not diagnose and it does not read minds. "
    "A sudden change, new pain, fever, or distress should be checked with the "
    "care team promptly. Never enter resident names, photos, or health records here."
)

tab1, tab2, tab3 = st.tabs([
    "What they said / did",
    "Simplify what I say",
    "English ↔ Spanish",
])

# ------------------------------------------------------------ Tab 1: patterns
with tab1:
    st.header("What they said or did")
    st.write("Type a word or phrase, or pick a category. The result is a best guess, not a certainty. Check the basics first.")
    q = st.text_input("Search, for example: go home, pacing, refusing", key="pattern_q")
    cat = st.selectbox("Category", ["All"] + CATEGORIES, key="pattern_cat")
    results = search_patterns(q, cat)
    if not results:
        st.write("No match yet. Try a shorter word, like home, pain, or night.")
    for p in results:
        with st.expander(f"{p['says']}  —  {p['category']}", expanded=False):
            if p.get("red_flag"):
                st.warning("Sudden change? Tell the nurse promptly.")
            st.subheader("It often means")
            for line in p["likely_means"]:
                st.write(f"• {line}")
            st.subheader("Try first")
            for line in p["try"]:
                st.write(f"• {line}")
            st.subheader("Say this")
            for line in p["say"]:
                st.write(f"• “{line}”")
            st.subheader("Avoid saying")
            for line in p["avoid"]:
                st.write(f"• “{line}”")

# ------------------------------------------------------------ Tab 2: simplify
with tab2:
    st.header("Simplify what I say")
    st.write("Paste a long instruction. You will get it back as short, one-step lines. Say one step, wait, then say the next.")
    text = st.text_area(
        "What you need to say",
        value="It's time for your shower and then we need to get dressed and take your medicine",
        height=90,
    )
    if st.button("Simplify it"):
        steps = simplify(text)
        if not steps:
            st.write("Type something first.")
        else:
            for i, step in enumerate(steps, 1):
                st.write(f"**Step {i}:** {step}")
            st.write("Tips: use a calm voice, get at eye level, offer a choice of two, and give time to answer.")
    st.subheader("Examples that work better")
    st.write("• Instead of: “We need to shower, dress, eat, and go out” — try: “Let's take a shower.” Then stop.")
    st.write("• Instead of: “Don't you remember?” — try: “Lunch is at noon.”")
    st.write("• Instead of arguing a fact — try validating the feeling, then redirecting to a calm activity.")

# ------------------------------------------------------------ Tab 3: Spanish
with tab3:
    st.header("English ↔ Spanish care phrases")
    st.write(
        "Dementia often brings back a first language first. Short, familiar "
        "phrases in Spanish can calm and connect, even if you only know a few. "
        "Spanish below uses the respectful usted form, the safer default for an older adult."
    )
    st.success(
        "You do not have to pronounce it yourself. Tap the audio player and the phone "
        "speaks the Spanish for you. Turn the volume up, hold the phone near the resident, "
        "play it once, watch their face, and play it again if needed."
    )
    st.subheader("I need to say something in Spanish")
    sq = st.text_input("Search in English or Spanish, for example: bathroom, pain, safe", key="spanish_q")
    scat = st.selectbox("Category", ["All"] + SPANISH_CATEGORIES, key="spanish_cat")
    sresults = search_spanish(sq, scat)
    if not sresults:
        st.write("No match yet. Try a shorter word, like water, pain, or sleep.")
    for p in sresults:
        st.write(f"**{p['en']}**")
        st.write(f"🇪🇸 {p['es']}")
        st.write(f"Say it like: {p['say']}")
        orig_idx = SPANISH_PHRASES.index(p)
        play_spanish_audio(AUDIO_DIR / f"caregiver_{orig_idx:02d}.mp3", p["es"])
        st.divider()

    st.subheader("They said something in Spanish — what does it mean?")
    rq = st.text_input("Search in Spanish or English, for example: casa, miedo, hambre", key="resident_q")
    rresults = search_resident_spanish(rq)
    for p in rresults:
        with st.expander(f"{p['es']}  —  {p['en']}", expanded=False):
            st.write(f"**Means:** {p['en']}")
            st.write(f"**You can reply:** {p['reply_es']}")
            st.write(f"That means: {p['reply_en']}")
            orig_idx = RESIDENT_SPANISH.index(p)
            play_spanish_audio(AUDIO_DIR / f"resident_reply_{orig_idx:02d}.mp3", p["reply_es"])

    st.subheader("Your own pattern (this visit only)")
    st.write(
        "This notebook is only for this open page. Nothing is saved for other "
        "people, and nothing should include a name or photo. Use it for a pattern "
        "you notice, like a word this person uses for the bathroom."
    )
    if "my_patterns" not in st.session_state:
        st.session_state.my_patterns = []
    new_pattern = st.text_input("My note, for example: When she says 'vamos', she usually wants to walk", key="my_pattern")
    if st.button("Add my note"):
        if new_pattern.strip():
            st.session_state.my_patterns.append(new_pattern.strip())
    for note in st.session_state.my_patterns:
        st.write(f"• {note}")

st.divider()
st.caption(
    f"V1: {len(PATTERNS)} dementia patterns, {len(SPANISH_PHRASES)} caregiver Spanish phrases with audio, "
    f"and {len(RESIDENT_SPANISH)} resident Spanish phrases with spoken replies. No API key needed, nothing is saved. "
    "If the phone-voice button ever sounds English, the pre-recorded audio above it is the one to use."
)
