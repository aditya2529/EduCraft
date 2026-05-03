from utils.groq_client import call_groq, parse_json_response
from utils.export import create_presentation
from utils.unsplash import fetch_cover_image

# ── System persona ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are Dr. Maya Chen, a lead curriculum designer with a PhD in Educational Psychology from Harvard and 25 years of experience designing IB, AP, and national-award-winning classroom materials.

Your content philosophy:
1. NEVER state the obvious. Every bullet must deliver an INSIGHT — something that makes a student think "I never thought of it that way."
2. Always answer the student's unspoken question: "Why does this matter to MY life?"
3. Use concrete, vivid specifics over vague generalities. Not "plants are important" but "every breath you take contains oxygen released by a plant during photosynthesis."
4. Build MENTAL MODELS, not fact lists. Students forget facts; they remember frameworks.
5. Address the #1 misconception about each topic — name it and correct it.
6. Each slide must have a THROUGHLINE — a single core idea everything else supports.

CITATION RULES — READ CAREFULLY:
- DO NOT write "A study by X found that..." — this pattern causes you to fabricate references.
- State facts DIRECTLY without citing a source, OR name only institutions/events you are 100% certain are real.
- ALLOWED: "Cambridge Analytica harvested 87 million Facebook profiles without consent."
- ALLOWED: "The Pew Research Center found 45% of teens feel overwhelmed by social media pressure."
- ALLOWED: "Sean Parker, Facebook's founding president, admitted in 2017 that the app was designed to exploit human vulnerability."
- BANNED: "A study by the Journal of Community Psychology found that..."
- BANNED: "Researchers at the University of California found that..."
- BANNED: Any city programme, initiative, or policy you are not 100% certain is real.
- When in doubt: drop the citation and state the fact. A fact without a source is better than an invented source.

FACTUAL ACCURACY — NON-NEGOTIABLE:
- Every named example, statistic, person, date, or literary work must be verifiably real.
- NEVER say X "is like" Y when X IS Y (e.g., do not write "the Holocaust was like a genocide" — it IS a genocide).
- For topics involving human suffering, mental health, addiction, poverty, disability, religion, or discrimination: be engaging but NEVER trivialising. Facts and human stories only.

Quality bar: if a bullet could appear in a generic Google search summary, rewrite it. Every line must earn its place.

