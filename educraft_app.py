import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv, set_key
import streamlit as st

# ── Bootstrap path so generators/ and utils/ are importable ───────────────────
sys.path.insert(0, str(Path(__file__).parent))

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)


def _get_secret(key: str) -> str:
    """Check st.secrets first (Streamlit Cloud), then .env, then empty."""
    try:
        return st.secrets.get(key, "") or os.getenv(key, "")
    except Exception:
        return os.getenv(key, "")

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="EduCraft AI",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Apple Dark Mode CSS ────────────────────────────────────────────────────────
st.html("""
<style>
/* ── Base & Layout ── */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background-color: #000000 !important;
    color: #F5F5F7 !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", Arial, sans-serif !important;
}
section.main > div.block-container {
    background-color: #000000 !important;
    padding-top: 2rem;
    max-width: 860px;
}
[data-testid="stAppViewContainer"] > section.main {
    background-color: #000000 !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: #1C1C1E !important;
    border-right: 1px solid #38383A !important;
}
section[data-testid="stSidebar"] * {
    color: #F5F5F7 !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
    color: #8E8E93 !important;
    font-size: 0.85rem;
}
section[data-testid="stSidebar"] hr {
    border-color: #38383A !important;
}
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] .stCaption {
    color: #636366 !important;
}

/* ── Sidebar inputs ── */
section[data-testid="stSidebar"] input {
    background-color: #2C2C2E !important;
    color: #F5F5F7 !important;
    border: 1px solid #48484A !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] label {
    color: #AEAEB2 !important;
}

/* ── Sidebar button ── */
section[data-testid="stSidebar"] .stButton > button {
    background-color: #2C2C2E !important;
    color: #0A84FF !important;
    border: 1.5px solid #0A84FF !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #0A84FF !important;
    color: #FFFFFF !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background-color: transparent !important;
    border-bottom: 1px solid #38383A !important;
    padding-bottom: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: #1C1C1E !important;
    border-radius: 10px !important;
    padding: 8px 22px !important;
    border: 1px solid #38383A !important;
    color: #AEAEB2 !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}
.stTabs [aria-selected="true"] {
    background-color: #0A84FF !important;
    color: #FFFFFF !important;
    border-color: #0A84FF !important;
    font-weight: 600 !important;
}
[data-testid="stTabContent"] {
    background-color: #000000 !important;
    padding-top: 1rem;
}

/* ── Form card ── */
div[data-testid="stForm"] {
    background-color: #1C1C1E !important;
    border-radius: 16px !important;
    padding: 28px 32px !important;
    border: 1px solid #38383A !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.5) !important;
    margin-bottom: 1.5rem !important;
}

/* ── All labels ── */
label, .stTextInput label, .stTextArea label,
.stSelectbox label, .stSlider label,
div[data-testid="stForm"] label {
    color: #AEAEB2 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.3px !important;
    margin-bottom: 4px !important;
}

/* ── Text inputs & textareas ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #2C2C2E !important;
    color: #F5F5F7 !important;
    border: 1px solid #48484A !important;
    border-radius: 10px !important;
    font-size: 0.95rem !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #636366 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #0A84FF !important;
    box-shadow: 0 0 0 3px rgba(10,132,255,0.2) !important;
    outline: none !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div,
.stSelectbox [data-baseweb="select"] > div {
    background-color: #2C2C2E !important;
    color: #F5F5F7 !important;
    border: 1px solid #48484A !important;
    border-radius: 10px !important;
}
.stSelectbox [data-baseweb="select"] span {
    color: #F5F5F7 !important;
}
[data-baseweb="popover"] ul {
    background-color: #2C2C2E !important;
    border: 1px solid #48484A !important;
    border-radius: 10px !important;
}
[data-baseweb="popover"] li {
    color: #F5F5F7 !important;
}
[data-baseweb="popover"] li:hover {
    background-color: #3A3A3C !important;
}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] [data-testid="stTickBarMin"],
.stSlider [data-baseweb="slider"] [data-testid="stTickBarMax"] {
    color: #636366 !important;
}
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background-color: #0A84FF !important;
    border-color: #0A84FF !important;
}

/* ── Generate (submit) button ── */
div[data-testid="stForm"] .stButton > button,
div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg, #0A84FF 0%, #0071E3 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 13px 24px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    margin-top: 10px !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 2px 12px rgba(10,132,255,0.35) !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stForm"] .stButton > button:hover,
div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
    background: linear-gradient(135deg, #1A94FF 0%, #0077ED 100%) !important;
    box-shadow: 0 4px 20px rgba(10,132,255,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background-color: #1C1C1E !important;
    color: #0A84FF !important;
    border: 1.5px solid #0A84FF !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    width: 100% !important;
    padding: 12px 24px !important;
    font-size: 1rem !important;
    margin-top: 8px !important;
    transition: all 0.15s ease !important;
    letter-spacing: 0.3px !important;
}
.stDownloadButton > button:hover {
    background-color: #0A84FF !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 16px rgba(10,132,255,0.4) !important;
}

/* ── Alerts ── */
.stSuccess {
    background-color: rgba(48,209,88,0.12) !important;
    border: 1px solid rgba(48,209,88,0.3) !important;
    border-left: 4px solid #30D158 !important;
    border-radius: 10px !important;
    color: #30D158 !important;
}
.stSuccess * { color: #30D158 !important; }
.stError {
    background-color: rgba(255,69,58,0.12) !important;
    border: 1px solid rgba(255,69,58,0.3) !important;
    border-left: 4px solid #FF453A !important;
    border-radius: 10px !important;
}
.stError * { color: #FF453A !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: #1C1C1E !important;
    border: 1px solid #38383A !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary {
    color: #F5F5F7 !important;
    font-weight: 600 !important;
}
[data-testid="stExpander"] p,
[data-testid="stExpander"] li {
    color: #AEAEB2 !important;
}

/* ── Dividers ── */
hr { border-color: #38383A !important; }

/* ── Markdown in main area ── */
.stMarkdown h4 { color: #AEAEB2 !important; font-weight: 500 !important; font-size: 0.95rem !important; }
.stMarkdown p  { color: #AEAEB2 !important; }
.stMarkdown strong { color: #F5F5F7 !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #0A84FF !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #1C1C1E; }
::-webkit-scrollbar-thumb { background: #48484A; border-radius: 3px; }

/* ── Mobile ── */
@media (max-width: 640px) {
    div[data-testid="stForm"] { padding: 20px 16px !important; }
}
</style>
""")

