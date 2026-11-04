
import sqlite3

DB_PATH = "database/learnable.db"


def get_connection():
    """Create a connection to our SQLite database."""
    return sqlite3.connect(DB_PATH)


def initialize_database():
    """Create the student profiles table if it doesn't exist."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age_group TEXT,
            learning_style TEXT,
            language_level TEXT,
            learning_pace TEXT,
            font_size TEXT,
            text_to_speech INTEGER,
            reduced_animations INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
        # Quiz Questions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL
        )
    """)

    # Quiz Attempts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(profile_id) REFERENCES student_profiles(id)
        )
    """)

    # Quiz Responses Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            selected_option TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            FOREIGN KEY(attempt_id) REFERENCES quiz_attempts(id),
            FOREIGN KEY(question_id) REFERENCES quiz_questions(id)
        )
    """)

    connection.commit()
    connection.close()


def save_profile(profile):
    """Save a student's profile in SQLite."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO student_profiles (
            name, age_group, learning_style,
            language_level, learning_pace,
            font_size, text_to_speech,
            reduced_animations
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        profile["name"],
        profile["age_group"],
        profile["learning_style"],
        profile["language_level"],
        profile["learning_pace"],
        profile["font_size"],
        int(profile["text_to_speech"]),
        int(profile["reduced_animations"])
    ))

    profile_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return profile_id

def get_latest_profile():
    """Retrieve the most recently saved student profile."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM student_profiles
        ORDER BY id DESC
        LIMIT 1
    """)

    profile = cursor.fetchone()
    connection.close()

    return profile
def add_quiz_questions(questions):
    """Insert quiz questions into the database without creating duplicates."""

    connection = get_connection()
    cursor = connection.cursor()

    added_count = 0

    for question in questions:
        cursor.execute("""
            SELECT id FROM quiz_questions
            WHERE topic = ? AND question = ?
        """, (question["topic"], question["question"]))

        existing_question = cursor.fetchone()

        if existing_question is None:
            cursor.execute("""
                INSERT INTO quiz_questions (
                    topic, question,
                    option_a, option_b,
                    option_c, option_d,
                    correct_option
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                question["topic"],
                question["question"],
                question["option_a"],
                question["option_b"],
                question["option_c"],
                question["option_d"],
                question["correct_option"]
            ))

            added_count += 1

    connection.commit()
    connection.close()

    return added_count
def get_quiz_questions(topic):
    """Retrieve all questions for a given topic."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, topic, question,
               option_a, option_b,
               option_c, option_d
        FROM quiz_questions
        WHERE topic = ?
    """, (topic,))

    questions = cursor.fetchall()
    connection.close()

    return questions