Return ONLY valid JSON. No markdown fences. No text outside the JSON."""


# ── Subject-specific pedagogical strategies ────────────────────────────────────
_SUBJECT_STRATEGY = {
    "science":    "Use the Predict-Observe-Explain cycle. Surface common misconceptions and correct them with evidence. Connect to real phenomena students can observe. Reference actual experiments or discoveries.",
    "biology":    "Use the Predict-Observe-Explain cycle. Surface common misconceptions and correct them with evidence. Connect to real phenomena students can observe. Reference actual discoveries (Darwin, Watson & Crick, etc.).",
    "chemistry":  "Connect atomic/molecular level to macroscopic observations. Use analogies for invisible phenomena. Include real industrial/everyday applications of every concept.",
    "physics":    "Always move from everyday observation to the underlying principle — not the reverse. Use thought experiments (like Einstein did). Quantify with memorable numbers, not vague descriptions.",
    "math":       "Show the WHY behind every procedure, not just the HOW. Include a real-world scenario where this exact calculation is used. Highlight the pattern or elegance, not just the steps. Anticipate the step where students most commonly make errors.",
    "mathematics":"Show the WHY behind every procedure, not just the HOW. Include a real-world scenario where this exact calculation is used. Highlight the pattern or elegance, not just the steps.",
    "history":    "Use causation, not just chronology. Every event needs a 'so what?' — its consequence on the world today. Include a human story or primary source voice. Avoid the 'great men' trap — show systemic forces.",
    "geography":  "Connect place to power, people, and change over time. Use data and statistics to ground abstract concepts. Link local to global. Include a case study the grade level can relate to.",
    "economics":  "Ground every concept in a choice a real person or government actually made. Use opportunity cost thinking throughout. Connect theory to a current news event students may have heard of.",
    "english":    "Teach reading as a thinking skill, not a decoding skill. Show HOW authors create meaning — technique, not just identification. Use short, powerful extracts. Connect literary themes to students' own lives.",
    "literature": "Focus on WHY the author made specific choices. Connect themes to human universals students recognise. Teach close reading as an argument, not a summary.",
    "computer science": "Always show the algorithm before the code. Connect computing concepts to real systems students use daily (Google, WhatsApp, Netflix). Emphasise problem decomposition over syntax.",
    "default":    "Connect every concept to a real-world application students encounter in daily life. Surface and correct the most common misconception. Use specific examples, not vague generalities. Build a mental model, not a fact list.",
}

def _subject_strategy(subject: str) -> str:
    key = subject.lower().strip()
    for k, v in _SUBJECT_STRATEGY.items():
        if k in key:
            return v
    return _SUBJECT_STRATEGY["default"]


# ── Grade-level detection ──────────────────────────────────────────────────────
import re as _re

def _grade_band(grade: str) -> str:
    """Return one of: 'primary', 'middle', 'high', 'university', 'unknown'."""
    g = grade.lower()
    if any(x in g for x in ["primary", "elementary", "junior", "kindergarten", "prep", "k-"]):
        return "primary"
    if any(x in g for x in ["college", "university", "undergraduate", "graduate",
                              "degree", "bachelor", "master", "phd"]):
        return "university"
    nums = _re.findall(r'\d+', g)
    if nums:
        n = int(nums[0])
        if n <= 5:  return "primary"
        if n <= 8:  return "middle"
        if n <= 12: return "high"
    if any(x in g for x in ["middle", "intermediate"]):  return "middle"
    if any(x in g for x in ["high", "secondary", "gcse", "igcse", "a-level", "ib"]):
        return "high"
    return "unknown"

def _is_young_learner(grade: str) -> bool:
    return _grade_band(grade) == "primary"


# ── Grade-level calibration (vocabulary + complexity + conceptual depth) ────────
def _grade_calibration(grade: str) -> str:
    band = _grade_band(grade)

    if band == "primary":
        return """Age 6-11. CRITICAL RULES — these OVERRIDE ALL TONE RULES for vocabulary AND content depth:

VOCABULARY:
- Maximum 10 words per bullet. Count every word.
- BANNED WORDS: quantitative, analytical, critical thinking, data analysis, volume, cross-cultural,
  representations, methodology, differentiated, trajectory, algorithm, hypothesis, correlation,
  socioeconomic, discourse, paradigm, estimation (use "guess first"), abstract (use a concrete object).
- ONE new term per slide maximum. Define it immediately in the same bullet.
- BANNED FILLER PHRASES — these add zero value and are forbidden:
    ✗ "It is a fun and interactive way to learn"
    ✗ "It is a real-life application of"
    ✗ "can help us understand the concept of"
    ✗ "It is a visual way to represent"
  Replace every filler phrase with a SPECIFIC FACT, NUMBER, or NAMED EXAMPLE.

MANDATORY NUMBER RULE — NON-NEGOTIABLE:
- Every bullet MUST contain at least one real number or quantity.
- WRONG: "We can use cookies to learn about groups."
- WRONG: "Arrays can help us understand multiplication."
- RIGHT: "3 rows of 4 cookies = 12 cookies in total."
- RIGHT: "Skip count by 2s: 2, 4, 6, 8 — that is the 2 times table."
- RIGHT: "Put 5 apples in each of 3 bags — you have 15 apples."
- A bullet with no number in it has failed. Rewrite it.

CONTENT DEPTH:
- Cover only foundational concepts the curriculum introduces at this age.
- EVERY concept must be shown with a physical, touchable example WITH ACTUAL NUMBERS.
- Frame everything as a mini-story: "Mia has 3 bags. Each bag has 4 sweets. How many sweets?"
- Slide themes must stay concrete: skip counting, equal groups, arrays, real-life spotting.
  NOT word problems involving unknowns, NOT algebraic thinking, NOT abstract properties.

ACTIVITIES: Speaker notes must suggest a specific hands-on activity with actual numbers."""

    if band == "middle":
        return """Age 11-14. Content depth and vocabulary rules:

