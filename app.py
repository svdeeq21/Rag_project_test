import streamlit as st
import json
import os
import base64
import hashlib
import tempfile
import time
import re
import uuid

# ════════════════════════════════════════════════════════
# ── BRANDING — edit these lines ──────────────────────────
BRAND_NAME   = "Sadiq Shehu"           # ← your name or company
BRAND_LOGO   = "sh1.png"                    # ← path to logo file e.g. "logo.png", or leave ""
APP_SUBTITLE = "Document Intelligence"
# ════════════════════════════════════════════════════════

# ── Pipeline defaults (hidden from end-users) ────────────
DEFAULT_MAX_CHARS   = 3000
DEFAULT_NEW_AFTER   = 2400
DEFAULT_COMBINE     = 500
DEFAULT_TOP_K       = 3
DEFAULT_PERSIST_DIR = "chroma_db"
DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_LLM_MODEL   = "models/gemini-2.5-flash"

# ─── Page Config ─────────────────────────────────────────
st.set_page_config(
    page_title=f"{BRAND_NAME} · {APP_SUBTITLE}",
    page_icon="sh1.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@500;700;800&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --bg:      #0f0f0f;
    --surface: #1a1a1a;
    --surf2:   #222222;
    --border:  #2a2a2a;
    --orange:  #f97316;
    --orange2: #fb923c;
    --ash:     #a3a3a3;
    --white:   #f5f5f5;
    --dim:     #525252;
    --ok:      #22c55e;
    --err:     #ef4444;
}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"] {
    background-color: var(--bg) !important;
    color: var(--white) !important;
    font-family: 'Inter', sans-serif !important;
}

/* hide sidebar toggle arrow & footer */
[data-testid="collapsedControl"],
[data-testid="stSidebar"],
footer { display: none !important; }

/* ── brand bar ── */
.brand-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.4rem 0 1.2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2.4rem;
}
.brand-left { display: flex; align-items: center; gap: 13px; }
.brand-logo {
    width: 40px; height: 40px;
    border-radius: 10px;
    object-fit: cover;
    border: 1px solid var(--border);
}
.brand-initials {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, #f97316, #7c2d12);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.05rem; font-weight: 800;
    color: white; font-family: 'Syne', sans-serif;
    flex-shrink: 0;
    letter-spacing: -0.02em;
}
.brand-name {
    font-family: 'Syne', sans-serif;
    font-weight: 800; font-size: 1.05rem;
    color: var(--white); letter-spacing: -0.02em;
    line-height: 1.1;
}
.brand-sub {
    font-size: 0.68rem; color: var(--ash);
    letter-spacing: 0.07em; text-transform: uppercase;
}
.brand-pill {
    font-size: 0.62rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
    padding: 4px 11px; border-radius: 20px;
    border: 1px solid var(--orange); color: var(--orange);
}

/* ── page hero ── */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.3rem; font-weight: 800;
    letter-spacing: -0.04em; line-height: 1.1;
    color: var(--white); margin-bottom: 0.4rem;
}
.hero-title span { color: var(--orange); }
.hero-desc {
    color: var(--ash); font-size: 0.88rem;
    line-height: 1.6; margin-bottom: 2rem;
}

/* ── file uploader ── */
[data-testid="stFileUploader"] > div {
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 14px !important;
    transition: border-color .2s;
}
[data-testid="stFileUploader"] > div:hover {
    border-color: var(--orange) !important;
}
[data-testid="stFileUploader"] label { display: none !important; }

/* ── file pill ── */
.file-pill {
    display: flex; align-items: center; gap: 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--orange);
    border-radius: 10px;
    padding: 0.8rem 1.1rem;
    margin: 0.6rem 0 1.2rem 0;
}
.fp-name { font-weight: 600; font-size: 0.88rem; color: var(--white); }
.fp-size { font-size: 0.72rem; color: var(--ash); }

/* ── run button ── */
.stButton > button {
    background: var(--orange) !important;
    color: #0f0f0f !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.93rem !important;
    padding: 0.65rem 1.6rem !important;
    width: 100% !important;
    transition: opacity .15s, transform .15s !important;
}
.stButton > button:hover { opacity:.88 !important; transform:translateY(-1px) !important; }
.stButton > button:disabled { background: var(--surf2) !important; color: var(--dim) !important; }

/* ── metrics row ── */
.metrics-row { display:flex; gap:12px; margin:1.5rem 0; }
.metric-tile {
    flex:1; background:var(--surface);
    border:1px solid var(--border);
    border-radius:10px; padding:1rem; text-align:center;
}
.metric-num {
    font-family:'Syne',sans-serif; font-size:1.8rem;
    font-weight:800; color:var(--orange); line-height:1;
}
.metric-lbl {
    font-size:0.67rem; color:var(--ash);
    text-transform:uppercase; letter-spacing:.08em; margin-top:4px;
}

/* ── divider ── */
.sec-div {
    display:flex; align-items:center; gap:12px;
    margin:2rem 0 1.5rem 0;
}
.sec-div hr { flex:1; border:none; border-top:1px solid var(--border); margin:0; }
.sec-lbl {
    font-size:.68rem; text-transform:uppercase;
    letter-spacing:.1em; color:var(--dim); white-space:nowrap;
}

