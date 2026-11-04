import streamlit as st
import requests
from urllib.parse import quote

from database.db import (
    get_latest_profile,
    get_connection,
    save_lesson_attempt,
    get_lesson_history,
    save_topic_diagnostic
)

from engines.learner_model import (
    get_learning_recommendations,
    get_topic_mastery
)

from engines.lesson_engine import (
    generate_personalised_lesson,
    generate_adaptive_explanation,
    generate_topic_diagnostic
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="LearnAble AI | Explore & Learn",
    page_icon="📚",
    layout="wide"
)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def get_topic_image(topic):
    """Find a relevant educational image for a topic."""

    try:
        url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + quote(topic.replace(" ", "_"))
        )

        response = requests.get(
            url,
            headers={"User-Agent": "LearnAbleAI/1.0"},
            timeout=8
        )
        response.raise_for_status()

        data = response.json()
        image_url = data.get("thumbnail", {}).get("source")

        return {
            "url": image_url,
            "source": data.get("content_urls", {})
                         .get("desktop", {})
                         .get("page")
        }

    except Exception:
        return {"url": None, "source": None}


def get_active_profile():
    """
    Return the active profile as a database row.

    The profile page stores a dictionary in session state,
    while this page needs the database row format.
    """

    profile_id = st.session_state.get("profile_id")

    if profile_id:
        connection = get_connection()

        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM student_profiles WHERE id = ?",
                (profile_id,)
            )
            return cursor.fetchone()
        finally:
            connection.close()

    return get_latest_profile()


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown("""
<style>

    .stApp {
        background-color: #F8FAFC;
    }

    .main .block-container {
        max-width: 1150px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp p,
    .stApp label {
        color: #1F2937;
    }

    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #1F2937;
    }

    .learning-banner {
        background: linear-gradient(120deg, #6C63FF, #8B5CF6);
        padding: 28px 32px;
        border-radius: 18px;
        margin: 12px 0 24px 0;
    }

    .learning-banner h2 {
        color: #FFFFFF !important;
        font-size: 27px;
        margin-bottom: 8px;
    }

    .learning-banner p {
        color: #F3F0FF !important;
        font-size: 15px;
        margin-bottom: 0;
    }

    .section-note {
        color: #64748B !important;
        font-size: 14px;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 15px;
    }

    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 17px 19px;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] {
        color: #1F2937 !important;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        min-height: 42px;
    }

    div[data-testid="stRadio"] label {
        color: #1F2937 !important;
    }

    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
    }

    hr {
        border-color: #E5E7EB;
    }

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# ACCESSIBILITY SETTINGS AND ACTIVE PROFILE
# --------------------------------------------------

profile = get_active_profile()

if not profile:
    st.title("Welcome to LearnAble AI")
    st.warning("Please create your learning profile first.")
    st.page_link(
        "pages/1_Learning_Profile.py",
        label="Create your learning profile",
        icon="➡️"
    )
    st.stop()

profile_id = profile[0]

st.session_state["profile_id"] = profile_id
st.session_state["student_profile"] = profile

learning_profile = {
    "learning_style": profile[3],
    "language_level": profile[4],
    "learning_pace": profile[5],
    "font_size": profile[6],
    "text_to_speech": profile[7],
    "reduced_animations": profile[8]
}

font_value = str(profile[6]).lower()

if "extra large" in font_value:
    font_size = "24px"
elif "large" in font_value:
    font_size = "22px"
elif "small" in font_value:
    font_size = "15px"
else:
    font_size = "18px"

st.markdown(
    f"""
    <style>
        .stMarkdown, .stText, [data-testid="stWidgetLabel"] {{
            font-size: {font_size};
        }}
    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

with st.sidebar:

    st.title("📚 LearnAble AI")
    st.caption("Learning without limits")

    st.divider()

    st.subheader("Navigation")

    st.page_link(
        "app.py",
        label="Dashboard",
        icon="➡️"
    )

    st.page_link(
        "pages/1_Learning_Profile.py",
        label="My Profile",
        icon="➡️"
    )

    st.page_link(
        "pages/2_Baseline_Assessment.py",
        label="Baseline Assessment",
        icon="➡️"
    )

    st.page_link(
        "pages/3_Personalised_Lesson.py",
        label="Learn & Practise",
        icon="➡️"
    )

    st.divider()

    st.caption("Learn something new, one step at a time.")


# --------------------------------------------------
# LEARNER EVALUATION
# --------------------------------------------------

st.title("Explore & Learn")

st.markdown("""
<div class="learning-banner">
    <h2>Your learning journey starts here! ✨</h2>
    <p>
        Choose a topic, discover what you already know, and receive
        a lesson adapted to your learning preferences.
    </p>
</div>
""", unsafe_allow_html=True)

recommendations = get_learning_recommendations(
    profile_id,
    learning_profile
)

if recommendations.get("status") != "Ready":

    st.info(
        "Before starting, complete your initial assessment. "
        "This helps LearnAble estimate your starting knowledge level."
    )

    st.page_link(
        "pages/2_Baseline_Assessment.py",
        label="Complete my initial assessment",
        icon="➡️"
    )

    st.stop()


# --------------------------------------------------
# LEARNING PROFILE SUMMARY
# --------------------------------------------------

with st.expander("👤 My learning preferences"):

    preference_col1, preference_col2 = st.columns(2)

    with preference_col1:
        st.write(f"**Learning style:** {profile[3]}")
        st.write(f"**Explanation level:** {profile[4]}")

    with preference_col2:
        st.write(f"**Learning pace:** {profile[5]}")
        st.write(
            f"**Current estimated level:** "
            f"{recommendations['knowledge_level']}"
        )

st.divider()


# --------------------------------------------------
# TOPIC SELECTION
# --------------------------------------------------

st.subheader("What would you like to learn today?")

st.caption(
    "Enter any topic or concept. LearnAble will prepare a short "
    "diagnostic before generating your personalised lesson."
)

topic = st.text_input(
    "Enter a topic or concept",
    placeholder="Example: Photosynthesis, Newton's Laws, Python loops...",
    key="student_topic"
)

if st.button(
    "Start learning",
    type="primary",
    width="stretch"
):

    if not topic.strip():
        st.warning("Please enter a topic.")

    else:
        st.session_state.pop("student_lesson", None)
        st.session_state.pop("student_result", None)
        st.session_state.pop("student_feedback", None)
        st.session_state.pop("student_diagnostic", None)
        st.session_state.pop("diagnostic_result", None)

        with st.spinner("Preparing your topic assessment..."):
            try:
                questions = generate_topic_diagnostic(topic.strip())

                st.session_state["student_diagnostic"] = {
                    "topic": topic.strip(),
                    "profile_id": profile_id,
                    "questions": questions
                }

                # Clear old diagnostic radio selections for the new topic.
                for index in range(3):
                    st.session_state.pop(
                        f"diagnostic_answer_{index}",
                        None
                    )

            except Exception as error:
                st.error(f"Unable to prepare the diagnostic: {error}")


# --------------------------------------------------
# TOPIC DIAGNOSTIC
# --------------------------------------------------

diagnostic = st.session_state.get("student_diagnostic")

if diagnostic and diagnostic["profile_id"] == profile_id:

    st.divider()

    st.subheader("🧠 First, let's check what you already know")

    st.caption(
        "Answer these three questions. This helps LearnAble "
        "choose an appropriate starting level."
    )

    with st.container(border=True):

        st.markdown(f"**Topic: {diagnostic['topic']}**")
        st.write("Select one answer for each question.")

        with st.form("topic_diagnostic_form"):

            diagnostic_answers = []

            for index, question in enumerate(diagnostic["questions"]):

                st.markdown(
                    f"**Question {index + 1}. {question['question']}**"
                )

                answer = st.radio(
                    f"Your answer to question {index + 1}",
                    ["A", "B", "C", "D"],
                    format_func=lambda option, q=question: (
                        f"{option}) {q['options'][option]}"
                    ),
                    index=None,
                    key=f"diagnostic_answer_{index}"
                )

                diagnostic_answers.append(answer)

                if index < len(diagnostic["questions"]) - 1:
                    st.divider()

            diagnostic_submitted = st.form_submit_button(
                "Submit diagnostic",
                type="primary",
                use_container_width=True
            )

    if diagnostic_submitted:

        if any(answer is None for answer in diagnostic_answers):
            st.warning("Please answer all three questions.")

        else:
            with st.spinner(
                "Analysing your answers and preparing your lesson..."
            ):

                try:
                    diagnostic_result = save_topic_diagnostic(
                        profile_id,
                        diagnostic["topic"],
                        diagnostic["questions"],
                        diagnostic_answers
                    )

                    accuracy = diagnostic_result["accuracy"]

                    # BKT: estimate mastery after saving diagnostic responses.
                    mastery_data = get_topic_mastery(profile_id)
                    topic_key = diagnostic["topic"].strip().casefold()

                    # Match topic names without being affected by capitalisation.
                    matching_mastery = [
                        value
                        for saved_topic, value in mastery_data.items()
                        if saved_topic.strip().casefold() == topic_key
                    ]

                    topic_mastery = None

                    if matching_mastery:
                        # If old records contain differently-cased topic names,
                        # use the entry with the most observations.
                        topic_mastery = max(
                            matching_mastery,
                            key=lambda item: item["observations"]
                        )

                    # Use BKT mastery for adaptation when available.
                    # Fall back to the current diagnostic score otherwise.
                    if topic_mastery:
                        mastery_percent = topic_mastery["mastery_percent"]

                        if mastery_percent < 50:
                            knowledge_level = "Beginner"
                            complexity = "Very simple"
                        elif mastery_percent < 80:
                            knowledge_level = "Developing"
                            complexity = "Simple"
                        else:
                            knowledge_level = "Strong"
                            complexity = "Moderate"

                    else:
                        if accuracy <= 33:
                            knowledge_level = "Beginner"
                            complexity = "Very simple"
                        elif accuracy <= 66:
                            knowledge_level = "Developing"
                            complexity = "Simple"
                        else:
                            knowledge_level = "Strong"
                            complexity = "Moderate"

                    topic_recommendations = dict(recommendations)
                    topic_recommendations["knowledge_level"] = knowledge_level
                    topic_recommendations["recommended_complexity"] = complexity
                    topic_recommendations["topic_diagnostic_accuracy"] = accuracy
                    topic_recommendations["topic_mastery"] = topic_mastery

                    # Keep estimated mastery with the diagnostic result.
                    diagnostic_result["bkt_mastery"] = (
                        topic_mastery["mastery_percent"]
                        if topic_mastery else None
                    )

                    lesson = generate_personalised_lesson(
                        diagnostic["topic"],
                        topic_recommendations,
                        learning_profile
                    )

                    st.session_state["student_lesson"] = {
                        "topic": diagnostic["topic"],
                        "profile_id": profile_id,
                        "content": lesson,
                        "diagnostic": diagnostic_result,
                        "knowledge_level": knowledge_level
                    }

                    st.session_state["diagnostic_result"] = diagnostic_result

                    st.rerun()

                except Exception as error:
                    st.error(f"Unable to prepare your lesson: {error}")


# --------------------------------------------------
# DIAGNOSTIC RESULT
# --------------------------------------------------

diagnostic_result = st.session_state.get("diagnostic_result")

if diagnostic_result:

    st.success(
        f"Starting knowledge: {diagnostic_result['score']}/"
        f"{diagnostic_result['total_questions']} "
        f"({diagnostic_result['accuracy']:.0f}%). "
        "Your lesson has been adapted to your result."
    )

    if diagnostic_result.get("bkt_mastery") is not None:
        st.caption(
            "BKT-estimated topic mastery: "
            f"{diagnostic_result['bkt_mastery']:.2f}%. "
            "This estimate is used to select the lesson difficulty."
        )


# --------------------------------------------------
# PERSONALISED LESSON
# --------------------------------------------------

lesson_data = st.session_state.get("student_lesson")

if lesson_data and lesson_data["profile_id"] == profile_id:

    lesson = lesson_data["content"]

    st.divider()

    st.header(lesson["title"])
    st.write(lesson["hook"])

    # Lesson difficulty and topic context.
    lesson_col1, lesson_col2 = st.columns(2)

    with lesson_col1:
        st.caption(f"📘 Topic: {lesson_data['topic']}")

    with lesson_col2:
        st.caption(
            f"🎯 Starting level: {lesson_data['knowledge_level']}"
        )

    st.divider()

    # --------------------------------------------------
    # ADAPTED CONTENT FORMAT
    # --------------------------------------------------

    if profile[3] == "Visual explanations":

        st.subheader("Explore the concept visually")

        with st.spinner("Finding a relevant educational image..."):
            visual = get_topic_image(lesson_data["topic"])

        if visual["url"]:

            st.image(
                visual["url"],
                caption=f"Visual reference: {lesson_data['topic']}",
                use_container_width=True
            )

            if visual["source"]:
                st.caption(f"Image source: {visual['source']}")

        else:
            st.info(
                "A topic image is not available right now. "
                "You can still use the visual explanation below."
            )

        st.subheader("Understand the diagram")
        st.write(lesson["visual_description"])

        st.subheader("The main idea")
        st.write(lesson["core_idea"])

    elif profile[3] == "Listening to audio":

        st.subheader("Listen-friendly explanation")

        st.write(lesson["core_idea"])
        st.info(lesson["visual_description"])

        st.caption(
            "This content is prepared in a listen-friendly format. "
            "Actual speech playback is not currently implemented."
        )

    else:

        st.subheader("Understand the concept")

        st.write(lesson["core_idea"])

        if profile[3] == "Step-by-step explanations":

            st.subheader("Learn one step at a time")

            for index, step in enumerate(lesson["steps"], 1):

                with st.container(border=True):
                    st.markdown(f"**Step {index}**")
                    st.write(step)

        else:

            with st.expander("Explore the explanation step by step"):

                for index, step in enumerate(lesson["steps"], 1):
                    st.write(f"{index}. {step}")

    with st.expander("Explore another explanation format"):

        st.write(lesson["core_idea"])
        st.write(lesson["visual_description"])

        if lesson.get("steps"):
            st.markdown("**Step-by-step explanation**")

            for index, step in enumerate(lesson["steps"], 1):
                st.write(f"{index}. {step}")

    # Example and key takeaway.
    st.subheader("Try an example")

    with st.container(border=True):
        st.write(lesson["activity"])

    st.subheader("Remember this")

    st.success(
        lesson["steps"][-1]
        if lesson["steps"]
        else lesson["core_idea"]
    )

    st.divider()


    # --------------------------------------------------
    # UNDERSTANDING ASSESSMENT
    # --------------------------------------------------

    st.subheader("📝 Check your understanding")

    st.write(lesson["question"])

    result = st.session_state.get("student_result")

    if not result:

        quiz_version = st.session_state.get("quiz_version", 0)

        with st.form(f"student_check_{quiz_version}"):

            selected_answer = st.radio(
                "Choose your answer",
                ["A", "B", "C", "D"],
                format_func=lambda option: (
                    f"{option}) {lesson['options'][option]}"
                ),
                index=None
            )

            submitted = st.form_submit_button(
                "Check my answer",
                type="primary",
                use_container_width=True
            )

        if submitted:

            if selected_answer is None:

                st.warning("Please select an answer.")

            else:

                correct = (
                    selected_answer == lesson["correct_answer"]
                )

                try:
                    save_lesson_attempt(
                        profile_id,
                        lesson_data["topic"],
                        int(correct),
                        1
                    )

                except Exception as error:
                    st.error(f"Could not save your result: {error}")

                st.session_state["student_result"] = {
                    "correct": correct,
                    "selected": selected_answer
                }

                if not correct:

                    with st.spinner(
                        "Let's try a different way of explaining this..."
                    ):

                        try:
                            feedback = generate_adaptive_explanation(
                                lesson_data["topic"],
                                lesson["core_idea"],
                                lesson["question"],
                                selected_answer,
                                lesson["correct_answer"],
                                lesson["explanation"],
                                learning_profile
                            )

                        except Exception:
                            feedback = (
                                "Let's look at the concept again. "
                                "Review the explanation and think about "
                                "how the example connects to the main idea."
                            )

                        st.session_state["student_feedback"] = feedback

                st.rerun()

    else:

        if result["correct"]:

            st.success("Correct! You understood this concept.")

            st.write(lesson["explanation"])

            st.write("Your learning result has been saved.")

        else:

            st.warning("Not quite. Let's understand it another way.")

            st.write(
                st.session_state.get("student_feedback", "")
            )

            if st.button("Try again", type="primary"):

                st.session_state.pop("student_result", None)
                st.session_state.pop("student_feedback", None)

                st.session_state["quiz_version"] = (
                    st.session_state.get("quiz_version", 0) + 1
                )

                st.rerun()


# --------------------------------------------------
# STUDENT PROGRESS
# --------------------------------------------------

st.divider()

st.subheader("📈 My learning progress")

history = get_lesson_history(profile_id)

if history:

    st.dataframe(
        [
            {
                "Topic": row[0],
                "Score": f"{row[1]}/{row[2]}",
                "Accuracy": f"{row[3]:.0f}%",
                "Date": row[4]
            }
            for row in history
        ],
        width="stretch",
        hide_index=True
    )

else:

    st.info("Your learning progress will appear here.")


# --------------------------------------------------
# BKT TOPIC MASTERY
# --------------------------------------------------

mastery_history = get_topic_mastery(profile_id)

if mastery_history:

    st.divider()

    st.subheader("🧠 My topic mastery")

    st.caption(
        "Estimated using Bayesian Knowledge Tracing (BKT). "
        "Mastery updates as you answer diagnostic and lesson questions."
    )

    mastery_rows = [
        {
            "Topic": topic.title(),
            "Estimated mastery": f"{data['mastery_percent']:.2f}%",
            "Responses": data["observations"],
            "Learning status": data["status"]
        }
        for topic, data in sorted(mastery_history.items())
    ]

    st.dataframe(
        mastery_rows,
        width="stretch",
        hide_index=True
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "LearnAble AI | Learn at your pace. Grow with every attempt."
)