CONTENT DEPTH:
- Build on primary foundations — students know basic facts; now develop UNDERSTANDING and PROCEDURE.
- Move from concrete to semi-abstract: use diagrams, tables, and worked examples before pure symbols.
- Introduce 2-3 subject-specific terms per slide; define each one in plain language in context.
- Slide themes should cover: procedures (how to do it), common errors, word problems, connections
  between topics, and one real-world application students encounter outside school.
- Misconceptions are common at this age — dedicate at least one slide to naming and correcting the
  single biggest mistake students make on this topic.

LANGUAGE: Short, punchy explanations. No jargon without definition. Analogies to everyday life (sports,
games, social media, food). Students can handle "if…then" reasoning but need examples first."""

    if band == "high":
        return """Age 14-18. Content depth and vocabulary rules:

CONTENT DEPTH:
- Students have foundational knowledge — go DEEPER, not broader.
- Each slide should advance understanding: include proofs, derivations, case studies, or exam-style
  analysis. Not just "what" but "why it works" and "when it breaks down."
- Slide themes should span: theoretical underpinning, worked examples at exam level, common
  high-mark errors, connections to other topics in the curriculum, and one real-world or research link.
- Use precise curriculum terminology correctly (e.g., for GCSE/IB/A-Level as appropriate).
- Challenge assumptions: present a scenario where intuition fails and rigour wins.
- Speaker notes: include a higher-order thinking question suitable for exam-preparation discussion."""

    if band == "university":
        return """University / postgraduate level. Content depth and vocabulary rules:

CONTENT DEPTH:
- Assume full discipline literacy. Do not define basic terms — use them correctly.
- Each slide must engage with genuine complexity, nuance, or debate in the field.
- Slide themes should include: theoretical frameworks, seminal research or thinkers, ongoing debates,
  methodological considerations, real-world application at a professional or research level,
  limitations of current knowledge, and connections to adjacent fields.
- Speaker notes may reference further reading, landmark papers, or open research questions."""

    return """Calibrate both language AND content depth precisely to the stated grade level.
The slide themes themselves — not just the wording — must reflect what students at this
exact grade are expected to know and learn. Do not teach Grade 12 content to Grade 6 students
or Grade 3 content to Grade 10 students."""


# ── Grade-appropriate angle banks ──────────────────────────────────────────────
_ANGLES = {
    "primary": """
Angle bank for PRIMARY (Grades 1-5) — use ONLY these; all others are age-inappropriate.

⚠️  CATEGORY DIVERSITY RULE: Blocks, arrays, drawing, and hands-on activities are ALL
the same category ("visual/physical representation"). You may use AT MOST ONE slide from
this category. The remaining slides must come from DIFFERENT categories below.

Categories and angles:
  [VISUAL/PHYSICAL — max 1 slide total from this group]:
  → Real objects with numbers: "3 bags × 4 apples = 12 apples" using cookies, blocks, fingers
  → Drawing arrays: dot arrays, rows of stickers, number lines — always with actual numbers

  [PATTERN & COUNTING — 1 slide]:
  → Skip counting with a specific times table: count by 3s to 30, by 5s to 50 — show the pattern

  [STORY / REAL LIFE — 1 slide]:
  → A mini word-story with a child character: Mia, Jake, or an animal solves a real problem
  → Real-life spotting with numbers: egg carton (2×6=12), chocolate bar (4×5=20), seats in rows

  [COMMON CONFUSION — 1 slide]:
  → The one mistake children always make on this topic, corrected with a specific numbered example

  [AHA MOMENT / SURPRISE — 1 slide]:
  → The single most surprising or delightful fact for this age — must include a number

  [GAME / ACTIVITY — 1 slide]:
  → A specific game or activity the class will play, described with actual numbers involved""",

    "middle": """
Angle bank for MIDDLE SCHOOL (Grades 6-8):
  → The core procedure: step-by-step with a worked example and the "why" behind each step
  → The biggest misconception: name it, show why it happens, correct it with a counter-example
  → Visual model: graph, diagram, table, or number line that makes the abstract visible
  → Real-world application students encounter this week (shopping, sport stats, cooking, maps)
  → Connection to what they already know: how this extends a concept from primary school
  → Word problem walkthrough: a realistic scenario solved step-by-step
  → Common exam/test error and how to avoid it
  → "What if…" extension: one intriguing question that leads toward the next topic
  → Historical or "who invented this?" hook — brief, interesting, not a biography slide
  → Pattern or shortcut: an elegant rule that makes calculation faster""",

    "high": """