/* ── answer box ── */
.answer-box {
    background:var(--surface);
    border:1px solid var(--border);
    border-left:3px solid var(--orange);
    border-radius:12px;
    padding:1.3rem 1.5rem;
    margin-bottom: .5rem;
}
/* ensure markdown elements inside answer-box look right */
.answer-box p  { font-size:.9rem; line-height:1.75; color:var(--white); margin:.4rem 0; }
.answer-box li { font-size:.9rem; line-height:1.7;  color:var(--white); }
.answer-box h1,.answer-box h2,.answer-box h3 {
    font-family:'Syne',sans-serif; color:var(--white);
    margin:.8rem 0 .3rem 0;
}
.answer-box code {
    background:var(--surf2); border:1px solid var(--border);
    border-radius:4px; padding:1px 5px;
    font-size:.82rem; color:var(--orange2);
}
.answer-box pre {
    background:var(--surf2); border:1px solid var(--border);
    border-radius:8px; padding:1rem;
    overflow-x:auto; font-size:.8rem;
}
.answer-box table {
    width:100%; border-collapse:collapse;
    font-size:.83rem; margin:.6rem 0;
}
.answer-box th {
    background:var(--surf2); color:var(--orange2);
    padding:.5rem .75rem; text-align:left;
    border:1px solid var(--border); font-weight:600;
}
.answer-box td {
    padding:.45rem .75rem; border:1px solid var(--border);
    color:var(--ash);
}
.answer-box tr:nth-child(even) td { background:rgba(255,255,255,.02); }
/* MathJax output */
.answer-box mjx-container { color:var(--white) !important; }

/* ── image label ── */
.img-lbl {
    font-size:.68rem; text-transform:uppercase;
    letter-spacing:.1em; color:var(--ash);
    margin:1rem 0 .5rem 0;
}

/* ── chunk card ── */
.chunk-card {
    background:var(--surf2);
    border:1px solid var(--border);
    border-radius:8px; padding:.85rem 1rem;
    margin-bottom:.55rem; font-size:.77rem;
    line-height:1.5; color:var(--ash);
}

