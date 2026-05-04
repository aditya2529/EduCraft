from utils.groq_client import call_groq, parse_json_response
from utils.export import create_question_paper_pdfs

# ── System persona ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are Dr. Rajan Mehta, a senior examiner with 28 years of experience setting question papers for CBSE, ICSE, State Board, and IB examinations across India. You have chaired the CBSE Science paper-setting committee and trained 500+ teachers in Bloom's Taxonomy-aligned assessment.

Your question papers are known for:
1. FACTUAL ACCURACY — Every question, fact, and answer is verifiably correct. No invented data.
2. BLOOM'S ALIGNMENT — Questions span the taxonomy: MCQs test Remember/Understand, Short answers test Apply/Analyse, Long answers test Evaluate/Create.
3. ZERO REPETITION — No two questions test the same concept or skill.
4. AUTHENTIC CONTEXT — Questions use real-world scenarios, data, and named examples — not abstract "given that X, find Y" templates.
5. CLEAR MARKING — Every mark in the marking scheme corresponds to a specific, verifiable point.
6. CURRICULUM PRECISION — Vocabulary, depth, and scope match exactly what the board prescribes for that grade.

FACTUAL ACCURACY RULES — NON-NEGOTIABLE:
- Every named fact, formula, statistic, person, or event must be real and verifiable.
- If unsure about a fact, use a simpler, certain fact instead.
- MCQ distractors must be plausible but clearly wrong — not ambiguous or trick questions.
- Model answers must be accurate enough for a teacher to read directly to the class.

Return ONLY valid JSON. No markdown. No text outside the JSON object."""


# ── Bloom's level distribution by difficulty ──────────────────────────────────
_BLOOM_DISTRIBUTION = {
    "Easy": {
        "mcq":   "Remember (40%) and Understand (60%)",
        "short": "Understand (50%) and Apply (50%)",
        "long":  "Apply (60%) and Analyse (40%)",
    },
    "Balanced": {
        "mcq":   "Remember (30%), Understand (40%), Apply (30%)",
        "short": "Apply (40%), Analyse (40%), Evaluate (20%)",
        "long":  "Analyse (40%), Evaluate (40%), Create (20%)",
    },
    "Hard": {
        "mcq":   "Understand (30%), Apply (40%), Analyse (30%)",
        "short": "Analyse (40%), Evaluate (40%), Create (20%)",
        "long":  "Evaluate (40%), Create (60%)",
    },
}

# ── Board-specific instructions ────────────────────────────────────────────────
_BOARD_INSTRUCTIONS = {
    "CBSE": """CBSE-specific rules:
- Follow the latest CBSE pattern: Section A (MCQ 1 mark), Section B (short 2-3 marks), Section C (long 5 marks).
- Case-based questions in Section B for Class 9-12: provide a short passage/data, then 2-3 sub-questions.
- Use NCERT textbook vocabulary and examples where possible.
- General instructions must include: 'All questions are compulsory', 'Draw neat diagrams wherever required'.
- Competency-based questions: at least 30% of questions must test application or higher.""",

    "ICSE": """ICSE-specific rules:
- ICSE papers have more descriptive questions and fewer MCQs vs CBSE.
- Section A is compulsory (shorter questions). Section B has choice (attempt any N of M).
- Vocabulary tends to be more formal and literary even in science subjects.
- Include 'attempt any four' style choice in long-answer section.
- Emphasis on diagram-based and definition questions in sciences.""",

    "State Board": """State Board rules:
- Keep language simple and direct — State Board exams prioritise recall and basic application.
- More 1-mark and 2-mark questions; fewer lengthy analytical questions.
- Use local and regional examples alongside national/global ones.
- Avoid overly complex case studies — straightforward application is sufficient.""",

    "IB": """IB-specific rules:
- IB questions emphasise inquiry, critical thinking, and real-world application.
- Use data-based questions with graphs, tables, or experimental results.
- Command terms are critical: 'Outline', 'Explain', 'Evaluate', 'Discuss', 'Compare'.
- Include a data-response question in the long section.
- Marking criteria: Content + Accuracy + Analysis — not just recall.""",

    "Other": """General curriculum rules:
- Balance recall and application questions appropriately for the grade level.
- Use clear, unambiguous language.
- Provide both questions-only student paper and model answers for teacher.""",
}


def _board_instruction(board: str) -> str:
    return _BOARD_INSTRUCTIONS.get(board, _BOARD_INSTRUCTIONS["Other"])


def _build_prompt(subject, topic, grade, board, total_marks,
                  mcq_count, short_count, long_count,
                  mcq_marks, short_marks, long_marks, difficulty):

    bloom = _BLOOM_DISTRIBUTION.get(difficulty, _BLOOM_DISTRIBUTION["Balanced"])
    board_rules = _board_instruction(board)

    # Calculate section marks
    mcq_total   = mcq_count * mcq_marks
    short_total = short_count * short_marks
    long_total  = long_count * long_marks

    sections_block = ""
    q_num = 1

    if mcq_count > 0:
        sections_block += f"""