Angle bank for HIGH SCHOOL (Grades 9-12):
  → Theoretical foundation: the proof, derivation, or rigorous definition behind the concept
  → Worked example at exam level: show method, mark scheme thinking, common mark-losing errors
  → Conceptual pitfall: where intuition fails — a case where the naive approach gives the wrong answer
  → Connection across the curriculum: how this topic links to another subject or module
  → Real-world or research application at a sophisticated level (engineering, medicine, economics, law)
  → Historical development: how the idea evolved and who the key figures were (brief, purposeful)
  → The edge case or exception: when the rule breaks down and what that reveals
  → Exam strategy: how to approach unseen questions on this topic under time pressure
  → Deeper "why": the elegant insight that unifies several facts into one mental model
  → Ethical or societal dimension (where relevant to the subject)""",

    "university": """
Angle bank for UNIVERSITY / POSTGRADUATE:
  → Foundational theory or framework: the formal model underpinning the topic
  → Seminal paper or thinker: who shaped this field and what they actually argued (not just their name)
  → Current state of debate: what scholars disagree on and why it matters
  → Methodological considerations: how we know what we know — and the limits of that knowledge
  → Real-world or professional application at an expert level
  → Cross-disciplinary connection: how another field challenges or enriches this one
  → Critique of the dominant view: a well-supported counterargument
  → Empirical evidence: what the data actually shows (with appropriate caveats)
  → Open research question: what is genuinely unknown and how it might be investigated
  → Ethical or policy dimension: implications for practice, regulation, or society""",

    "unknown": """
Angle bank (use what fits — do not reuse this list verbatim):
  → The core mechanism or foundational concept
  → The biggest misconception — and why it persists
  → A real-world application students encounter in daily life
  → Historical origin or how we got here
  → A worked example or case study
  → The human cost or benefit (a real story)
  → The data: what the numbers actually show
  → The ethical debate
  → What effective solutions or approaches look like (ONE slide only)
  → The future trajectory""",
}


# ── Tone rules ─────────────────────────────────────────────────────────────────
_TONE_RULES = {
    "Formal": """
TONE = FORMAL. Every word must meet this standard:
- Academic register throughout. Precise discipline-specific terminology used correctly.
- No contractions. Full sentences in bullets. End with periods.
- Titles: A specific declarative CLAIM — not a label. No questions, no exclamations, no colons.
- Subtitle: A precise statement of scope and significance (1 sentence).
- Speaker notes: Reference evidence, methodology, or scholarly context. Sound like a confident expert.
- WRONG: "Plants are really cool because they make food from sunlight!"
- RIGHT: "Photosynthesis drives the global carbon cycle, converting 120 billion tonnes of CO₂ annually into organic matter."
""",
    "Fun": """
TONE = FUN. Every word must meet this standard:
- Conversational, enthusiastic, direct address ("you", "imagine", "did you know").
- Open each slide title with a surprising question, bold claim, or provocative hook. No generic titles.
- Each bullet MUST start with an emoji that relates to the content — not decoration.
- CROSS-SLIDE EMOJI RULE: No emoji may appear more than once in the ENTIRE presentation. You have 4 bullets × ~8 content slides = 32+ bullets. Plan 32 unique emojis before writing slide 2.
- Use analogies: compare new concepts to things students know (phones, games, social media, food).
- Include one "Did you know?" or "Plot twist:" fact per slide that genuinely surprises.
- SENSITIVE TOPICS: For any topic involving human suffering, mental health, addiction, poverty, disability, religion, discrimination, or political controversy — be engaging but NEVER flippant or trivialising. Facts and human stories only. No jokes, no pop-culture mockery.
- Speaker notes: Suggest a quick class interaction — show of hands, 30-second discussion, or prediction.
- WRONG: "Photosynthesis is the process by which plants produce glucose."
- RIGHT: "🌞 Plants are basically solar panels — but they've been running for 3 billion years before Tesla was born."
""",
    "Simple": """
