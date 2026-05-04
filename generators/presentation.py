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
        # Detect specific grade number for fine-grained rules
        nums = _re.findall(r'\d+', grade.lower())
        grade_num = int(nums[0]) if nums else 3  # default to Grade 3 if unclear

        if grade_num <= 2:
            symbol_rule = """SYMBOL RULE FOR GRADE 1-2 — CRITICAL:
- Do NOT use the × symbol. Grade 1-2 students have not learned it yet.
- Use "groups of" language instead:
    WRONG: "3 × 4 = 12"
    RIGHT: "3 groups of 4 apples = 12 apples"
    RIGHT: "4 bags with 2 cookies each = 8 cookies"
- Do NOT use the word "columns". Use "rows" and "groups" only.
- Do NOT use the word "array" without defining it as "objects in equal rows".
- Maximum number size: stay within 5 groups of 5 = 25. No bigger."""
        elif grade_num <= 3:
            symbol_rule = """SYMBOL RULE FOR GRADE 3:
- The × symbol is now introduced — use it but always show the "groups of" meaning alongside it.
    RIGHT: "3 × 4 means 3 groups of 4 — that is 12."
- Maximum number size: times tables up to 10×10 = 100."""
        else:
            symbol_rule = """SYMBOL RULE FOR GRADE 4-5:
- Use × freely. Students know multiplication notation.
- Include decimals and fractions in multiplication by Grade 5.
- Maximum number size: multi-digit multiplication (e.g., 23 × 4 = 92)."""

        return f"""Age 6-11. CRITICAL RULES — these OVERRIDE ALL TONE RULES for vocabulary AND content depth:

{symbol_rule}

VOCABULARY:
- Maximum 10 words per bullet. Count every word.
- BANNED WORDS: quantitative, analytical, critical thinking, data analysis, volume, cross-cultural,
  representations, methodology, differentiated, trajectory, algorithm, hypothesis, correlation,
  socioeconomic, discourse, paradigm. Replace with a concrete object or action.
- ONE new term per slide maximum. Define it immediately in the same bullet.
- BANNED FILLER PHRASES — these add zero value and are forbidden in every bullet:
    ✗ "It is a fun and interactive way to learn"
    ✗ "It is a real-life application of"
    ✗ "can help us understand the concept of"
    ✗ "It is a visual way to represent"
    ✗ "helps us develop a deeper understanding"
    ✗ Any sentence that does not contain a number or named object.

MANDATORY NUMBER RULE — NON-NEGOTIABLE. Applies to EVERY slide including activity and mistake slides:
- Every single bullet MUST contain at least one real number or quantity.
- This applies to the Common Mistake slide: show the mistake WITH numbers, then correct it WITH numbers.
    WRONG: "Some children forget to multiply the rows by the columns."
    RIGHT: "Some children count 1,2,3...12 one by one instead of saying 3 groups of 4 = 12."
- This applies to the Activity slide: name the specific numbers used in the activity.
    WRONG: "Use blocks to build arrays and practice multiplication."
    RIGHT: "Build 3 rows of 4 blocks — count them to confirm you have 12 blocks every time."
- This applies to the Summary slide: each bullet must state a specific numbered fact, not a vague claim.
    WRONG: "Multiplication is a fundamental concept in mathematics."
    RIGHT: "3 groups of 4 always equals 12 — you never need to count one by one again."

CONTENT DEPTH:
- Cover only foundational concepts the curriculum introduces at this exact grade.
- Frame everything as a mini-story with a named child: "Mia has 3 bags. Each bag has 4 sweets."
- Slide themes must stay concrete. Use the angle bank — each slide must come from a DIFFERENT category.

NO-REPEAT RULE: If two slides both involve arrays, real objects, or real-life scenarios,
you have repeated the same angle. Merge them into one slide and use a different angle for the other."""

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
  • Grade 1: "groups of" language only (NO × symbol), equal groups up to 5 groups of 5,
             skip counting by 2s and 5s, simple real-life objects (cookies, fingers, toy cars).
  • Grade 2: introduction of × symbol alongside "groups of", times tables for 2, 5, 10,
             arrays up to 5×5, simple word problems with small numbers.
  • Grade 3: full times tables 1-10, repeated addition, word problems, area as rows × columns.
  • Grade 4: multi-digit multiplication, mental strategies, estimation, word problems.
  • Grade 5: multiplying fractions and decimals, area models, multi-step word problems.

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


def _build_user_prompt(topic, grade, subject, num_slides, tone, board="CBSE"):
    tone_rules      = _TONE_RULES.get(tone, _TONE_RULES["Formal"])
    subject_tip     = _subject_strategy(subject)
    grade_tip       = _grade_calibration(grade)
    n_content       = num_slides - 2
    band            = _grade_band(grade)
    angle_bank      = _ANGLES.get(band, _ANGLES["unknown"])
    young           = band == "primary"
    curriculum_note = _grade_curriculum_note(grade, topic, subject)
    grade_override  = """
GRADE OVERRIDE: This is for young learners. Calibration OVERRIDES tone for vocabulary and depth.
No abstract words. Every bullet needs a real number. No filler phrases.
""" if young else ""

    return f"""Create a {num_slides}-slide presentation:

Topic: {topic} | Subject: {subject} | Grade: {grade} | Board: {board} | Tone: {tone}

GRADE CALIBRATION:
{grade_tip}
{grade_override}
BOARD ALIGNMENT: Align all content, examples, terminology and exam-style depth to the {board} curriculum.

SUBJECT STRATEGY:
{subject_tip}
{curriculum_note}
TONE:
{tone_rules}

ANGLE BANK - pick {n_content} DIFFERENT angles for content slides:
{angle_bank}

TITLE RULES - every title must be a specific CLAIM or FACT. BANNED formats:
"[X] Can Help [Y]", "The X of Y", "X and Y", "What is X?", "Understanding X", "X Is Important"
GOOD examples: "3 Groups of 4 Is Always 12" / "Your Brain Reads Emojis Like a Human Face"

SLIDE RULES:
- Slide 1 (cover): title = compelling hook, subtitle = biggest idea, no bullets.
- Slides 2 to {num_slides-1} (content): title = specific claim, exactly 4 bullets each with a real number or named example, speaker_notes = 2 sentences (1 class question + 1 real-world link).
- Slide {num_slides} (summary): title = single biggest insight (not "Key Takeaways"), 4 standalone bullets.

Return JSON only:
{{
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


def generate_presentation(topic, grade, subject, num_slides, tone, board="CBSE",
                          api_key="", unsplash_key="", on_retry=None):
    raw  = call_groq(
        system=SYSTEM_PROMPT,
        user=_build_user_prompt(topic, grade, subject, num_slides, tone, board),
        temperature=0.65,
        api_key=api_key,
        on_retry=on_retry,
    )
    data = parse_json_response(raw)
    data.setdefault("tone", tone)

    img_bytes = fetch_cover_image(f"{subject} {topic}", unsplash_key)
    return create_presentation(data, img_bytes=img_bytes)