# ── Lazy imports (after path setup) ───────────────────────────────────────────
from generators.presentation import generate_presentation
from generators.lesson_plan import generate_lesson_plan
from generators.question_paper import generate_question_paper
import groq as groq_sdk


# ── Session state initialisation ───────────────────────────────────────────────
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = _get_secret("GROQ_API_KEY")
if "unsplash_key" not in st.session_state:
    st.session_state.unsplash_key = _get_secret("UNSPLASH_ACCESS_KEY")

# Generation flags + stored results + error messages
for _k in ("pres_generating", "lp_generating", "qp_generating"):
    if _k not in st.session_state:
        st.session_state[_k] = False
for _k in ("pres_result", "lp_result", "pres_params", "lp_params",
           "pres_error", "lp_error",
           "qp_student_result", "qp_answer_key_result", "qp_params", "qp_error"):
    if _k not in st.session_state:
        st.session_state[_k] = None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## EduCraft AI")
    st.markdown("*Your AI teaching assistant*")
    st.divider()

    groq_key = st.text_input(
        "Groq API Key",
        value=st.session_state.groq_api_key,
        type="password",
        help="Get a free key at console.groq.com — takes 30 seconds",
        placeholder="gsk_...",
        key="api_key_input",
    )
    if st.button("Save Key", use_container_width=True):
        if not groq_key or not groq_key.strip():
            st.error("Please enter a key first.")
        else:
            with st.spinner("Validating key..."):
                try:
                    import groq as _groq_sdk
                    _test = _groq_sdk.Groq(api_key=groq_key.strip())
                    _test.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": "hi"}],
                        max_tokens=1,
                    )
                    set_key(str(ENV_PATH), "GROQ_API_KEY", groq_key)
                    load_dotenv(ENV_PATH, override=True)
                    st.session_state.groq_api_key = groq_key
                    st.success("Key saved and verified!")
                except _groq_sdk.AuthenticationError:
                    st.error("Invalid key — please check and try again.")
                except Exception:
                    # Network issue etc — save anyway
                    set_key(str(ENV_PATH), "GROQ_API_KEY", groq_key)
                    load_dotenv(ENV_PATH, override=True)
                    st.session_state.groq_api_key = groq_key
                    st.success("Key saved! (Could not verify — check connection.)")
    # Keep session_state in sync as user types (without clicking Save)
    st.session_state.groq_api_key = groq_key

    st.divider()

    with st.expander("Upgrade cover photos (optional)"):
        st.caption("AI-generated photos are added automatically. Add an Unsplash key to use real photographs instead.")
        unsplash_key = st.text_input(
            "Unsplash Access Key",
            value=st.session_state.unsplash_key,
            type="password",
            help="Free at unsplash.com/developers",
            placeholder="Your Unsplash access key",
            key="unsplash_key_input",
        )
        if st.button("Save Photo Key", use_container_width=True):
            set_key(str(ENV_PATH), "UNSPLASH_ACCESS_KEY", unsplash_key)
            load_dotenv(ENV_PATH, override=True)
            st.session_state.unsplash_key = unsplash_key
            st.success("Saved!")
        st.session_state.unsplash_key = unsplash_key

    st.divider()
    st.markdown(
        """
**Phase 1 Features**
- Presentation Generator (PPTX)
- Lesson Plan Generator (PDF)

Powered by Groq + Llama 3.3 70B
"""
    )
    st.caption("EduCraft AI — Phase 1")