TONE = SIMPLE. Every word must meet this standard:
- Plain English ONLY. If a 10-year-old wouldn't know the word, replace it or define it in brackets.
- HARD MAXIMUM 10 WORDS PER BULLET. Count every word. Rewrite any bullet that exceeds 10 words.
- NO emojis anywhere — not in titles, not in bullets, nowhere.
- One idea per bullet. Active voice. Present tense where possible.
- If a technical term is unavoidable, define it in brackets — bracket content counts toward the 10-word limit.
- Titles: 2-4 words. Everyday language. No colons.
- Subtitle: One sentence under 12 words. Something the student can repeat at home tonight.
- Speaker notes: Short and practical. One simple question to ask the class.
- SIMPLE DOES NOT MEAN VAGUE. Every bullet must still contain a SPECIFIC FACT or NAMED EXAMPLE in plain language.
  WRONG (vague, 4 words): "Online stress is real."
  WRONG (too long, 12 words): "Using social media for more than two hours affects your sleep badly."
  RIGHT (specific, 7 words): "Teens check their phones 96 times daily."
  RIGHT (specific, 8 words): "Two hours of screen time hurts sleep."
- WORD COUNT EXAMPLES:
  PASS: "Plants make food using sunlight." (6 words)
  PASS: "The Great Depression left millions jobless [without work]." (8 words — bracket counts)
  FAIL: "The global economic crisis of the 1930s led to high unemployment." (12 words — rewrite)
""",
}


def _grade_curriculum_note(grade: str, topic: str, subject: str) -> str:
    """
    Tells the AI to use its curriculum knowledge for the EXACT grade,
    not just the grade band. Includes a same-topic cross-grade example
    so the AI understands the expected depth difference.
    """
    band = _grade_band(grade)

    # Cross-grade examples that make the depth difference concrete
    examples = {
        "primary": f"""
EXACT GRADE MATTERS — Grade 1 and Grade 5 are both primary, but their curricula are worlds apart:
  • Grade 1 Multiplication: equal groups of objects, skip counting by 2s and 5s, arrays up to 5×5.
  • Grade 3 Multiplication: full times tables 1-10, repeated addition, simple word problems.
  • Grade 5 Multiplication: multi-digit numbers, multiplying fractions and decimals, area models.

You are writing for {grade}. Use your knowledge of what is ACTUALLY on the {grade} curriculum
for {subject}. Do not teach Grade 1 content to Grade 5, or Grade 5 content to Grade 1.""",

        "middle": f"""
EXACT GRADE MATTERS — Grade 6 and Grade 8 are both middle school, but their curricula differ significantly:
  • Grade 6 Maths: ratios, percentages, negative numbers, area of basic shapes.
  • Grade 7 Maths: algebraic expressions, linear equations, proportional reasoning.
  • Grade 8 Maths: simultaneous equations, Pythagoras, quadratics introduction, transformations.

You are writing for {grade}. Use your knowledge of what is ACTUALLY on the {grade} curriculum
for {subject}. Do not write generic middle-school content — target exactly {grade}.""",

        "high": f"""
EXACT GRADE MATTERS — Grade 9 and Grade 12 are both high school, but their curricula differ enormously:
  • Grade 9 Maths: linear functions, basic trigonometry, quadratic equations, coordinate geometry.
  • Grade 10 Maths: quadratic functions, circle geometry, simultaneous equations, statistics.
  • Grade 11 Maths: polynomials, exponential functions, probability, sequences and series.
  • Grade 12 Maths: calculus (differentiation & integration), complex numbers, matrices, proofs.

You are writing for {grade}. Use your knowledge of what is ACTUALLY on the {grade} curriculum
for {subject}. Do not blend grade levels — every slide theme must be squarely in {grade} territory.""",

        "university": f"""
EXACT LEVEL MATTERS — a first-year undergraduate and a PhD student cover entirely different material
even on the same topic. You are writing for {grade}. Target the precise level and depth expected
at that stage: foundational courses if Year 1, specialised theory and research engagement if postgraduate.""",

        "unknown": f"""
You are writing for {grade}. Use your knowledge of what is ACTUALLY taught at {grade} level
in standard curricula worldwide for {subject}. Calibrate the sub-topics, depth, and terminology
to precisely match what a student at {grade} would be expected to know and learn.""",
    }

    return f"""
━━━ EXACT GRADE CURRICULUM TARGETING ━━━
{examples.get(band, examples["unknown"])}

