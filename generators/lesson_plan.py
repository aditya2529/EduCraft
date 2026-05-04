from utils.groq_client import call_groq, parse_json_response
from utils.export import create_lesson_plan_pdf

# ── System persona ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are Professor James Okafor, a master teacher trainer with 30 years of experience coaching teachers across IB, Cambridge, and national curriculum schools in 12 countries. You hold a PhD in Curriculum Design and have written three textbooks on the 5E Instructional Model and Bloom's Taxonomy.

Your lesson plans are famous for:
1. PRECISION: Every activity has a clear pedagogical purpose — nothing is filler.
2. COGNITIVE PROGRESSION: Each phase builds explicitly on the previous one — no arbitrary jumps.
3. ACTIVE LEARNING: Students are always doing something — not just listening.
4. ASSESSMENT INTEGRATION: You check for understanding continuously, not just at the end.
5. REAL ENGAGEMENT: Activities connect to students' actual lives and current world events.
6. TEACHER CONFIDENCE: Your speaker guidance gives teachers the exact words and moves to make the lesson sing.

Elite standard for activities:
- WEAK: "Discuss photosynthesis in groups"
- ELITE: "Give each group a different ecosystem (rainforest, ocean, desert, arctic). Groups identify HOW photosynthesis works differently in their ecosystem and WHY that matters for life there. Share back with one surprising finding."

Elite standard for teacher actions:
- WEAK: "Explain the concept to students"
- ELITE: "Draw the equation on the board. Ask: 'Which side of this equation are YOU on right now — are you giving off CO2 or absorbing it?' (Both — you breathe out CO2, the plant in the corner absorbs it). Let the contradiction land."

Return ONLY valid JSON. No markdown fences. No text outside the JSON object."""


# ── Subject-specific teaching strategies ──────────────────────────────────────
_TEACHING_STRATEGIES = {
    "science":   "Use Predict-Observe-Explain for every demonstration. Make students form a hypothesis before revealing the answer. Use discrepant events (unexpected outcomes) to create cognitive conflict. Connect to current scientific news.",
    "biology":   "Use case studies of real organisms and ecosystems. Have students draw and label — visual processing deepens retention. Connect cellular/molecular to organism/ecosystem level. Use disease or environmental case studies for relevance.",
    "chemistry": "Always start with the macroscopic phenomenon, then drill to molecular explanation. Use particle models. Safety-conscious hands-on activities where possible. Connect to industrial processes, medicine, or everyday products.",
    "physics":   "Start with a surprising demonstration or thought experiment. Use quantitative reasoning — actual numbers, not just descriptions. Connect to technology students use. Address the gap between intuition and physics reality.",
    "math":      "Use the Problem-first approach: show a real problem BEFORE teaching the method. Multiple representations: numerical, algebraic, graphical, verbal. Error analysis: show common mistakes and explain WHY they happen. Real data wherever possible.",
    "mathematics":"Problem-first approach. Multiple representations. Error analysis activities. Real-world data contexts. Peer explanation ('if you can teach it, you know it').",
    "history":   "Use primary sources — let students be historians, not just history consumers. Teach causation with multiple factors, not single causes. Use the 'so what?' test for every event. Connect to present-day parallels. Avoid the 'inevitable' narrative.",
    "geography": "Use real maps, data, and current news. Case studies from multiple continents — avoid Eurocentrism. Quantify everything possible. Field observation or photo analysis activities.",
    "economics": "Use real market data and news events. Decision-making simulations. Show multiple economic perspectives, not just one school of thought. Connect to personal financial decisions students will face.",
    "english":   "Close reading of SHORT extracts — depth over breadth. Teach annotation as thinking made visible. Always ask HOW, not just WHAT. Student choice in discussion topics where possible. Model good writing by deconstructing mentor texts.",
    "default":   "Use collaborative structures (Think-Pair-Share, Jigsaw, Gallery Walk). Include at least one hands-on or creative activity. Use formative checks every 10-15 minutes. Connect to students' prior knowledge explicitly. Include at least one higher-order thinking task (Bloom's Analyze or above).",
}

def _teaching_strategy(subject: str) -> str:
    key = subject.lower().strip()
    for k, v in _TEACHING_STRATEGIES.items():
        if k in key:
            return v
    return _TEACHING_STRATEGIES["default"]


# ── Activity type bank per 5E phase ───────────────────────────────────────────
_ACTIVITY_TYPES = {
    "Engage":    "Hook activities: surprising demonstration, provocative question, short video clip stimulus, misconception reveal, real-world news hook, personal connection prompt.",
    "Explore":   "Discovery activities: experiment (real or virtual), data analysis, case study investigation, jigsaw reading, sorting/categorising, making observations and recording findings.",
    "Explain":   "Consolidation activities: annotated diagram, concept mapping, guided note-taking, teacher explanation with regular comprehension checks, worked examples with student participation.",
    "Elaborate": "Application activities: problem-solving with new context, creative task (design, write, build), role play or debate, cross-curricular connection, real-world scenario analysis.",
    "Evaluate":  "Assessment activities: exit ticket (2-3 targeted questions), peer teaching, self-assessment against success criteria, quick quiz, reflection journal, class discussion with accountable talk.",
}

def _activity_types_block():
    return "\n".join(f"- {k}: {v}" for k, v in _ACTIVITY_TYPES.items())


def _build_user_prompt(subject, topic, grade, duration, objectives, resources, board="CBSE"):
    strategy = _teaching_strategy(subject)

    objectives_block = (
        f"Teacher-specified objectives:\n{objectives}"
        if objectives.strip()
        else (
            "Design 3-4 learning objectives yourself. Each must:\n"
            "- Use a measurable Bloom's action verb (analyse, evaluate, construct — not 'understand' or 'know')\n"
            "- State what students can DO, not just what they will 'learn about'\n"
            "- Be genuinely achievable in a single lesson of this duration"
        )
    )

    return f"""Design an ELITE-QUALITY {duration}-minute lesson plan.