# ── Helpers ────────────────────────────────────────────────────────────────────
def _validate_key(key: str) -> bool:
    if not key or not key.strip():
        st.error(
            "Please enter your Groq API key in the sidebar.  \n"
            "Get one free at [console.groq.com](https://console.groq.com)."
        )
        return False
    return True


def _validate_fields(**fields) -> bool:
    missing = [label for label, val in fields.items() if not str(val).strip()]
    if missing:
        st.error(f"Please fill in: **{', '.join(missing)}**")
        return False
    return True


import re as _re

_GRADE_KEYWORDS = {
    "grade", "year", "level", "class", "form", "primary", "secondary",
    "elementary", "middle", "high", "junior", "senior", "undergraduate",
    "postgraduate", "graduate", "university", "college", "kindergarten",
    "nursery", "prep", "gcse", "igcse", "a-level", "ib", "bachelor",
    "master", "phd", "diploma",
}

def _looks_like_real_words(text: str, min_letters: int = 2) -> bool:
    """True if text has enough alphabetic content to be a genuine input."""
    letters = _re.sub(r'[^a-zA-Z]', '', text)
    return len(letters) >= min_letters

def _has_vowel(text: str) -> bool:
    """True if text contains at least one vowel — catches pure consonant mashing."""
    return bool(_re.search(r'[aeiouAEIOU]', text))

def _looks_like_grade(text: str) -> bool:
    """True if text looks like a valid grade/level descriptor."""
    t = text.lower().strip()
    if _re.search(r'\d', t):        # Grade 1, Year 10, 8th grade …
        return True
    words = set(_re.split(r'\W+', t))
    return bool(words & _GRADE_KEYWORDS)

def _validate_inputs(topic: str, grade: str, subject: str) -> bool:
    """Validate that topic, grade, and subject are sensible real inputs."""
    topic   = topic.strip()
    grade   = grade.strip()
    subject = subject.strip()

    # ── Topic ──────────────────────────────────────────────────────────────────
    if len(topic) < 3:
        st.error("**Topic** is too short — please be more specific, e.g. *Photosynthesis*.")
        return False
    if not _looks_like_real_words(topic, min_letters=2):
        st.error(
            "**Topic** must contain real words, e.g. *World War II*, *Fractions*, *Climate Change*."
        )
        return False
    # Catch consonant-mashing (e.g. "asdfgh", "qwrtyp"):
    # for each word longer than 3 chars, require vowel ratio >= 20% (incl. y)
    # OR the topic contains a digit (valid for WW2, COVID19, etc.)
    has_digit = bool(_re.search(r'\d', topic))
    if not has_digit:
        for word in _re.split(r'\W+', topic):
            letters = _re.sub(r'[^a-zA-Z]', '', word)
            vowels  = _re.sub(r'[^aeiouAEIOUyY]', '', letters)
            if len(letters) > 3 and (len(vowels) / len(letters)) < 0.20:
                st.error(
                    "**Topic** doesn't look like a real topic — "
                    "please enter something like *Photosynthesis* or *World War II*."
                )
                return False

    # ── Subject ────────────────────────────────────────────────────────────────
    if not _looks_like_real_words(subject, min_letters=2):
        st.error(
            "**Subject** doesn't look valid — please enter a school subject "
            "e.g. *Biology*, *History*, *Mathematics*."
        )
        return False
    if len(subject) > 3 and not _has_vowel(subject):
        st.error(
            "**Subject** doesn't look valid — please enter a school subject "
            "e.g. *Biology*, *History*, *Mathematics*."
        )
        return False

    # ── Grade ──────────────────────────────────────────────────────────────────
    if not _looks_like_grade(grade):
        st.error(
            "**Grade / Level** doesn't look valid — please enter something like "
            "*Grade 8*, *Year 10*, *Undergraduate*, or *GCSE*."
        )
        return False

    return True