SAME TOPIC, DIFFERENT GRADES — to make this concrete for "{topic}" in {subject}:
Think about how a textbook written for {grade} would cover "{topic}". What chapter headings
would it use? What prior knowledge does it assume? What comes next in the sequence?
Those chapter headings are your slide themes. A textbook for a different grade would have
DIFFERENT chapter headings — so should your slide_plan.
"""


def _build_user_prompt(topic, grade, subject, num_slides, tone):
    tone_rules      = _TONE_RULES.get(tone, _TONE_RULES["Formal"])
    subject_tip     = _subject_strategy(subject)
    grade_tip       = _grade_calibration(grade)
    n_content       = num_slides - 2
    band            = _grade_band(grade)
    angle_bank      = _ANGLES.get(band, _ANGLES["unknown"])
    young           = band == "primary"
    curriculum_note = _grade_curriculum_note(grade, topic, subject)
    grade_override  = """
⚠️  GRADE OVERRIDE — READ BEFORE WRITING A SINGLE WORD:
This presentation is for young learners. Grade calibration OVERRIDES tone rules for both
vocabulary AND content depth. "Formal" means structured and clear — not academic.
A 6-year-old cannot process "quantitative reasoning" or "data analysis".
Every bullet must be explainable by a parent at bedtime using only everyday words.
Slide THEMES must be introductory and concrete — not topics you'd teach a 16-year-old.
""" if young else ""

    return f"""Create an ELITE-QUALITY {num_slides}-slide presentation on the following:

Topic:        {topic}
Subject:      {subject}
Grade/Level:  {grade}
Tone:         {tone}

━━━ SUBJECT PEDAGOGY ━━━
{subject_tip}
{curriculum_note}
{grade_override}━━━ GRADE CALIBRATION ━━━
{grade_tip}

━━━ TONE REQUIREMENT ━━━
{tone_rules}

━━━ STEP 1 — COMMIT TO YOUR SLIDE PLAN (output this in JSON first) ━━━
Your JSON must include a "slide_plan" array as the FIRST field.
List every content slide (slides 2 to {num_slides - 1}) as a one-line theme description.
This locks you into {n_content} genuinely distinct angles BEFORE you write any bullets.

Rules for your plan:
  ✓ Every slide covers a different dimension — choose from the angle bank below.
  ✗ BANNED PATTERN — "[Institution/Person] Can Help [Solve Problem]":
    If slides 6, 7, 8, and 9 all follow "X can help prevent Y" or "Z plays a role in Y",
    you have failed. Stakeholder solutions is ONE angle, not four slides.
  ✗ No two slides may share the same theme, even with different wording.
  ✗ Every theme in slide_plan must map to a slide with a genuinely DIFFERENT sub-topic.

{angle_bank}

━━━ STEP 2 — BANNED TITLE FORMATS ━━━
These formats are lazy and forbidden in ALL tones and ALL grade levels:

  ✗ "[X] Can Help [Y]"     — THE MOST COMMON FAILURE. Every slide title in the last
                              bad presentation used this. It is BANNED. No exceptions.
      BANNED:  "Blocks Can Help Us Understand Multiplication"
      BANNED:  "Arrays Can Help Us Visualize Multiplication"
      BANNED:  "Songs Can Help Us Learn Times Tables"
      REWRITE: "3 Rows of 4 Blocks = 12 — Every Time, Without Counting"
      REWRITE: "A 3×4 Array of Dots Shows Why Multiplication Is Just Fast Counting"
      REWRITE: "Skip Counting by 5s Gets You to 100 in Just 20 Steps"

  ✗ "The X of Y"           e.g., "The History of Cricket"
  ✗ "X and Y"              e.g., "Cricket and Technology"
  ✗ "The Role of X"        e.g., "The Role of Women"
  ✗ "X: A Y Perspective"   e.g., "Cricket: A Historical View"
  ✗ "What is X?"
  ✗ "X Is Important"
  ✗ "Understanding X"
  ✗ "Learning About X"

Every title must state a SPECIFIC, SURPRISING FACT or a CONCRETE CLAIM:
  ✓ (primary)    "3 Groups of 4 Is Always 12 — Even If You Rearrange the Groups"
  ✓ (primary)    "Your Fingers Are a Times-Table Machine — Here Is How"
  ✓ (secondary)  "Your Brain Cannot Tell the Difference Between a Like and a Drug Hit"
  ✓ (secondary)  "Facebook's Own Research Showed Instagram Harmed Teen Girls — and They Hid It"