/* ── tags ── */
.tag {
    display:inline-block; padding:1px 7px;
    border-radius:4px; font-size:.59rem;
    font-weight:600; letter-spacing:.06em;
    margin-right:4px; text-transform:uppercase;
}
.t-text  { background:rgba(249,115,22,.1); color:#fb923c; border:1px solid rgba(249,115,22,.2);}
.t-table { background:rgba(163,163,163,.08); color:#a3a3a3; border:1px solid rgba(163,163,163,.18);}
.t-image { background:rgba(34,197,94,.08); color:#4ade80; border:1px solid rgba(34,197,94,.18);}

/* ── chat ── */
[data-testid="stChatMessage"] { background:transparent !important; }
[data-testid="stChatMessageContent"] {
    background:var(--surface) !important;
    border:1px solid var(--border) !important;
    border-radius:10px !important;
    color:var(--white) !important;
    font-size:.88rem !important;
}
[data-testid="stChatInput"] textarea {
    background:var(--surface) !important;
    border:1px solid var(--border) !important;
    border-radius:10px !important;
    color:var(--white) !important;
    font-size:.88rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color:var(--orange) !important;
    box-shadow:0 0 0 2px rgba(249,115,22,.12) !important;
}

/* ── expander ── */
[data-testid="stExpander"] {
    background:var(--surf2) !important;
    border:1px solid var(--border) !important;
    border-radius:10px !important;
}
[data-testid="stExpander"] summary {
    font-size:.79rem !important; color:var(--ash) !important;
}

/* ── progress ── */
.stProgress > div > div > div { background:var(--orange) !important; }

/* ── tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    gap:4px; border-bottom:1px solid var(--border) !important;
}
[data-testid="stTabs"] button[role="tab"] {
    font-family:'Inter',sans-serif !important;
    font-size:.8rem !important; font-weight:500 !important;
    color:var(--ash) !important; background:transparent !important;
    border-radius:6px 6px 0 0 !important; padding:6px 16px !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color:var(--orange) !important;
    border-bottom:2px solid var(--orange) !important;
    background:rgba(249,115,22,.06) !important;
}

/* ── log panel ── */
.log-wrap {
    background:var(--surface); border:1px solid var(--border);
    border-radius:10px; padding:1rem 1.2rem;
    font-family:'Courier New',monospace; font-size:.74rem;
    max-height:360px; overflow-y:auto;
}
.ll { padding:2px 0; border-bottom:1px solid var(--border); color:var(--dim); }
.ll.ok  { color:var(--ok); }
.ll.err { color:var(--err); }
.ll .px { color:var(--orange2); margin-right:6px; }

hr { border-color:var(--border) !important; }
label { color:var(--ash) !important; font-size:.75rem !important; }

/* ── quiz ── */
.quiz-q {
    background:var(--surface);
    border:1px solid var(--border);
    border-radius:12px;
    padding:1.3rem 1.5rem;
    margin-bottom:1.2rem;
}
.quiz-q-num {
    font-size:.65rem; text-transform:uppercase;
    letter-spacing:.1em; color:var(--orange);
    font-weight:600; margin-bottom:.4rem;
}
.quiz-q-text {
    font-size:.95rem; font-weight:500;
    color:var(--white); line-height:1.5;
    margin-bottom:1rem;
}
.quiz-opt {
    display:flex; align-items:center; gap:10px;
    background:var(--surf2); border:1px solid var(--border);
    border-radius:8px; padding:.65rem 1rem;
    margin-bottom:.5rem; cursor:pointer;
    font-size:.85rem; color:var(--ash);
    transition:border-color .15s, color .15s;
}
.quiz-opt:hover { border-color:var(--orange); color:var(--white); }
.quiz-opt.correct {
    border-color:#22c55e; color:#22c55e;
    background:rgba(34,197,94,.08);
}
.quiz-opt.wrong {
    border-color:#ef4444; color:#ef4444;
    background:rgba(239,68,68,.08);
}
.quiz-score-card {
    background:var(--surface);
    border:1px solid var(--border);
    border-radius:14px; padding:2rem;
    text-align:center; margin-bottom:1.5rem;
}
.quiz-score-num {
    font-family:'Syne',sans-serif;
    font-size:3.5rem; font-weight:800;
    color:var(--orange); line-height:1;
}
.quiz-score-lbl {
    font-size:.75rem; color:var(--ash);
    text-transform:uppercase; letter-spacing:.1em;
    margin-top:.3rem;
}
.quiz-explanation {
    background:var(--surf2);
    border-left:3px solid var(--orange);
    border-radius:0 8px 8px 0;
    padding:.7rem 1rem;
    font-size:.8rem; color:var(--ash);
    margin-top:.5rem; line-height:1.5;
}
.diff-badge {
    display:inline-block; padding:3px 10px;
    border-radius:20px; font-size:.65rem;
    font-weight:700; letter-spacing:.07em;
    text-transform:uppercase; margin-right:6px;
}
.diff-easy   { background:rgba(34,197,94,.12); color:#4ade80; border:1px solid rgba(34,197,94,.25);}
.diff-medium { background:rgba(249,115,22,.12); color:#fb923c; border:1px solid rgba(249,115,22,.25);}
.diff-hard   { background:rgba(239,68,68,.12);  color:#f87171; border:1px solid rgba(239,68,68,.25);}
</style>
""", unsafe_allow_html=True)

# ─── MathJax (renders $...$ and $$...$$ LaTeX in answers) ───
st.markdown("""
<script>
window.MathJax = {
  tex: { inlineMath: [['$','$']], displayMath: [['$$','$$']] },
  svg: { fontCache: 'global' }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" async></script>
""", unsafe_allow_html=True)
# User isolation — each browser session gets its own UUID so
# multiple users never share the same ChromaDB folder or state.
if "user_id" not in st.session_state:
    st.session_state.user_id = uuid.uuid4().hex

USER_PERSIST_DIR = os.path.join(DEFAULT_PERSIST_DIR, st.session_state.user_id)

for k, v in {
    "db": None,
    "processed_chunks": [],
    "pipeline_ran": False,
    "logs": [],
    "metrics": {"elements": 0, "chunks": 0, "docs": 0},
    "chat_history": [],
    # ── quiz ──
    "quiz_questions": [],      # list of dicts from LLM
    "quiz_answers": {},        # {q_index: chosen_option_index}
    "quiz_submitted": False,
    "quiz_generating": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Helpers ─────────────────────────────────────────────
def log(msg, level="info"):
    st.session_state.logs.append({"msg": msg, "level": level})

def _hash(s: str) -> str:
    """MD5 fingerprint of a string — used for deduplication."""
    return hashlib.md5(s.encode()).hexdigest()

def collect_content(chunks):
    """
    Walk retrieved chunks and return three deduplicated lists:
      - unique_images  : base64 strings (no duplicates by content hash)
      - unique_tables  : HTML strings   (no duplicates by content hash)
      - unique_texts   : raw text blocks (no duplicates by content hash)
    """
    seen_imgs   = set()
    seen_tables = set()
    seen_texts  = set()

    unique_images  = []
    unique_tables  = []
    unique_texts   = []

    for c in chunks:
        if "original_content" not in c.metadata:
            continue
        orig = json.loads(c.metadata["original_content"])

        # ── images ──
        for b64 in orig.get("images_base64", []):
            if not b64:
                continue
            h = _hash(b64)
            if h not in seen_imgs:
                seen_imgs.add(h)
                unique_images.append(b64)

        # ── tables ──
        for tbl in orig.get("tables_html", []):
            if not tbl:
                continue
            h = _hash(tbl.strip())
            if h not in seen_tables:
                seen_tables.add(h)
                unique_tables.append(tbl)

        # ── raw text ──
        txt = orig.get("raw_text", "").strip()
        if txt:
            h = _hash(txt)
            if h not in seen_texts:
                seen_texts.add(h)
                unique_texts.append(txt)

    return unique_images, unique_tables, unique_texts

def render_answer(answer, images):
    """
    Render the LLM answer with full markdown + LaTeX support.

    Streamlit's st.markdown() handles:
      - **bold**, *italic*, `code`, tables, bullet lists
      - LaTeX via $...$ (inline) and $$...$$ (block)
      - Code blocks with syntax highlighting

    We wrap it in a styled container div for the orange left-border
    look, but the actual text goes through st.markdown() not raw HTML
    so nothing gets escaped or stripped.
    """
    # opening styled wrapper
    st.markdown(
        '<div class="answer-box">',
        unsafe_allow_html=True
    )
    # render content through Streamlit — preserves markdown, LaTeX, tables
    st.markdown(answer)
    # close wrapper
    st.markdown('</div>', unsafe_allow_html=True)

    if images:
        st.markdown('<div class="img-lbl">📷 Referenced figures from document</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(images), 3))
        for i, b64 in enumerate(images[:6]):
            try:
                cols[i % len(cols)].image(base64.b64decode(b64), use_container_width=True)
            except Exception:
                pass

def _is_quota_error(e: Exception) -> bool:
    s = str(e)
    return "429" in s or "RESOURCE_EXHAUSTED" in s or "quota" in s.lower()

def _groq_messages(gemini_messages):
    """
    Convert a LangChain HumanMessage list (which may contain image_url blocks)
    into plain-text-only messages safe for Groq (no vision support).
    Images are dropped; everything else is kept.
    """
    from langchain_core.messages import HumanMessage as HM
    plain_parts = []
    for msg in gemini_messages:
        if hasattr(msg, "content"):
            if isinstance(msg.content, str):
                plain_parts.append(msg.content)
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        plain_parts.append(block["text"])
                    # image_url blocks are silently dropped — Groq can't handle them
    return [HM(content="\n\n".join(plain_parts))]

def invoke_with_fallback(messages, status_slot=None):
    """
    Tier 1 — Gemini (vision-capable, 20 req/day free).
    Tier 2 — Groq / llama-3.3-70b (text+tables only, 14,400 req/day free).

    On a quota/rate-limit error from Gemini, switches to Groq immediately
    and shows the user a small notice. Any non-quota error is re-raised.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    from dotenv import load_dotenv
    load_dotenv()

    # ── Tier 1: Gemini ───────────────────────────────────
    try:
        llm = ChatGoogleGenerativeAI(model=DEFAULT_LLM_MODEL, temperature=0)
        return llm.invoke(messages), "gemini"
    except Exception as e:
        if not _is_quota_error(e):
            raise
        # quota hit → fall through to Groq
        if status_slot:
            status_slot.markdown(
                '<div style="background:#1a1a1a; border:1px solid #2a2a2a; '
                'border-left:3px solid #f97316; border-radius:10px; '
                'padding:0.75rem 1.1rem; font-size:0.8rem; color:#a3a3a3; margin-bottom:8px;">'
                '⚡ Gemini quota reached — switching to <strong style="color:#f97316">Groq (Llama 3.3)</strong>. '
                'Images won\'t be analysed this turn but will still display.</div>',
                unsafe_allow_html=True
            )

    # ── Tier 2: Groq ────────────────────────────────────
    try:
        from langchain_groq import ChatGroq
        groq_llm  = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        groq_msgs = _groq_messages(messages)   # strip image blocks
        return groq_llm.invoke(groq_msgs), "groq"
    except Exception as e2:
        if _is_quota_error(e2):
            raise RuntimeError(
                "Both Gemini and Groq have hit their rate limits. "
                "Please wait a few minutes and try again."
            ) from e2
        raise

def generate_quiz(num_questions: int, difficulty: str) -> list:
    """
    Pull random chunks from the indexed document and ask the LLM to produce
    a JSON quiz. Returns a list of dicts:
      { "question": str, "options": [A,B,C,D], "answer": int (0-3), "explanation": str }
    """
    from langchain_core.messages import HumanMessage

    # sample up to 6 chunks as context so we cover the doc breadth
    docs = st.session_state.processed_chunks
    import random
    sample = random.sample(docs, min(6, len(docs)))
    context = "\n\n---\n\n".join(
        json.loads(d.metadata["original_content"]).get("raw_text", d.page_content)[:600]
        for d in sample
    )

    diff_instruction = {
        "Easy":   "straightforward recall questions — answers are stated directly in the text",
        "Medium": "questions that require understanding and connecting ideas across the text",
        "Hard":   "challenging questions requiring inference, analysis, or application of concepts",
    }[difficulty]

    prompt = f"""You are a quiz generator. Based on the document excerpts below, create exactly {num_questions} multiple-choice questions.

Difficulty: {difficulty} — {diff_instruction}

DOCUMENT EXCERPTS:
{context}

STRICT OUTPUT FORMAT — respond with valid JSON only, no markdown fences, no extra text:
[
  {{
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": 0,
    "explanation": "Brief explanation of why the correct answer is right."
  }}
]

Rules:
- "answer" is the 0-based index of the correct option (0=A, 1=B, 2=C, 3=D)
- All 4 options must be plausible — no obviously wrong distractors
- Questions must be answerable from the document content provided
- Return exactly {num_questions} question objects in the array
- No markdown, no code fences — raw JSON only"""

    msgs = [HumanMessage(content=prompt)]
    response, _ = invoke_with_fallback(msgs)
    raw = response.content.strip()

    # strip any accidental markdown fences
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw, flags=re.MULTILINE).strip()

    questions = json.loads(raw)

    # validate shape
    for q in questions:
        assert "question" in q and "options" in q and "answer" in q
        assert len(q["options"]) == 4
        assert 0 <= q["answer"] <= 3

    return questions


# ─── Branding Header ─────────────────────────────────────
initial = BRAND_NAME[0].upper() if BRAND_NAME else "?"
if BRAND_LOGO and os.path.exists(BRAND_LOGO):
    with open(BRAND_LOGO, "rb") as f:
        enc = base64.b64encode(f.read()).decode()
    ext  = BRAND_LOGO.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    logo_html = f'<img class="brand-logo" src="data:{mime};base64,{enc}" />'
else:
    logo_html = f'<div class="brand-initials">{initial}</div>'

st.markdown(f"""
<div class="brand-bar">
  <div class="brand-left">
    {logo_html}
    <div>
      <div class="brand-name">{BRAND_NAME}</div>
      <div class="brand-sub">{APP_SUBTITLE}</div>
    </div>
  </div>
  <div class="brand-pill">Powered by AI</div>
</div>
""", unsafe_allow_html=True)

# ─── Hero ────────────────────────────────────────────────
st.markdown("""
<div class="hero-title">Ask your <span>documents.</span></div>
<div class="hero-desc">
Upload any document like PDF, Word, PowerPoint, Excel, images, and more.
The pipeline extracts text, tables &amp; images, builds a smart index,
then lets you chat with the content or test your understanding.
</div>
""", unsafe_allow_html=True)

# ─── Tabs ────────────────────────────────────────────────
tab_ingest, tab_query, tab_quiz, tab_logs = st.tabs(
    ["  📄  Upload & Index  ", "  💬  Chat  ", "  🧠  Quiz  ", "  🗒  Logs  "]
)

# ════════════════════════════════════════════════════════
# TAB 1 — INGEST
# ════════════════════════════════════════════════════════

# Supported types → (display label, icon, temp suffix)
SUPPORTED_TYPES = {
    "pdf":  ("PDF",        "📄"),
    "docx": ("Word Doc",   "📝"),
    "pptx": ("PowerPoint", "📊"),
    "xlsx": ("Excel",      "📗"),
    "txt":  ("Text File",  "📃"),
    "md":   ("Markdown",   "📃"),
    "html": ("HTML",       "🌐"),
    "csv":  ("CSV",        "📋"),
    "png":  ("Image",      "🖼️"),
    "jpg":  ("Image",      "🖼️"),
    "jpeg": ("Image",      "🖼️"),
}

with tab_ingest:

    uploaded_file = st.file_uploader(
        "Upload document",
        type=list(SUPPORTED_TYPES.keys()),
        label_visibility="collapsed"
    )

    if uploaded_file:
        ext     = uploaded_file.name.rsplit(".", 1)[-1].lower()
        f_label, f_icon = SUPPORTED_TYPES.get(ext, ("Document", "📄"))
        size_kb = uploaded_file.size / 1024
        st.markdown(f"""
        <div class="file-pill">
            <div style="font-size:1.4rem">{f_icon}</div>
            <div>
                <div class="fp-name">{uploaded_file.name}</div>
                <div class="fp-size">{size_kb:.1f} KB · {f_label}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    run_btn = st.button("Run Pipeline →", disabled=(uploaded_file is None))

    # supported formats strip
    st.markdown("""
    <div style="margin:.6rem 0 1.4rem 0; display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
        <span style="font-size:.65rem; color:#525252; text-transform:uppercase; letter-spacing:.08em; margin-right:4px;">Supports</span>
        <span class="tag t-text">PDF</span>
        <span class="tag t-text">DOCX</span>
        <span class="tag t-text">PPTX</span>
        <span class="tag t-table">XLSX</span>
        <span class="tag t-table">CSV</span>
        <span class="tag t-text">TXT</span>
        <span class="tag t-text">MD</span>
        <span class="tag t-text">HTML</span>
        <span class="tag t-image">PNG</span>
        <span class="tag t-image">JPG</span>
    </div>
    """, unsafe_allow_html=True)

    # metrics + chunk preview after pipeline runs
    if st.session_state.pipeline_ran:
        m = st.session_state.metrics
        st.markdown(f"""
        <div class="metrics-row">
            <div class="metric-tile"><div class="metric-num">{m['elements']}</div><div class="metric-lbl">Elements</div></div>
            <div class="metric-tile"><div class="metric-num">{m['chunks']}</div><div class="metric-lbl">Chunks</div></div>
            <div class="metric-tile"><div class="metric-num">{m['docs']}</div><div class="metric-lbl">Indexed</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sec-div"><hr/><span class="sec-lbl">Chunk preview</span><hr/></div>', unsafe_allow_html=True)
        for i, doc in enumerate(st.session_state.processed_chunks[:5]):
            preview = doc.page_content[:250] + ("…" if len(doc.page_content) > 250 else "")
            orig    = json.loads(doc.metadata.get("original_content", "{}"))
            tags    = '<span class="tag t-text">text</span>'
            if orig.get("tables_html"):   tags += '<span class="tag t-table">table</span>'
            if orig.get("images_base64"): tags += '<span class="tag t-image">image</span>'
            with st.expander(f"Chunk {i + 1}"):
                st.markdown(f'<div style="margin-bottom:6px">{tags}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="chunk-card">{preview}</div>', unsafe_allow_html=True)

    # ── pipeline execution ──
    if run_btn and uploaded_file:
        st.session_state.logs = []

        with st.status("Running pipeline…", expanded=True) as status:
            try:
                st.write("📂 Saving file…")
                ext      = uploaded_file.name.rsplit(".", 1)[-1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                log(f"Saved → {tmp_path}")

                st.write("📦 Loading modules…")
                from unstructured.chunking.title import chunk_by_title
                from langchain_core.documents import Document
                from langchain_huggingface import HuggingFaceEmbeddings
                from langchain_chroma import Chroma
                from dotenv import load_dotenv
                load_dotenv()
                log("Modules loaded", "success")

                # 1 ─ partition (route by file type)
                f_label = SUPPORTED_TYPES.get(ext, ("Document", "📄"))[0]
                st.write(f"📄 Partitioning {f_label}…")

                if ext == "pdf":
                    from unstructured.partition.pdf import partition_pdf
                    elements = partition_pdf(
                        filename=tmp_path,
                        strategy="hi_res",
                        infer_table_structure=True,
                        extract_image_block_types=["Image"],
                        extract_image_block_to_payload=True,
                    )
                elif ext == "docx":
                    from unstructured.partition.docx import partition_docx
                    elements = partition_docx(filename=tmp_path)
                elif ext == "pptx":
                    from unstructured.partition.pptx import partition_pptx
                    elements = partition_pptx(filename=tmp_path)
                elif ext == "xlsx":
                    from unstructured.partition.xlsx import partition_xlsx
                    elements = partition_xlsx(filename=tmp_path)
                elif ext in ("png", "jpg", "jpeg"):
                    from unstructured.partition.image import partition_image
                    elements = partition_image(filename=tmp_path, strategy="hi_res")
                elif ext == "html":
                    from unstructured.partition.html import partition_html
                    elements = partition_html(filename=tmp_path)
                elif ext == "csv":
                    from unstructured.partition.csv import partition_csv
                    elements = partition_csv(filename=tmp_path)
                elif ext in ("txt", "md"):
                    from unstructured.partition.text import partition_text
                    elements = partition_text(filename=tmp_path)
                else:
                    from unstructured.partition.auto import partition
                    elements = partition(filename=tmp_path)
                st.session_state.metrics["elements"] = len(elements)
                log(f"{len(elements)} elements extracted", "success")
                st.write(f"✅ {len(elements)} elements extracted")

                # 2 ─ chunk
                st.write("🔨 Chunking…")
                chunks = chunk_by_title(
                    elements,
                    max_characters=DEFAULT_MAX_CHARS,
                    new_after_n_chars=DEFAULT_NEW_AFTER,
                    combine_text_under_n_chars=DEFAULT_COMBINE,
                )
                st.session_state.metrics["chunks"] = len(chunks)
                log(f"{len(chunks)} chunks created", "success")
                st.write(f"✅ {len(chunks)} chunks")

                # 3 ─ AI summarise
                st.write("🧠 Generating AI summaries…")
                prog = st.progress(0)

                def separate(chunk):
                    d = {"text": chunk.text, "tables": [], "images": []}
                    if hasattr(chunk, "metadata") and hasattr(chunk.metadata, "orig_elements"):
                        for el in chunk.metadata.orig_elements:
                            t = type(el).__name__
                            if t == "Table":
                                d["tables"].append(getattr(el.metadata, "text_as_html", el.text))
                            elif t == "Image" and hasattr(el.metadata, "image_base64"):
                                d["images"].append(el.metadata.image_base64)
                    return d

                def ai_summary(text, tables, images):
                    try:
                        from langchain_core.messages import HumanMessage
                        p = f"Create a detailed, searchable description for retrieval.\n\nTEXT:\n{text}\n\n"
                        for i, t in enumerate(tables):
                            p += f"TABLE {i+1}:\n{t}\n\n"
                        p += "Cover key facts, numbers, topics, questions this answers, and search terms.\n\nDESCRIPTION:"
                        content = [{"type": "text", "text": p}]
                        for img in images:
                            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
                        response, _ = invoke_with_fallback([HumanMessage(content=content)])
                        return response.content
                    except Exception as e:
                        log(f"AI summary error: {e}", "error")
                        return text

                docs = []
                for i, chunk in enumerate(chunks):
                    cd = separate(chunk)
                    enhanced = (
                        ai_summary(cd["text"], cd["tables"], cd["images"])
                        if (cd["tables"] or cd["images"]) else cd["text"]
                    )
                    docs.append(Document(
                        page_content=enhanced,
                        metadata={"original_content": json.dumps({
                            "raw_text":     cd["text"],
                            "tables_html":  cd["tables"],
                            "images_base64": cd["images"],
                        })}
                    ))
                    prog.progress((i + 1) / len(chunks))

                log(f"{len(docs)} docs processed", "success")
                st.write(f"✅ {len(docs)} docs processed")

                # 4 ─ vector store
                st.write("🔮 Building vector store…")
                embeddings = HuggingFaceEmbeddings(
                    model_name=DEFAULT_EMBED_MODEL,
                    model_kwargs={"device": "cpu"},
                )
                db = Chroma.from_documents(
                    documents=docs,
                    embedding=embeddings,
                    persist_directory=USER_PERSIST_DIR,
                    collection_metadata={"hnsw:space": "cosine"},
                )

                st.session_state.db               = db
                st.session_state.processed_chunks = docs
                st.session_state.metrics["docs"]  = len(docs)
                st.session_state.pipeline_ran      = True
                log(f"Vector store ready → {USER_PERSIST_DIR}", "success")
                st.write(f"✅ {len(docs)} docs indexed")

                os.unlink(tmp_path)
                status.update(label="Pipeline complete ✅", state="complete")

            except Exception as e:
                log(f"Pipeline failed: {e}", "error")
                status.update(label=f"Failed: {e}", state="error")
                st.error(str(e))

        st.rerun()

# ════════════════════════════════════════════════════════
# TAB 2 — CHAT
# ════════════════════════════════════════════════════════
with tab_query:
    if not st.session_state.pipeline_ran:
        st.markdown("""
        <div style="text-align:center; padding:3rem 1rem;
                    border:1px dashed #2a2a2a; border-radius:14px; margin-top:1rem;">
            <div style="font-size:2.4rem; margin-bottom:.75rem">💬</div>
            <div style="font-family:'Syne',sans-serif; font-weight:700; font-size:1.05rem;
                        color:#f5f5f5; margin-bottom:.4rem;">No document indexed yet</div>
            <div style="color:#525252; font-size:.82rem">
                Go to <strong style="color:#a3a3a3">Upload &amp; Index</strong> to get started
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # replay history
        for turn in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(turn["query"])
            with st.chat_message("assistant"):
                render_answer(turn["answer"], turn.get("images", []))
                if turn.get("chunks"):
                    with st.expander(f"📎 {len(turn['chunks'])} source chunks"):
                        for i, c in enumerate(turn["chunks"]):
                            st.markdown(
                                f'<div class="chunk-card"><strong>Source {i+1}</strong>'
                                f'<br>{c.page_content[:300]}…</div>',
                                unsafe_allow_html=True
                            )

        query = st.chat_input("Ask anything about your document…")

        if query:
            with st.chat_message("user"):
                st.write(query)

            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    try:
                        from langchain_core.messages import HumanMessage
                        from dotenv import load_dotenv
                        load_dotenv()

                        retriever     = st.session_state.db.as_retriever(search_kwargs={"k": DEFAULT_TOP_K})
                        retrieved     = retriever.invoke(query)

                        # ── deduplicate all content across chunks ──
                        chunk_images, chunk_tables, chunk_texts = collect_content(retrieved)

                        prompt = f"Answer this question using the documents below.\n\nQUESTION: {query}\n\nDOCUMENTS:\n"

                        # add deduplicated text blocks
                        for i, txt in enumerate(chunk_texts):
                            prompt += f"\n--- Text block {i+1} ---\n{txt}\n"

                        # add deduplicated tables
                        if chunk_tables:
                            prompt += "\n--- Tables ---\n"
                            for j, tbl in enumerate(chunk_tables):
                                prompt += f"Table {j+1}:\n{tbl}\n\n"

                        if chunk_images:
                            prompt += f"\n{len(chunk_images)} unique document image(s) are attached — reference them where relevant.\n"
                        prompt += """
Formatting rules — follow these strictly:
- Use $...$ for inline math expressions (e.g. $x^2$)
- Use $$...$$ on its own line for block/display equations (e.g. $$ E = mc^2 $$)
- Use markdown tables for tabular data
- Use **bold** for key terms, `code` for variable names or constants
- Use bullet points or numbered lists where appropriate
- Never write raw LaTeX like \\frac without wrapping it in $ signs

Provide a clear, complete answer. Describe any relevant figures.

ANSWER:"""

                        content = [{"type": "text", "text": prompt}]
                        for b64 in chunk_images[:4]:
                            content.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                            })

                        notice_slot = st.empty()
                        response, provider = invoke_with_fallback(
                            [HumanMessage(content=content)],
                            status_slot=notice_slot
                        )
                        answer = response.content

                        # show which provider answered (subtle badge)
                        if provider == "groq":
                            notice_slot.markdown(
                                '<div style="font-size:0.65rem; color:#525252; margin-bottom:6px;">'
                                '⚡ Answered by Groq · Llama 3.3 70B (images not analysed this turn)</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            notice_slot.empty()

                        render_answer(answer, chunk_images)

                        with st.expander(f"📎 {len(retrieved)} source chunks"):
                            for i, c in enumerate(retrieved):
                                st.markdown(
                                    f'<div class="chunk-card"><strong>Source {i+1}</strong>'
                                    f'<br>{c.page_content[:300]}…</div>',
                                    unsafe_allow_html=True
                                )

                        st.session_state.chat_history.append({
                            "query":  query,
                            "answer": answer,
                            "chunks": retrieved,
                            "images": chunk_images,
                        })

                    except Exception as e:
                        st.error(f"Error: {e}")

        if st.session_state.chat_history:
            if st.button("🗑 Clear chat"):
                st.session_state.chat_history = []
                st.rerun()

# ════════════════════════════════════════════════════════
# TAB 3 — QUIZ
# ════════════════════════════════════════════════════════
with tab_quiz:
    if not st.session_state.pipeline_ran:
        st.markdown("""
        <div style="text-align:center; padding:3rem 1rem;
                    border:1px dashed #2a2a2a; border-radius:14px; margin-top:1rem;">
            <div style="font-size:2.4rem; margin-bottom:.75rem">🧠</div>
            <div style="font-family:'Syne',sans-serif; font-weight:700; font-size:1.05rem;
                        color:#f5f5f5; margin-bottom:.4rem;">No document indexed yet</div>
            <div style="color:#525252; font-size:.82rem">
                Upload and index a document first, then come back here to test your understanding.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── setup screen ─────────────────────────────────
        if not st.session_state.quiz_questions:
            st.markdown("""
            <div style="margin-bottom:1.5rem;">
                <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.6rem;
                            letter-spacing:-0.03em; color:#f5f5f5; margin-bottom:.3rem;">
                    Test your understanding
                </div>
                <div style="color:#a3a3a3; font-size:.85rem; line-height:1.5;">
                    The quiz is generated directly from your uploaded document.
                    Pick a difficulty and number of questions to begin.
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                difficulty = st.selectbox(
                    "Difficulty",
                    ["Easy", "Medium", "Hard"],
                    index=1,
                    label_visibility="visible"
                )
            with col_b:
                num_q = st.selectbox(
                    "Number of questions",
                    [3, 5, 10],
                    index=1,
                    label_visibility="visible"
                )

            diff_class = {"Easy": "easy", "Medium": "medium", "Hard": "hard"}[difficulty]
            st.markdown(f"""
            <div style="margin:.8rem 0 1.2rem 0;">
                <span class="diff-badge diff-{diff_class}">{difficulty}</span>
                <span style="color:#525252; font-size:.78rem;">
                    {num_q} questions · generated from your document
                </span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🧠 Generate Quiz"):
                with st.spinner("Generating questions from your document…"):
                    try:
                        qs = generate_quiz(num_q, difficulty)
                        st.session_state.quiz_questions = qs
                        st.session_state.quiz_answers   = {}
                        st.session_state.quiz_submitted  = False
                        st.rerun()
                    except json.JSONDecodeError:
                        st.error("The AI returned malformed JSON. Please try again.")
                    except Exception as e:
                        st.error(f"Quiz generation failed: {e}")

        # ── active quiz ───────────────────────────────────
        elif not st.session_state.quiz_submitted:
            questions = st.session_state.quiz_questions
            answered  = len(st.session_state.quiz_answers)
            total     = len(questions)

            # progress bar
            st.progress(answered / total)
            st.markdown(
                f'<div style="font-size:.72rem; color:#525252; margin-bottom:1.2rem;">'
                f'{answered} of {total} answered</div>',
                unsafe_allow_html=True
            )

            with st.form("quiz_form"):
                user_answers = {}
                for i, q in enumerate(questions):
                    st.markdown(f"""
                    <div class="quiz-q">
                        <div class="quiz-q-num">Question {i + 1} of {total}</div>
                        <div class="quiz-q-text">{q['question']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    choice = st.radio(
                        f"q_{i}",
                        options=q["options"],
                        index=st.session_state.quiz_answers.get(i, None),
                        label_visibility="collapsed",
                        key=f"radio_{i}"
                    )
                    user_answers[i] = q["options"].index(choice) if choice else None
                    st.markdown("<div style='margin-bottom:1rem'></div>", unsafe_allow_html=True)

                submitted = st.form_submit_button("✅ Submit Answers")
                if submitted:
                    # check all answered
                    if any(v is None for v in user_answers.values()):
                        st.warning("Please answer all questions before submitting.")
                    else:
                        st.session_state.quiz_answers   = user_answers
                        st.session_state.quiz_submitted  = True
                        st.rerun()

        # ── results screen ────────────────────────────────
        else:
            questions = st.session_state.quiz_questions
            answers   = st.session_state.quiz_answers
            total     = len(questions)
            correct   = sum(1 for i, q in enumerate(questions) if answers.get(i) == q["answer"])
            pct       = round((correct / total) * 100)

            # score card
            if pct >= 80:
                grade_color = "#22c55e"
                grade_msg   = "Excellent work! 🎉"
            elif pct >= 50:
                grade_color = "#f97316"
                grade_msg   = "Good effort — review the sections below."
            else:
                grade_color = "#ef4444"
                grade_msg   = "Keep studying — you'll get there!"

            st.markdown(f"""
            <div class="quiz-score-card">
                <div class="quiz-score-num" style="color:{grade_color};">{correct}/{total}</div>
                <div class="quiz-score-lbl">correct answers · {pct}%</div>
                <div style="color:{grade_color}; font-size:.9rem; margin-top:.6rem; font-weight:500;">
                    {grade_msg}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # per-question review
            st.markdown('<div class="sec-div"><hr/><span class="sec-lbl">Answer review</span><hr/></div>', unsafe_allow_html=True)

            for i, q in enumerate(questions):
                user_ans    = answers.get(i)
                correct_ans = q["answer"]
                is_correct  = user_ans == correct_ans

                icon = "✅" if is_correct else "❌"
                with st.expander(f"{icon}  Q{i+1}: {q['question'][:80]}…"):
                    for j, opt in enumerate(q["options"]):
                        if j == correct_ans and j == user_ans:
                            tag = "✅ Your answer · Correct"
                            css = "correct"
                        elif j == correct_ans:
                            tag = "✅ Correct answer"
                            css = "correct"
                        elif j == user_ans:
                            tag = "❌ Your answer"
                            css = "wrong"
                        else:
                            tag = ""
                            css = ""

                        border = f"border-color:#22c55e" if css == "correct" else (f"border-color:#ef4444" if css == "wrong" else "")
                        color  = f"color:#22c55e" if css == "correct" else (f"color:#ef4444" if css == "wrong" else "color:#a3a3a3")
                        st.markdown(f"""
                        <div class="quiz-opt" style="{border}; {color};">
                            <span style="font-weight:600; min-width:18px">{"ABCD"[j]}.</span>
                            <span>{opt}</span>
                            {f'<span style="margin-left:auto; font-size:.7rem; opacity:.8">{tag}</span>' if tag else ''}
                        </div>
                        """, unsafe_allow_html=True)

                    if q.get("explanation"):
                        st.markdown(f'<div class="quiz-explanation">💡 {q["explanation"]}</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Retake this quiz"):
                    st.session_state.quiz_answers   = {}
                    st.session_state.quiz_submitted  = False
                    st.rerun()
            with col2:
                if st.button("🆕 New quiz"):
                    st.session_state.quiz_questions = []
                    st.session_state.quiz_answers   = {}
                    st.session_state.quiz_submitted  = False
                    st.rerun()

# ════════════════════════════════════════════════════════
# TAB 4 — LOGS
# ════════════════════════════════════════════════════════
with tab_logs:
    st.markdown("### Pipeline logs")
    if not st.session_state.logs:
        st.markdown('<div style="color:#525252; font-size:.82rem; padding:.5rem 0">No logs yet.</div>', unsafe_allow_html=True)
    else:
        lines = ""
        for e in st.session_state.logs:
            cls = "ok" if e["level"] == "success" else ("err" if e["level"] == "error" else "")
            px  = "✅" if e["level"] == "success" else ("❌" if e["level"] == "error" else "›")
            lines += f'<div class="ll {cls}"><span class="px">{px}</span>{e["msg"]}</div>'
        st.markdown(f'<div class="log-wrap">{lines}</div>', unsafe_allow_html=True)

        if st.button("🗑 Clear logs"):
            st.session_state.logs = []
            st.rerun()