def _groq_error_message(e: Exception) -> str:
    if isinstance(e, groq_sdk.AuthenticationError):
        return "Invalid API key. Please check your Groq key in the sidebar."
    elif isinstance(e, groq_sdk.RateLimitError):
        return "Rate limit reached. Wait a moment and try again — Groq's free tier resets quickly."
    elif isinstance(e, json.JSONDecodeError):
        return "The AI returned an unexpected response. Please try again — this is usually a one-time issue."
    else:
        return f"Something went wrong: {type(e).__name__}. Please check your connection and try again."


# ── Main UI ────────────────────────────────────────────────────────────────────
st.html("""
<div style="font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display',Arial,sans-serif;">

  <!-- Hero -->
  <div style="text-align:center; padding: 16px 0 36px 0;">
    <div style="display:inline-block; background:linear-gradient(135deg,#0A84FF,#0071E3);
                border-radius:20px; padding:14px 20px; margin-bottom:18px;
                box-shadow: 0 8px 32px rgba(10,132,255,0.35);">
      <span style="font-size:2rem; line-height:1;">🎓</span>
    </div>
    <h1 style="color:#F5F5F7; font-size:2.6rem; font-weight:700; margin:0 0 10px 0;
               letter-spacing:-0.8px;">EduCraft AI</h1>
    <p style="color:#8E8E93; font-size:1.1rem; margin:0 0 6px 0;">
      Your AI-powered teaching assistant
    </p>
    <p style="color:#636366; font-size:0.92rem; margin:0;">
      Stop spending weekends on lesson prep &mdash; let AI do it in seconds.
    </p>
  </div>

  <!-- Problem statement -->
  <div style="background:#1C1C1E; border:1px solid #38383A; border-radius:16px;
              padding:20px 24px; margin-bottom:20px; text-align:center;">
    <p style="color:#AEAEB2; font-size:0.95rem; margin:0; line-height:1.6;">
      Teachers spend <strong style="color:#FF9F0A;">10&ndash;15 hours every week</strong>
      preparing slides, quizzes, and lesson plans.<br>
      EduCraft AI cuts that to <strong style="color:#30D158;">under 30 seconds</strong>
      &mdash; so you can focus on your students, not your screen.
    </p>
  </div>

  <!-- Feature cards -->
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:28px;">

    <div style="background:#1C1C1E; border:1px solid #38383A; border-radius:14px; padding:20px;">
      <div style="font-size:1.6rem; margin-bottom:10px;">📊</div>
      <div style="color:#F5F5F7; font-weight:600; font-size:1rem; margin-bottom:6px;">
        Presentation Generator
      </div>
      <div style="color:#8E8E93; font-size:0.85rem; line-height:1.5;">
        Enter a topic &rarr; get a polished PowerPoint with cover slide, content slides,
        speaker notes &amp; summary. Ready to present instantly.
      </div>
      <div style="margin-top:12px;">
        <span style="background:rgba(10,132,255,0.15); color:#0A84FF; font-size:0.75rem;
                     font-weight:600; padding:3px 10px; border-radius:20px; border:1px solid rgba(10,132,255,0.3);">
          .pptx download
        </span>
      </div>
    </div>

    <div style="background:#1C1C1E; border:1px solid #38383A; border-radius:14px; padding:20px;">
      <div style="font-size:1.6rem; margin-bottom:10px;">📋</div>
      <div style="color:#F5F5F7; font-weight:600; font-size:1rem; margin-bottom:6px;">
        Lesson Plan Generator
      </div>
      <div style="color:#8E8E93; font-size:0.85rem; line-height:1.5;">
        Built on the 5E Model &amp; Bloom&rsquo;s Taxonomy. Get warm-up, activities,
        differentiation strategies &amp; assessment in one PDF.
      </div>
      <div style="margin-top:12px;">
        <span style="background:rgba(48,209,88,0.12); color:#30D158; font-size:0.75rem;
                     font-weight:600; padding:3px 10px; border-radius:20px; border:1px solid rgba(48,209,88,0.3);">
          .pdf download
        </span>
      </div>
    </div>

  </div>

  <!-- How it works -->
  <div style="background:#1C1C1E; border:1px solid #38383A; border-radius:14px;
              padding:18px 24px; margin-bottom:28px;">
    <div style="color:#AEAEB2; font-size:0.78rem; font-weight:600; letter-spacing:1px;
                text-transform:uppercase; margin-bottom:14px;">How it works</div>
    <div style="display:flex; gap:0; align-items:flex-start;">

      <div style="flex:1; text-align:center; padding:0 8px;">
        <div style="background:#0A84FF; color:#fff; font-weight:700; font-size:0.85rem;
                    width:28px; height:28px; border-radius:50%; display:inline-flex;
                    align-items:center; justify-content:center; margin-bottom:8px;">1</div>
        <div style="color:#F5F5F7; font-size:0.85rem; font-weight:500;">Fill the form</div>
        <div style="color:#636366; font-size:0.78rem; margin-top:3px;">Topic, grade, subject</div>
      </div>

      <div style="color:#38383A; font-size:1.2rem; padding-top:6px;">&rsaquo;</div>

      <div style="flex:1; text-align:center; padding:0 8px;">
        <div style="background:#0A84FF; color:#fff; font-weight:700; font-size:0.85rem;
                    width:28px; height:28px; border-radius:50%; display:inline-flex;
                    align-items:center; justify-content:center; margin-bottom:8px;">2</div>
        <div style="color:#F5F5F7; font-size:0.85rem; font-weight:500;">Click Generate</div>
        <div style="color:#636366; font-size:0.78rem; margin-top:3px;">AI works in ~15 sec</div>
      </div>

      <div style="color:#38383A; font-size:1.2rem; padding-top:6px;">&rsaquo;</div>

      <div style="flex:1; text-align:center; padding:0 8px;">
        <div style="background:#30D158; color:#fff; font-weight:700; font-size:0.85rem;
                    width:28px; height:28px; border-radius:50%; display:inline-flex;
                    align-items:center; justify-content:center; margin-bottom:8px;">3</div>
        <div style="color:#F5F5F7; font-size:0.85rem; font-weight:500;">Download &amp; use</div>
        <div style="color:#636366; font-size:0.78rem; margin-top:3px;">PPTX or PDF, ready to go</div>
      </div>

    </div>
  </div>

  <!-- Divider before tabs -->
  <div style="color:#AEAEB2; font-size:0.78rem; font-weight:600; letter-spacing:1px;
              text-transform:uppercase; margin-bottom:12px;">Choose a tool below</div>

</div>
""")

