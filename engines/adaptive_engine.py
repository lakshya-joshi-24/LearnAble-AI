import os
import json

from dotenv import load_dotenv
from google import genai

from data.lesson_library import LESSON_LIBRARY


MODEL_NAME = "gemini-3.5-flash-lite"


def adapt_lesson(lesson_key, learner_profile):
    """
    Adapt one common lesson to a learner's preferences.

    The underlying facts and learning objectives must remain unchanged.
    """

    lesson = LESSON_LIBRARY.get(lesson_key.lower())

    if not lesson:
        raise ValueError("This lesson is not available in the lesson library.")

    learner_profile = learner_profile or {}

    learning_style = learner_profile.get(
        "learning_style", "Step-by-step explanations"
    )

    language_level = learner_profile.get(
        "language_level", "Simple"
    )

    learning_pace = learner_profile.get(
        "learning_pace", "Normal"
    )

    font_size = learner_profile.get(
        "font_size", "Medium"
    )

    text_to_speech = learner_profile.get(
        "text_to_speech", False
    )

    reduced_animations = learner_profile.get(
        "reduced_animations", False
    )

    prompt = f"""
You are the adaptive content engine of LearnAble AI.

Your task is to adapt an existing educational lesson to a learner.

IMPORTANT:
The source lesson is authoritative.
Do not change scientific facts.
Do not remove any learning objective.
Do not introduce contradictory information.
Do not make assumptions about disability or ability.

SOURCE LESSON:
Title: {lesson['title']}

Learning objectives:
{json.dumps(lesson['learning_objectives'])}

Original educational content:
{lesson['core_content']}

Key facts:
{json.dumps(lesson['key_facts'])}

LEARNER PREFERENCES:
Learning style: {learning_style}
Language complexity: {language_level}
Learning pace: {learning_pace}
Font size preference: {font_size}
Text-to-speech enabled: {text_to_speech}
Reduced animations: {reduced_animations}

CREATE THESE FOUR REPRESENTATIONS:

1. adapted_explanation:
A learner-friendly explanation in the requested language complexity.

2. visual_content:
A simple visual explanation using text, arrows, labels or a diagram.
Make it useful even without images.

3. audio_script:
A natural spoken explanation with short sentences and pauses.
Avoid symbols that are difficult for screen readers.

4. learning_steps:
A sequence of short learning steps suited to the selected pace.

Also provide:
- one short real-life example
- one small learning activity
- three learning objectives copied from the source lesson
- a short recap

ADAPTATION RULES:
- Visual preference: prioritise diagrams and visual relationships.
- Reading text: use organised written explanations.
- Listening to audio: use natural spoken language.
- Step-by-step explanations: divide information into small sequential parts.
- Slow and steady: keep sections short and include pauses.
- Normal: use a balanced sequence.
- Self-paced: make sections independently understandable.
- Very simple: use familiar words and explain difficult terms.
- Simple: use clear language with basic subject terminology.
- Moderate: use appropriate subject terminology with explanations.
- Detailed: include more precise terminology and detail.

Return ONLY valid JSON using this structure:

{{
  "title": "Lesson title",
  "adapted_explanation": "Adapted explanation",
  "visual_content": "Visual representation",
  "audio_script": "Audio-friendly explanation",
  "learning_steps": [
    "Step 1",
    "Step 2",
    "Step 3"
  ],
  "example": "Real-life example",
  "activity": "Small learning activity",
  "objectives": [
    "Objective 1",
    "Objective 2",
    "Objective 3"
  ],
  "recap": "Short recap"
}}
"""

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from .env.")

    client = genai.Client(
        api_key=api_key,
        http_options={"timeout": 120000}
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "max_output_tokens": 1300,
                "temperature": 0.3
            }
        )

        if not response.text:
            raise RuntimeError("The AI returned an empty response.")

        adapted = json.loads(response.text)

        required_fields = [
            "title",
            "adapted_explanation",
            "visual_content",
            "audio_script",
            "learning_steps",
            "example",
            "activity",
            "objectives",
            "recap"
        ]

        for field in required_fields:
            if field not in adapted:
                raise ValueError(f"Missing field: {field}")

        if len(adapted["objectives"]) != len(lesson["learning_objectives"]):
            raise ValueError("The adapted lesson changed the number of learning objectives.")

        return adapted

    except Exception as error:
        raise RuntimeError(
            f"Content adaptation failed: {error}"
        ) from error