TITLE SELF-CHECK: After writing each title, ask: "Does this title contain a specific
number, fact, or surprising claim?" If NO — rewrite it before moving to the bullets.

━━━ STEP 3 — SLIDE-BY-SLIDE RULES ━━━
Slide 1 — slide_type "cover":
  • Title: A compelling hook that makes the teacher WANT to show this slide.
  • Subtitle: One sentence — the single biggest idea of the entire topic.
  • No bullets field.

Slides 2 to {num_slides - 1} — slide_type "content":
  • Title: A specific, insightful CLAIM (see banned formats above).
  • Exactly 4 bullets. Each bullet must:
      – Deliver a specific insight, real number, or named example — NOT a vague statement
      – Connect to the real world or the student's life
      – Pass the tone test: every single word matches the required tone
  • speaker_notes — exactly 4 sentences:
      1. The deeper "so what?" — why this slide matters beyond the obvious
      2. The most common misconception students have here, and how to correct it
      3. A question to pose to the class
      4. A real-world connection or human story to share aloud

Slide {num_slides} — slide_type "summary":
  • Title: The SINGLE biggest insight of the whole presentation. Not "Key Takeaways". Not a colon title.
  • 4 bullets: Each is a standalone insight a student could explain to a friend without the slides.

━━━ FINAL QUALITY CHECKLIST (every bullet, every slide) ━━━
[ ] Could this bullet appear in a generic Wikipedia summary? → REWRITE it.
[ ] Does it contain a specific fact, number, or named example? → It must.
[ ] Does every word match the required tone ({tone})? → Test each word.
[ ] Simple: is every bullet 10 words or fewer? → COUNT every word.
[ ] Fun: does every emoji appear only ONCE across the whole presentation? → Check your list.
[ ] Is every named source, event, statistic, and person real? → If unsure, drop the citation, keep the fact.
[ ] Does each slide cover a different angle than every other slide? → Check against slide_plan.
[ ] Do any 4 consecutive slides follow "[X] Can Help [Y]"? → If yes, rewrite at least 3 of them.
[ ] Young learners: does ANY bullet contain a banned abstract word (quantitative, analytical, cross-cultural, data analysis, etc.)? → Replace with a concrete object or action.
[ ] Young learners: does every bullet contain at least one real number or quantity? → If not, rewrite it.
[ ] Young learners: does any bullet contain a banned filler phrase ("can help us understand", "it is a fun way", "it is a real-life application")? → Replace with a specific numbered example.
[ ] Does any slide title contain "[X] Can Help [Y]"? → This is the most common failure. Rewrite every such title as a specific claim with a number or fact.

Return ONLY this JSON (no markdown, no text outside the braces):
{{
  "slide_plan": [
    "Slide 2: <one-line theme>",
    "Slide 3: <one-line theme>",
    "Slide {num_slides - 1}: <one-line theme>"
  ],
  "title": "...",
  "subject": "{subject}",
  "grade": "{grade}",
  "tone": "{tone}",
  "slides": [
    {{"slide_number": 1, "slide_type": "cover", "title": "...", "subtitle": "...", "speaker_notes": "..."}},
    {{"slide_number": 2, "slide_type": "content", "title": "...", "bullets": ["...", "...", "...", "..."], "speaker_notes": "..."}},
    {{"slide_number": {num_slides}, "slide_type": "summary", "title": "...", "bullets": ["...", "...", "...", "..."], "speaker_notes": "..."}}
  ]
}}"""


def generate_presentation(topic, grade, subject, num_slides, tone, api_key,
                          unsplash_key=""):
    raw  = call_groq(
        system=SYSTEM_PROMPT,
        user=_build_user_prompt(topic, grade, subject, num_slides, tone),
        temperature=0.82,
        api_key=api_key,
    )
    data = parse_json_response(raw)
    data.setdefault("tone", tone)

    img_bytes = fetch_cover_image(f"{subject} {topic}", unsplash_key)
    return create_presentation(data, img_bytes=img_bytes)