tab1, tab2, tab3 = st.tabs(["Presentation Generator", "Lesson Plan Generator", "Question Paper Generator"])


# ── Tab 1: Presentation Generator ─────────────────────────────────────────────
with tab1:
    st.markdown("#### Create a classroom presentation ready to download as PowerPoint")

    _pres_busy = st.session_state.pres_generating
    with st.form("presentation_form"):
        topic = st.text_input("Topic *", placeholder="e.g. Photosynthesis, World War II, Fractions")

        col1, col2 = st.columns(2)
        with col1:
            grade = st.text_input("Grade / Level *", placeholder="e.g. Grade 8, Undergraduate")
        with col2:
            subject = st.text_input("Subject *", placeholder="e.g. Biology, History, Math")

        col3, col4 = st.columns(2)
        with col3:
            num_slides = st.slider("Number of Slides", min_value=5, max_value=20, value=10)
        with col4:
            tone = st.selectbox("Tone", ["Formal", "Fun", "Simple"])

        board = st.selectbox("Board / Curriculum", ["CBSE", "ICSE", "State Board", "IB", "Other"])

        pres_submitted = st.form_submit_button(
            "Generating presentation..." if _pres_busy else "Generate Presentation",
            type="primary",
            use_container_width=True,
            disabled=_pres_busy,
        )

    # Phase 1: user clicked submit — save params, disable button, rerun
    if pres_submitted:
        if not _validate_key(groq_key):
            st.stop()
        if not _validate_fields(Topic=topic, **{"Grade/Level": grade}, Subject=subject):
            st.stop()
        if not _validate_inputs(topic, grade, subject):
            st.stop()
        st.session_state.pres_params = dict(
            topic=topic, grade=grade, subject=subject,
            num_slides=num_slides, tone=tone, board=board,
        )
        st.session_state.pres_generating = True
        st.session_state.pres_result = None
        st.session_state.pres_error = None
        st.rerun()

    # Phase 2: button is disabled — do the actual generation
    if st.session_state.pres_generating:
        p = st.session_state.pres_params
        _status = st.empty()
        def _pres_retry(attempt, wait):
            _status.warning(
                f"⏳ Groq rate limit hit — auto-retrying in {wait} seconds "
                f"(attempt {attempt} of 3)..."
            )
        try:
            _status.info("🎨 Crafting your presentation...")
            pptx_bytes = generate_presentation(
                topic=p["topic"], grade=p["grade"], subject=p["subject"],
                num_slides=p["num_slides"], tone=p["tone"], board=p.get("board", "CBSE"),
                api_key=groq_key,
                unsplash_key=st.session_state.unsplash_key,
                on_retry=_pres_retry,
            )
            st.session_state.pres_result = pptx_bytes
            st.session_state.pres_error = None
        except Exception as e:
            st.session_state.pres_error = _groq_error_message(e)
        finally:
            st.session_state.pres_generating = False
            _status.empty()
        st.rerun()

    # Show any stored error (persists across rerun)
    if st.session_state.pres_error:
        st.error(st.session_state.pres_error)

    # Phase 3: show result
    if st.session_state.pres_result:
        p = st.session_state.pres_params
        st.success("Your presentation is ready!")
        with st.expander("What was generated", expanded=True):
            st.markdown(
                f"**{p['num_slides']} slides** on *{p['topic']}* for **{p['grade']}** — "
                f"{p['subject']} | {p.get('board','CBSE')} | Tone: {p['tone']}"
            )
            st.markdown("Download the file below and open it in PowerPoint or Google Slides.")
        filename = f"{p['topic'].replace(' ', '_')}_presentation.pptx"
        st.download_button(
            label="Download PowerPoint (.pptx)",
            data=st.session_state.pres_result,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )
        if st.button("🔄 Regenerate (same settings)", use_container_width=True, key="pres_regen"):
            st.session_state.pres_generating = True
            st.session_state.pres_result = None
            st.session_state.pres_error = None
            st.rerun()


