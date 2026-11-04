from database.db import get_student_quiz_history, get_connection


# BKT starting parameters.
# These are prototype assumptions and can be calibrated with real data.
INITIAL_MASTERY = 0.30
LEARNING_PROBABILITY = 0.20
GUESS_PROBABILITY = 0.20
SLIP_PROBABILITY = 0.10


def update_mastery(mastery, is_correct):
    """Update the probability of mastery after one response."""

    if is_correct:
        numerator = mastery * (1 - SLIP_PROBABILITY)
        denominator = numerator + (
            (1 - mastery) * GUESS_PROBABILITY
        )
    else:
        numerator = mastery * SLIP_PROBABILITY
        denominator = numerator + (
            (1 - mastery) * (1 - GUESS_PROBABILITY)
        )

    if denominator == 0:
        posterior = mastery
    else:
        posterior = numerator / denominator

    # Account for the possibility that learning happened.
    updated_mastery = posterior + (
        (1 - posterior) * LEARNING_PROBABILITY
    )

    return updated_mastery


def get_topic_mastery(profile_id):
    """
    Calculate topic-wise mastery using Bayesian Knowledge Tracing.

    Uses baseline responses, topic diagnostic responses,
    and one-question lesson attempts.
    """

    connection = get_connection()
    cursor = connection.cursor()

    topic_events = {}

    def add_event(topic, timestamp, event_id, is_correct):
        if not topic:
          return

        topic = topic.strip().casefold()

        topic_events.setdefault(topic, []).append(
            (timestamp or "", event_id, bool(is_correct))
        )

    try:
        # 1. Baseline assessment responses.
        cursor.execute("""
            SELECT
                q.concept,
                a.created_at,
                r.id,
                r.is_correct
            FROM quiz_attempts a
            JOIN quiz_responses r ON a.id = r.attempt_id
            JOIN quiz_questions q ON r.question_id = q.id
            WHERE a.profile_id = ?
        """, (profile_id,))

        for topic, timestamp, event_id, correct in cursor.fetchall():
            add_event(topic, timestamp, event_id, correct)

        # 2. Topic-specific diagnostic responses.
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN (
                  'topic_diagnostics',
                  'topic_diagnostic_responses'
              )
        """)

        existing_tables = {row[0] for row in cursor.fetchall()}

        if {
            "topic_diagnostics",
            "topic_diagnostic_responses"
        }.issubset(existing_tables):

            cursor.execute("""
                SELECT
                    d.topic,
                    d.created_at,
                    r.id,
                    r.is_correct
                FROM topic_diagnostics d
                JOIN topic_diagnostic_responses r
                    ON d.id = r.diagnostic_id
                WHERE d.profile_id = ?
            """, (profile_id,))

            for topic, timestamp, event_id, correct in cursor.fetchall():
                add_event(topic, timestamp, event_id, correct)

        # 3. One-question lesson attempts.
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'lesson_attempts'
        """)

        if cursor.fetchone():

            cursor.execute("""
                SELECT
                    concept,
                    created_at,
                    id,
                    score,
                    total_questions
                FROM lesson_attempts
                WHERE profile_id = ?
            """, (profile_id,))

            for topic, timestamp, event_id, score, total in cursor.fetchall():

                # The current lesson assessment contains one question.
                # Avoid treating an aggregate multi-question score
                # as a sequence of individual responses.
                if total == 1:
                    add_event(
                        topic,
                        timestamp,
                        event_id,
                        score == 1
                    )

        # Calculate mastery separately for each topic.
        mastery_results = {}

        for topic, events in topic_events.items():

            events.sort(key=lambda event: (event[0], event[1]))

            mastery = INITIAL_MASTERY

            for _, _, is_correct in events:
                mastery = update_mastery(mastery, is_correct)

            mastery_percent = round(mastery * 100, 2)

            if mastery_percent < 50:
                status = "Needs reinforcement"
            elif mastery_percent < 80:
                status = "Developing mastery"
            else:
                status = "Mastered"

            mastery_results[topic] = {
                "mastery_probability": round(mastery, 4),
                "mastery_percent": mastery_percent,
                "observations": len(events),
                "status": status
            }

        return mastery_results

    finally:
        connection.close()


