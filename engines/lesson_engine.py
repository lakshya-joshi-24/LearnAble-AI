
import os
import json
from dotenv import load_dotenv
from google import genai


MODEL_NAME = "gemini-3.5-flash-lite"



def generate_personalised_lesson(
    concept,
    recommendations,
    learning_profile=None
):
    """Generate a structured lesson adapted to learner preferences."""

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Gemini API key not found in .env")

    if not concept or not concept.strip():
        raise ValueError("Please provide a topic.")

    learning_profile = learning_profile or {}
    recommendations = recommendations or {}

    learning_style = learning_profile.get(
        "learning_style",
        "Step-by-step explanations"
    )

    learning_pace = learning_profile.get(
        "learning_pace",
        "Normal"
    )

    complexity = recommendations.get(
         "recommended_complexity",
          learning_profile.get("language_level", "Simple")
    )

    knowledge_level = recommendations.get(
        "knowledge_level",
        "Not assessed"
    )

    prompt = f"""
Create an accurate educational lesson about: {concept}

Learner information:
- Knowledge level: {knowledge_level}
- Learning style: {learning_style}
- Language complexity: {complexity}
- Learning pace: {learning_pace}

Adapt the teaching to these preferences.

Return ONLY valid JSON with exactly these keys:

{{
  "title": "Lesson title",
  "hook": "An engaging introduction",
  "visual_description": "A visual explanation using text or a simple diagram",
  "core_idea": "The main explanation",
  "steps": ["Step 1", "Step 2", "Step 3"],
  "activity": "A relatable practical example or activity",
  "question": "One multiple-choice question",
  "options": {{
    "A": "Option A",
    "B": "Option B",
    "C": "Option C",
    "D": "Option D"
  }},
  "correct_answer": "A",
  "explanation": "Why the correct answer is correct"
}}

Rules:
- Use accurate educational information.
- Keep explanations appropriate for the learner's level.
- Use short, clear sentences.
- Adapt the explanation to the selected learning style.
- Make the question test understanding, not memorisation alone.
- Ensure exactly four answer options.
- The correct_answer must be A, B, C, or D.
- Do not include the answer key anywhere except the correct_answer field.
- Return valid JSON only. No Markdown fences.
"""

    try:
        client = genai.Client(
            api_key=api_key,
            http_options={"timeout": 120000}
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "max_output_tokens": 1200,
                "temperature": 0.4
            }
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        lesson = json.loads(response.text)

        required_keys = {
            "title", "hook", "visual_description", "core_idea",
            "steps", "activity", "question", "options",
            "correct_answer", "explanation"
        }

        if not required_keys.issubset(lesson):
            raise ValueError("Generated lesson is missing required fields.")

        if set(lesson["options"].keys()) != {"A", "B", "C", "D"}:
            raise ValueError("Lesson must contain exactly four options.")

        if lesson["correct_answer"] not in {"A", "B", "C", "D"}:
            raise ValueError("Invalid correct answer.")

        if not isinstance(lesson["steps"], list) or not lesson["steps"]:
            raise ValueError("Lesson steps are missing.")

        return lesson

    except Exception as error:
        raise RuntimeError(
            f"Lesson generation failed: {error}"
        ) from error


def generate_topic_diagnostic(concept):
    """Generate three questions to estimate prior knowledge of a topic."""

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing.")

    prompt = f"""
Create exactly 3 beginner-friendly diagnostic MCQs about: {concept}

These questions must test prior understanding, not obscure facts.

Return ONLY valid JSON in this format:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct_answer": "A",
      "explanation": "Short explanation"
    }}
  ]
}}

Rules:
- Exactly 3 questions.
- Four options per question.
- Exactly one correct answer.
- Correct answer must be A, B, C or D.
- Keep questions clear and accurate.
- No Markdown fences.
"""

    try:
        client = genai.Client(
            api_key=api_key,
            http_options={"timeout": 120000}
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "max_output_tokens": 1000,
                "temperature": 0.3
            }
        )

        data = json.loads(response.text)
        questions = data.get("questions", [])

        if len(questions) != 3:
            raise ValueError("Diagnostic must contain exactly 3 questions.")

        for question in questions:
            if set(question["options"]) != {"A", "B", "C", "D"}:
                raise ValueError("A diagnostic question has invalid options.")
            if question["correct_answer"] not in {"A", "B", "C", "D"}:
                raise ValueError("A diagnostic question has an invalid answer.")

        return questions

    except Exception as error:
        raise RuntimeError(
            f"Topic diagnostic generation failed: {error}"
        ) from error

def generate_adaptive_explanation(
    concept,
    core_idea,
    question,
    selected_answer,
    correct_answer,
    explanation,
    learning_profile
):
    """Generate a different explanation after an incorrect answer."""

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing.")

    learning_profile = learning_profile or {}

    learning_style = learning_profile.get(
        "learning_style", "Step-by-step explanations"
    )

    complexity = learning_profile.get(
        "language_level", "Simple"
    )

    prompt = f"""
You are the adaptive teaching engine of LearnAble AI.

The student is learning: {concept}

Original explanation:
{core_idea}

Question:
{question}

Student's selected answer:
{selected_answer}

Correct answer:
{correct_answer}

Correct explanation:
{explanation}

Learning preferences:
Style: {learning_style}
Complexity: {complexity}

The student selected an incorrect answer.

Your task:
1. Explain the concept in a DIFFERENT way.
2. Adapt the explanation to the student's learning style.
3. Use a simple real-life example.
4. Be supportive and never shame the student.
5. Give one useful hint for trying again.
6. Keep the response under 120 words.
7. Do not simply repeat the original explanation.

Return only the teaching feedback.
"""

    try:
        client = genai.Client(
            api_key=api_key,
            http_options={"timeout": 120000}
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "max_output_tokens": 300,
                "temperature": 0.7
            }
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty explanation.")

        return response.text.strip()

    except Exception as error:
        raise RuntimeError(
            f"Adaptive explanation failed: {error}"
        ) from error