# ── Tab 2: Lesson Plan Generator ──────────────────────────────────────────────
with tab2:
    st.markdown("#### Create a full lesson plan based on the 5E Model and Bloom's Taxonomy")

    _lp_busy = st.session_state.lp_generating
    with st.form("lesson_plan_form"):
        col1, col2 = st.columns(2)
        with col1:
            lp_subject = st.text_input("Subject *", placeholder="e.g. Mathematics")
        with col2:
            lp_topic = st.text_input("Topic *", placeholder="e.g. Quadratic Equations")

        col3, col4 = st.columns(2)
        with col3:
            lp_grade = st.text_input("Grade / Level *", placeholder="e.g. Grade 10")
        with col4:
            lp_duration = st.selectbox(
                "Duration",
                [30, 45, 60, 90],
                index=1,
                format_func=lambda x: f"{x} minutes",
            )

        lp_objectives = st.text_area(
            "Learning Objectives (optional)",
            placeholder=(
                "e.g. Students will be able to solve quadratic equations using factoring\n"
                "Leave blank and AI will design objectives for you."
            ),
            height=90,
        )

        lp_resources = st.selectbox(
            "Available Resources",
            [
                "Whiteboard only",
                "Whiteboard + Projector",
                "Full tech (projector, computers, internet)",
                "None",
            ],
        )

        lp_board = st.selectbox("Board / Curriculum", ["CBSE", "ICSE", "State Board", "IB", "Other"], key="lp_board")

        lp_submitted = st.form_submit_button(
            "Generating lesson plan..." if _lp_busy else "Generate Lesson Plan",
            type="primary",
            use_container_width=True,
            disabled=_lp_busy,
        )

    # Phase 1: save params, disable button, rerun
    if lp_submitted:
        if not _validate_key(groq_key):
            st.stop()
        if not _validate_fields(Subject=lp_subject, Topic=lp_topic, **{"Grade/Level": lp_grade}):
            st.stop()
        if not _validate_inputs(lp_topic, lp_grade, lp_subject):
            st.stop()
        st.session_state.lp_params = dict(
            subject=lp_subject, topic=lp_topic, grade=lp_grade,
            duration=lp_duration, objectives=lp_objectives, resources=lp_resources,
            board=lp_board,
        )
        st.session_state.lp_generating = True
        st.session_state.lp_result = None
        st.session_state.lp_error = None
        st.rerun()

    # Phase 2: button is disabled — do the generation
    if st.session_state.lp_generating:
        p = st.session_state.lp_params
        _lp_status = st.empty()
        def _lp_retry(attempt, wait):
            _lp_status.warning(
                f"⏳ Groq rate limit hit — auto-retrying in {wait} seconds "
                f"(attempt {attempt} of 3)..."
            )
        try:
            _lp_status.info("📋 Crafting your lesson plan...")
            pdf_bytes = generate_lesson_plan(
                subject=p["subject"], topic=p["topic"], grade=p["grade"],
                duration=p["duration"], objectives=p["objectives"],
                resources=p["resources"], board=p.get("board", "CBSE"),
                api_key=groq_key,
                on_retry=_lp_retry,
            )
            st.session_state.lp_result = pdf_bytes
            st.session_state.lp_error = None
        except Exception as e:
            st.session_state.lp_error = _groq_error_message(e)
        finally:
            st.session_state.lp_generating = False
            _lp_status.empty()
        st.rerun()

    # Show any stored error (persists across rerun)
    if st.session_state.lp_error:
        st.error(st.session_state.lp_error)

    # Phase 3: show result
    if st.session_state.lp_result:
        p = st.session_state.lp_params
        st.success("Your lesson plan is ready!")
        with st.expander("What was generated", expanded=True):
            st.markdown(
                f"**{p['duration']}-minute lesson** on *{p['topic']}* for **{p['grade']}** — {p['subject']}"
            )
            st.markdown(
                "Includes 5E sections (Engage → Explore → Explain → Elaborate → Evaluate), "
                "differentiation strategies, and optional homework."
            )
        filename = f"{p['topic'].replace(' ', '_')}_lesson_plan.pdf"
        st.download_button(
            label="Download Lesson Plan (PDF)",
            data=st.session_state.lp_result,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )
        if st.button("🔄 Regenerate (same settings)", use_container_width=True, key="lp_regen"):
            st.session_state.lp_generating = True
            st.session_state.lp_result = None
            st.session_state.lp_error = None
            st.rerun()