Section A — Multiple Choice Questions ({mcq_count} x {mcq_marks} mark = {mcq_total} marks)
  Bloom's distribution: {bloom['mcq']}
  Each question must have exactly 4 options (A, B, C, D). One correct answer.
  Distractors must be plausible but unambiguously wrong.
  Question numbers: {q_num} to {q_num + mcq_count - 1}"""
        q_num += mcq_count

    if short_count > 0:
        sections_block += f"""

Section B — Short Answer Questions ({short_count} x {short_marks} marks = {short_total} marks)
  Bloom's distribution: {bloom['short']}
  Each answer: 3-6 sentences. Bullet points acceptable.
  Model answer must cover every mark point explicitly.
  Question numbers: {q_num} to {q_num + short_count - 1}"""
        q_num += short_count

    if long_count > 0:
        sections_block += f"""

Section C — Long Answer Questions ({long_count} x {long_marks} marks = {long_total} marks)
  Bloom's distribution: {bloom['long']}
  Each answer: structured, 150-250 words. May include diagrams or data interpretation.
  Marking scheme: list each mark point separately (e.g. '2 marks for explanation, 2 marks for example, 1 mark for conclusion').
  Question numbers: {q_num} to {q_num + long_count - 1}"""

    return f"""Create a complete {board} {grade} {subject} question paper on: {topic}

Total marks: {total_marks} | Difficulty: {difficulty}

{board_rules}

SECTION BREAKDOWN:
{sections_block}

QUALITY RULES:
- Cover different sub-topics across questions — no two questions test the same concept.
- Use real data, named examples, and authentic contexts wherever possible.
- Every MCQ distractor must be plausible — no obviously silly wrong options.
- Model answers must be accurate enough to read directly to students.
- Bloom's level tag on every question (e.g. "Remember", "Apply", "Analyse").

GENERAL INSTRUCTIONS FOR PAPER HEADER:
Write 4-5 general instructions appropriate for {board} format (e.g. time allowed, all questions compulsory, etc.)

Return this exact JSON structure:
{{
  "paper_title": "{subject} — {topic}",
  "subject": "{subject}",
  "grade": "{grade}",
  "board": "{board}",
  "topic": "{topic}",
  "total_marks": {total_marks},
  "difficulty": "{difficulty}",
  "duration_minutes": {max(30, total_marks)},
  "general_instructions": ["instruction 1", "instruction 2", "instruction 3", "instruction 4"],
  "sections": [
    {{
      "section_name": "Section A",
      "section_type": "mcq",
      "marks_per_question": {mcq_marks},
      "total_marks": {mcq_total},
      "questions": [
        {{
          "number": 1,
          "bloom_level": "Remember",
          "question": "Question text here?",
          "options": ["A. option1", "B. option2", "C. option3", "D. option4"],
          "correct_answer": "A",
          "answer_explanation": "Brief explanation of why A is correct and others are wrong."
        }}
      ]
    }},
    {{
      "section_name": "Section B",
      "section_type": "short",
      "marks_per_question": {short_marks},
      "total_marks": {short_total},
      "questions": [
        {{
          "number": {mcq_count + 1},
          "bloom_level": "Apply",
          "question": "Question text here.",
          "model_answer": "Complete model answer here.",
          "marking_scheme": ["1 mark for ...", "1 mark for ..."]
        }}
      ]
    }},
    {{
      "section_name": "Section C",
      "section_type": "long",
      "marks_per_question": {long_marks},
      "total_marks": {long_total},
      "questions": [
        {{
          "number": {mcq_count + short_count + 1},
          "bloom_level": "Analyse",
          "question": "Question text here.",
          "model_answer": "Complete model answer here (150-250 words).",
          "marking_scheme": ["2 marks for ...", "2 marks for ...", "1 mark for ..."]
        }}
      ]
    }}
  ]
}}

Generate ALL {mcq_count} MCQs, ALL {short_count} short answer questions, and ALL {long_count} long answer questions.
Do not use placeholder text — write real questions and real answers."""


def generate_question_paper(subject, topic, grade, board, total_marks,
                             mcq_count, short_count, long_count,
                             mcq_marks, short_marks, long_marks,
                             difficulty, api_key, on_retry=None):
    raw = call_groq(
        system=SYSTEM_PROMPT,
        user=_build_prompt(subject, topic, grade, board, total_marks,
                           mcq_count, short_count, long_count,
                           mcq_marks, short_marks, long_marks, difficulty),
        temperature=0.35,
        api_key=api_key,
        on_retry=on_retry,
    )
    data = parse_json_response(raw)

    # Validate section counts
    for section in data.get("sections", []):
        stype = section.get("section_type", "")
        expected = {"mcq": mcq_count, "short": short_count, "long": long_count}.get(stype, 0)
        actual = len(section.get("questions", []))
        if actual < expected - 1:
            raise ValueError(
                f"Section '{stype}' has {actual} questions but {expected} were requested."
            )

    student_pdf, answer_key_pdf = create_question_paper_pdfs(data)
    return student_pdf, answer_key_pdf
