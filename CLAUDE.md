# EduCraft AI — Claude Code Context

## What This Project Is
AI-powered web app for teachers (primarily Indian curriculum: CBSE, ICSE, State Board, IB).
Generates teaching materials in seconds using Groq's free-tier LLM API.

**Live URL:** https://educraft-nufuobqzr5byvate92psfp.streamlit.app
**GitHub:** https://github.com/aditya2529/EduCraft
**Stack:** Streamlit · Python 3.9+ · Groq API (llama-3.1-8b-instant) · fpdf2 · python-pptx

---

## Current State — Phase 2 Complete

All three generators are built, QA-hardened, and deployed.

| Feature | Output | Status |
|---------|--------|--------|
| Presentation Generator | `.pptx` | ✅ Live |
| Lesson Plan Generator | `.pdf` | ✅ Live |
| Question Paper Generator | student `.pdf` + answer key `.pdf` | ✅ Live |

---

## File Map

```
educraft_app.py              — Main Streamlit app (all UI, session state, 3 tabs)
generators/
  presentation.py            — PPTX generation, Dr. Maya Chen persona, grade calibration
  lesson_plan.py             — PDF lesson plan, Prof. James Okafor persona, 5E model
  question_paper.py          — QP PDF, Dr. Rajan Mehta persona, Bloom's taxonomy
utils/
  groq_client.py             — Groq API wrapper (retry, timeout, JSON parse)
  export.py                  — All PDF/PPTX rendering (fpdf2 + python-pptx)
  unsplash.py                — Cover image fetch (Unsplash API or Pollinations fallback)
requirements.txt             — httpx, lxml, groq, fpdf2, python-pptx, streamlit
.env                         — GROQ_API_KEY, UNSPLASH_ACCESS_KEY (gitignored)
```

---

## Key Architecture Decisions

### Two-Phase Generation Pattern (Streamlit)
Streamlit reruns the entire script on every interaction. To show a "generating…" disabled
button state during a blocking API call, we use a two-phase pattern:
- **Phase 1** (form submit): save params to `session_state`, set `*_generating=True`, `st.rerun()`
- **Phase 2** (next render): if `generating=True`, run the API call, store result, `st.rerun()`
- **Phase 3** (next render): show result + download button

### PDF Generation Constraint
fpdf2 with Helvetica only supports **latin-1** characters. All AI-generated text passes
through `_safe()` in `export.py` which maps Unicode → ASCII equivalents before rendering.
Do NOT skip `_safe()` on any text that goes into fpdf2.

### Token Budget
`max_tokens=4096` in groq_client.py. The Question Paper tab enforces a pre-submit token
cap (~3800 estimated tokens) to prevent JSON truncation mid-response. Recommended maxima:
15 MCQs · 8 short · 3 long.

### Input Sanitization
All free-text user inputs (topic, subject, grade, objectives) pass through `_sanitize()`
in `educraft_app.py` before being injected into LLM prompts. Do not bypass this.

---

## Known Constraints

- **Groq free tier**: 14,400 TPM. Rate-limit retry is automatic (up to 3×, 62s wait each).
- **Model**: `llama-3.1-8b-instant` — smaller/faster than 70b but needs tighter prompts.
- **No auth**: anyone with the URL can use the app. API key is entered by the user.
- **Filename safety**: use `_safe_filename()` for all download filenames, not raw topic string.
- **latin-1 only**: fpdf2 can't render Unicode without font embedding. Always use `_safe()`.

---

## What's Next (Phase 3 Candidates)

1. **Worksheet Generator** — fill-in-the-blank, matching, short-answer practice sheets
2. **Rubric Generator** — grading criteria PDF for any assignment
3. **Assignment Brief** — project description + marking criteria
4. **Flashcard Pack** — printable Q&A revision cards
5. **Deploy with pre-loaded API key** — remove sidebar friction for non-technical teachers

---

## Do Not Touch Without Understanding
- `_safe()` in `export.py` — breaking this corrupts all PDF output
- The two-phase generation pattern — changing it breaks the button disable UX
- `response_format={"type": "json_object"}` in groq_client — removing it causes JSON parse failures
- `max_tokens=4096` — increasing this risks APIStatusError on free tier