Subject:    {subject}
Topic:      {topic}
Grade:      {grade}
Resources:  {resources}
Board:      {board}
Duration:   {duration} minutes

━━━ SUBJECT-SPECIFIC TEACHING STRATEGY ━━━
{strategy}

━━━ BOARD ALIGNMENT ━━━
Align all content, examples, activities, and assessment style to the {board} curriculum for {grade}.

━━━ LEARNING OBJECTIVES ━━━
{objectives_block}

━━━ 5E PHASE REQUIREMENTS ━━━
Use EXACTLY these five section names:
1. "Warm-Up (Engage)"
2. "Direct Instruction (Explore)"
3. "Guided Practice (Explain)"
4. "Activity (Elaborate)"
5. "Assessment & Wrap-Up (Evaluate)"

All duration_minutes MUST sum to exactly {duration}. Double-check this.

Activity type guidance for each phase:
{_activity_types_block()}

━━━ ELITE CONTENT STANDARDS ━━━
For EVERY section, apply these standards:

activities[] — each activity must be:
  ✓ Specific enough that a teacher can run it without guessing
  ✓ Student-ACTIVE (students do something, not just listen)
  ✓ Matched to the 5E phase purpose
  ✓ Achievable with the available resources: {resources}
  WEAK: "Discuss the topic in groups"
  ELITE: "Groups receive a set of 6 statements about {topic} — 3 true, 3 false (they don't know which). They discuss and sort them, then reveal answers. Misconceptions surface naturally."

teacher_actions — must be:
  ✓ Written as if coaching a first-year teacher through every move
  ✓ Include exact questions to ask the class (in quotes)
  ✓ Include what to do IF students are confused or silent
  ✓ Reference the specific resources available
  WEAK: "Explain the main concept"
  ELITE: "Write only the KEY TERM on the board — nothing else. Ask: 'What do you already know about this word?' Take 3-4 responses without correcting. Then reveal: 'Here's what scientists actually found...' — the gap between their answer and reality IS the lesson hook."

student_actions — must be:
  ✓ Describe what students are PHYSICALLY doing (writing, drawing, discussing, building)
  ✓ Include a thinking prompt or sentence starter where helpful
  ✓ Be differentiated by ability where relevant

━━━ DIFFERENTIATION STANDARDS ━━━
support[] — for students who struggle:
  - Modify the TASK, not just the amount (e.g., provide a partially completed graphic organiser, not just "do fewer questions")
  - Include a specific scaffold or sentence frame example

extension[] — for students who finish early or excel:
  - Push to higher Bloom's levels (evaluate, create, synthesise)
  - Connect to real-world complexity or current research
  - Avoid "do more of the same" — change the cognitive demand

━━━ MATERIALS ━━━
List only materials ACTUALLY needed for these activities, given resources available: {resources}.
Be specific (e.g., "A4 paper and coloured markers" not just "stationery").

━━━ HOMEWORK ━━━
If homework is appropriate:
  - Make it extend thinking, not repeat classwork
  - Connect to students' real lives outside school
  - Keep it short (15-20 min max for this grade level)
Set to null if the topic or grade level makes homework inappropriate.

Return ONLY this JSON (no markdown, no text outside the braces):
{{
  "lesson_title": "...",
  "subject": "{subject}",
  "grade": "{grade}",
  "duration_minutes": {duration},
  "learning_objectives": ["verb + specific outcome", "..."],
  "materials": ["specific item", "..."],
  "sections": [
    {{
      "name": "Warm-Up (Engage)",
      "duration_minutes": ...,
      "bloom_level": "Remember / Understand",
      "activities": ["specific activity description", "..."],
      "teacher_actions": "detailed step-by-step with exact questions and contingency moves",
      "student_actions": "what students physically do, with thinking prompts"
    }},
    {{
      "name": "Direct Instruction (Explore)",
      "duration_minutes": ...,
      "bloom_level": "Understand / Apply",
      "activities": ["..."],
      "teacher_actions": "...",
      "student_actions": "..."
    }},
    {{
      "name": "Guided Practice (Explain)",
      "duration_minutes": ...,
      "bloom_level": "Apply / Analyze",
      "activities": ["..."],
      "teacher_actions": "...",
      "student_actions": "..."
    }},
    {{
      "name": "Activity (Elaborate)",
      "duration_minutes": ...,
      "bloom_level": "Analyze / Evaluate",
      "activities": ["..."],
      "teacher_actions": "...",
      "student_actions": "..."
    }},
    {{
      "name": "Assessment & Wrap-Up (Evaluate)",
      "duration_minutes": ...,
      "bloom_level": "Evaluate / Create",
      "activities": ["..."],
      "teacher_actions": "...",
      "student_actions": "..."
    }}
  ],
  "differentiation": {{
    "support": ["specific scaffold with example", "..."],
    "extension": ["higher-order challenge", "..."]
  }},
  "homework": "specific task description or null"
}}"""


def generate_lesson_plan(subject, topic, grade, duration, objectives, resources,
                         board="CBSE", api_key="", on_retry=None):
    raw  = call_groq(
        system=SYSTEM_PROMPT,
        user=_build_user_prompt(subject, topic, grade, duration, objectives, resources, board),
        temperature=0.4,
        api_key=api_key,
        on_retry=on_retry,
    )
    data = parse_json_response(raw)
    return create_lesson_plan_pdf(data)