def save_quiz_attempt(profile_id, topic, answers):
    """Evaluate quiz answers and save the attempt in SQLite."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Verify that the student profile exists
        cursor.execute(
            "SELECT id FROM student_profiles WHERE id = ?",
            (profile_id,)
        )

        if cursor.fetchone() is None:
            raise ValueError("Student profile not found.")

        question_ids = list(answers.keys())

        if not question_ids:
            raise ValueError("No quiz answers provided.")

        # Retrieve correct answers
        placeholders = ",".join("?" for _ in question_ids)

        cursor.execute(f"""
            SELECT id, correct_option
            FROM quiz_questions
            WHERE id IN ({placeholders})
        """, question_ids)

        correct_answers = dict(cursor.fetchall())

        if len(correct_answers) != len(question_ids):
            raise ValueError("Some quiz questions were not found.")

        # Calculate score
        score = 0
        responses = []

        for question_id, selected_option in answers.items():

            if selected_option not in ["A", "B", "C", "D"]:
                raise ValueError("Invalid answer selected.")

            is_correct = (
                selected_option == correct_answers[question_id]
            )

            if is_correct:
                score += 1

            responses.append((
                question_id,
                selected_option,
                int(is_correct)
            ))

        total_questions = len(question_ids)
        accuracy = round((score / total_questions) * 100, 2)

        # Save quiz attempt
        cursor.execute("""
            INSERT INTO quiz_attempts (
                profile_id, topic, score,
                total_questions, accuracy
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            profile_id,
            topic,
            score,
            total_questions,
            accuracy
        ))

        attempt_id = cursor.lastrowid

        # Save individual responses
        for question_id, selected_option, is_correct in responses:

            cursor.execute("""
                INSERT INTO quiz_responses (
                    attempt_id, question_id,
                    selected_option, is_correct
                )
                VALUES (?, ?, ?, ?)
            """, (
                attempt_id,
                question_id,
                selected_option,
                is_correct
            ))

        connection.commit()

        return {
            "attempt_id": attempt_id,
            "score": score,
            "total_questions": total_questions,
            "accuracy": accuracy
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
def add_concept_column():
    """Safely add the concept column if it does not already exist."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("PRAGMA table_info(quiz_questions)")
        columns = [row[1] for row in cursor.fetchall()]

        if "concept" not in columns:
            cursor.execute(
                "ALTER TABLE quiz_questions ADD COLUMN concept TEXT"
            )
            connection.commit()
            print("Concept column added successfully.")
        else:
            print("Concept column already exists.")

    finally:
        connection.close()
def update_question_concepts(questions):
    """Update concept tags for existing quiz questions."""

    connection = get_connection()
    cursor = connection.cursor()

    updated_count = 0

    try:
        for question in questions:
            cursor.execute("""
                UPDATE quiz_questions
                SET concept = ?
                WHERE topic = ? AND question = ?
            """, (
                question["concept"],
                question["topic"],
                question["question"]
            ))

            updated_count += cursor.rowcount

        connection.commit()
        return updated_count

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
def get_student_quiz_history(profile_id):
    """Retrieve all quiz attempts for a specific student."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                topic,
                score,
                total_questions,
                accuracy,
                created_at
            FROM quiz_attempts
            WHERE profile_id = ?
            ORDER BY created_at ASC, id ASC
        """, (profile_id,))

        history = cursor.fetchall()
        return history

    finally:
        connection.close()
def save_lesson_attempt(profile_id, concept, score, total_questions):
    """Save a student's personalised lesson assessment."""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                concept TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES student_profiles(id)
            )
        """)

        accuracy = (score / total_questions) * 100 if total_questions else 0

        cursor.execute("""
            INSERT INTO lesson_attempts
            (profile_id, concept, score, total_questions, accuracy)
            VALUES (?, ?, ?, ?, ?)
        """, (profile_id, concept, score, total_questions, accuracy))

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_lesson_history(profile_id):
    """Retrieve a student's personalised lesson assessment history."""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                concept TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES student_profiles(id)
            )
        """)

        cursor.execute("""
            SELECT concept, score, total_questions, accuracy, created_at
            FROM lesson_attempts
            WHERE profile_id = ?
            ORDER BY id DESC
        """, (profile_id,))

        return cursor.fetchall()

    finally:
        connection.close()
def get_all_profiles():
    """Retrieve all saved learner profiles."""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM student_profiles
            ORDER BY id ASC
        """)

        return cursor.fetchall()

    finally:
        connection.close()

def save_topic_diagnostic(profile_id, topic, questions, answers):
    """Save a topic-specific diagnostic and the learner's responses."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_diagnostics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES student_profiles(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_diagnostic_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                diagnostic_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                selected_option TEXT NOT NULL,
                correct_option TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                FOREIGN KEY (diagnostic_id)
                    REFERENCES topic_diagnostics(id)
            )
        """)

        total = len(questions)
        score = sum(
            1 for question, answer in zip(questions, answers)
            if answer == question["correct_answer"]
        )
        accuracy = (score / total) * 100 if total else 0

        cursor.execute("""
            INSERT INTO topic_diagnostics
            (profile_id, topic, score, total_questions, accuracy)
            VALUES (?, ?, ?, ?, ?)
        """, (profile_id, topic, score, total, accuracy))

        diagnostic_id = cursor.lastrowid

        for question, answer in zip(questions, answers):
            correct_option = question["correct_answer"]

            cursor.execute("""
                INSERT INTO topic_diagnostic_responses
                (diagnostic_id, question, selected_option,
                 correct_option, is_correct)
                VALUES (?, ?, ?, ?, ?)
            """, (
                diagnostic_id,
                question["question"],
                answer,
                correct_option,
                int(answer == correct_option)
            ))

        connection.commit()

        return {
            "diagnostic_id": diagnostic_id,
            "score": score,
            "total_questions": total,
            "accuracy": accuracy
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