def get_concept_performance(profile_id):
    """Analyse a student's baseline performance for each concept."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                q.concept,
                COUNT(*) AS total_questions,
                SUM(r.is_correct) AS correct_answers
            FROM quiz_attempts a
            JOIN quiz_responses r
                ON a.id = r.attempt_id
            JOIN quiz_questions q
                ON r.question_id = q.id
            WHERE a.profile_id = ?
            GROUP BY q.concept
        """, (profile_id,))

        results = cursor.fetchall()
        concept_performance = {}

        for concept, total, correct in results:
            accuracy = round((correct / total) * 100, 2)

            concept_performance[concept] = {
                "total_questions": total,
                "correct_answers": correct,
                "accuracy": accuracy
            }

        return concept_performance

    finally:
        connection.close()


def classify_knowledge_level(accuracy):
    """Classify assessment performance."""

    if accuracy <= 40:
        return "Beginner", "Very simple"
    elif accuracy <= 60:
        return "Developing", "Simple"
    elif accuracy <= 80:
        return "Intermediate", "Moderate"
    else:
        return "Strong", "Detailed"


def get_learning_recommendations(profile_id, learning_profile):
    """Generate a personalised learning plan."""

    history = get_student_quiz_history(profile_id)

    if not history:
        return {
            "status": "No assessment completed",
            "message": "Complete a baseline assessment to receive personalised recommendations."
        }

    latest_attempt = history[-1]

    score = latest_attempt[2]
    total_questions = latest_attempt[3]
    accuracy = latest_attempt[4]

    knowledge_level, recommended_complexity = (
        classify_knowledge_level(accuracy)
    )

    concept_performance = get_concept_performance(profile_id)
    topic_mastery = get_topic_mastery(profile_id)

    concepts_to_practice = [
        concept
        for concept, performance in concept_performance.items()
        if performance["accuracy"] < 60
    ]

    # Include topics identified by BKT as needing reinforcement.
    for topic, mastery in topic_mastery.items():
        if (
            mastery["mastery_percent"] < 50
            and topic not in concepts_to_practice
        ):
            concepts_to_practice.append(topic)

    teaching_strategy = get_teaching_strategy(
        learning_profile["learning_style"],
        learning_profile["learning_pace"]
    )

    return {
        "status": "Ready",
        "score": score,
        "total_questions": total_questions,
        "accuracy": accuracy,
        "knowledge_level": knowledge_level,
        "recommended_complexity": recommended_complexity,
        "learning_style": learning_profile["learning_style"],
        "learning_pace": learning_profile["learning_pace"],
        "teaching_approach": teaching_strategy["teaching_approach"],
        "pace_strategy": teaching_strategy["pace_strategy"],
        "concepts_to_practice": concepts_to_practice,
        "concept_performance": concept_performance,
        "topic_mastery": topic_mastery
    }


def get_teaching_strategy(learning_style, learning_pace):
    """Convert student preferences into teaching strategies."""

    strategies = {
        "Visual explanations": "Use diagrams, illustrations and visual examples.",
        "Reading text": "Use clear written explanations with headings and examples.",
        "Listening to audio": "Provide audio-friendly explanations with short spoken sections.",
        "Step-by-step explanations": "Break concepts into small, sequential steps."
    }

    pace_strategies = {
        "Slow and steady": "Present one small section at a time with frequent checks for understanding.",
        "Normal": "Use a balanced explanation with regular practice questions.",
        "Self-paced": "Allow the student to control progression and revisit explanations."
    }

    return {
        "teaching_approach": strategies.get(
            learning_style,
            "Use clear explanations with examples."
        ),
        "pace_strategy": pace_strategies.get(
            learning_pace,
            "Allow the student to learn at a comfortable pace."
        )
    }