# ── Tab 3: Question Paper Generator ───────────────────────────────────────────
with tab3:
    st.markdown("#### Create a CBSE-style question paper with student version + answer key")

    _qp_busy = st.session_state.qp_generating
    with st.form("question_paper_form"):
        col1, col2 = st.columns(2)
        with col1:
            qp_subject = st.text_input("Subject *", placeholder="e.g. Science, Mathematics")
        with col2:
            qp_topic = st.text_input("Topic *", placeholder="e.g. Chemical Reactions, Fractions")

        col3, col4 = st.columns(2)
        with col3:
            qp_grade = st.text_input("Grade / Level *", placeholder="e.g. Class 10, Grade 8")
        with col4:
            qp_board = st.selectbox("Board", ["CBSE", "ICSE", "State Board", "IB", "Other"], key="qp_board_sel")

        col5, col6 = st.columns(2)
        with col5:
            qp_total_marks = st.selectbox("Total Marks", [10, 20, 40, 50, 80, 100], index=2)
        with col6:
            qp_difficulty = st.selectbox("Difficulty", ["Easy", "Balanced", "Hard"], index=1)

        st.markdown("**Section Breakdown**")
        col7, col8, col9 = st.columns(3)
        with col7:
            qp_mcq_count  = st.number_input("MCQs (1 mark each)", min_value=0, max_value=30, value=10, step=1)
        with col8:
            qp_short_count = st.number_input("Short Ans (marks each)", min_value=0, max_value=15, value=5, step=1)
            qp_short_marks = st.number_input("Marks per short answer", min_value=1, max_value=5, value=2, step=1)
        with col9:
            qp_long_count  = st.number_input("Long Ans (marks each)", min_value=0, max_value=10, value=2, step=1)
            qp_long_marks  = st.number_input("Marks per long answer", min_value=3, max_value=10, value=5, step=1)

        qp_submitted = st.form_submit_button(
            "Generating question paper..." if _qp_busy else "Generate Question Paper",
            type="primary",
            use_container_width=True,
            disabled=_qp_busy,
        )

    # Validate total marks match
    if qp_submitted:
        computed = qp_mcq_count * 1 + qp_short_count * qp_short_marks + qp_long_count * qp_long_marks
        if not _validate_key(groq_key):
            st.stop()
        if not _validate_fields(Subject=qp_subject, Topic=qp_topic, **{"Grade/Level": qp_grade}):
            st.stop()
        if not _validate_inputs(qp_topic, qp_grade, qp_subject):
            st.stop()
        if computed != qp_total_marks:
            st.warning(
                f"⚠️ Section breakdown adds up to **{computed} marks**, "
                f"but Total Marks is set to **{qp_total_marks}**. "
                f"Adjust the counts or total marks so they match."
            )
            st.stop()
        st.session_state.qp_params = dict(
            subject=qp_subject, topic=qp_topic, grade=qp_grade, board=qp_board,
            total_marks=qp_total_marks, difficulty=qp_difficulty,
            mcq_count=int(qp_mcq_count), short_count=int(qp_short_count),
            long_count=int(qp_long_count), mcq_marks=1,
            short_marks=int(qp_short_marks), long_marks=int(qp_long_marks),
        )
        st.session_state.qp_generating = True
        st.session_state.qp_student_result = None
        st.session_state.qp_answer_key_result = None
        st.session_state.qp_error = None
        st.rerun()

    # Phase 2: generate
    if st.session_state.qp_generating:
        p = st.session_state.qp_params
        _qp_status = st.empty()
        def _qp_retry(attempt, wait):
            _qp_status.warning(
                f"⏳ Groq rate limit hit — auto-retrying in {wait} seconds "
                f"(attempt {attempt} of 3)..."
            )
        try:
            _qp_status.info("📝 Generating your question paper and answer key...")
            student_pdf, answer_key_pdf = generate_question_paper(
                subject=p["subject"], topic=p["topic"], grade=p["grade"],
                board=p["board"], total_marks=p["total_marks"],
                mcq_count=p["mcq_count"], short_count=p["short_count"],
                long_count=p["long_count"], mcq_marks=p["mcq_marks"],
                short_marks=p["short_marks"], long_marks=p["long_marks"],
                difficulty=p["difficulty"], api_key=groq_key,
                on_retry=_qp_retry,
            )
            st.session_state.qp_student_result = student_pdf
            st.session_state.qp_answer_key_result = answer_key_pdf
            st.session_state.qp_error = None
        except Exception as e:
            st.session_state.qp_error = _groq_error_message(e)
        finally:
            st.session_state.qp_generating = False
            _qp_status.empty()
        st.rerun()

    if st.session_state.qp_error:
        st.error(st.session_state.qp_error)

    # Phase 3: show results
    if st.session_state.qp_student_result:
        p = st.session_state.qp_params
        st.success("Your question paper is ready!")
        with st.expander("What was generated", expanded=True):
            st.markdown(
                f"**{p['total_marks']}-mark paper** on *{p['topic']}* for **{p['grade']}** — "
                f"{p['subject']} | {p['board']} | Difficulty: {p['difficulty']}"
            )
            st.markdown(
                f"Sections: {p['mcq_count']} MCQs · {p['short_count']} Short ({p['short_marks']}m) · "
                f"{p['long_count']} Long ({p['long_marks']}m)"
            )
        safe_topic = p['topic'].replace(' ', '_')
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                label="Download Student Paper (PDF)",
                data=st.session_state.qp_student_result,
                file_name=f"{safe_topic}_question_paper.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with col_b:
            st.download_button(
                label="Download Answer Key (PDF)",
                data=st.session_state.qp_answer_key_result,
                file_name=f"{safe_topic}_answer_key.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        if st.button("🔄 Regenerate (same settings)", use_container_width=True, key="qp_regen"):
            st.session_state.qp_generating = True
            st.session_state.qp_student_result = None
            st.session_state.qp_answer_key_result = None
            st.session_state.qp_error = None
            st.rerun()
