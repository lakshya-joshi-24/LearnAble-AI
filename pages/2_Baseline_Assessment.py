import streamlit as st

from database.db import get_quiz_questions, save_quiz_attempt
from database.db import initialize_database, add_quiz_questions
from database.quiz_data import BASIC_SCIENCE_QUESTIONS

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Baseline Assessment | LearnAble AI",
    page_icon="📝",
    layout="wide"
)
# Initialize database and seed baseline questions
initialize_database()
add_quiz_questions(BASIC_SCIENCE_QUESTIONS)

# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown("""
<style>

    .stApp {
        background-color: #F8FAFC;
    }

    .main .block-container {
        max-width: 1050px;
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

    .assessment-banner {
        background: linear-gradient(120deg, #6C63FF, #8B5CF6);
        padding: 28px 32px;
        border-radius: 18px;
        margin: 12px 0 24px 0;
    }

    .assessment-banner h2 {
        color: #FFFFFF !important;
        font-size: 26px;
        margin-bottom: 8px;
    }

    .assessment-banner p {
        color: #F3F0FF !important;
        font-size: 15px;
        margin-bottom: 0;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-color: #E5E7EB;
        border-radius: 14px;
    }

    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 18px;
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
        min-height: 44px;
    }

    hr {
        border-color: #E5E7EB;
    }

</style>
""", unsafe_allow_html=True)


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

    st.caption("Understand what you already know.")


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("Baseline Assessment")

st.markdown("""
<div class="assessment-banner">
    <h2>Let's discover what you already know! 🧠</h2>
    <p>
        Answer these questions to help us understand your current
        knowledge and personalise your learning journey.
    </p>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# CHECK STUDENT PROFILE
# --------------------------------------------------

profile_id = st.session_state.get("profile_id")

if not profile_id:

    st.warning(
        "Please save your Learning Profile before taking the assessment."
    )

    st.page_link(
        "pages/1_Learning_Profile.py",
        label="Create Learning Profile",
        icon="➡️"
    )

    st.stop()


# --------------------------------------------------
# RETRIEVE QUESTIONS
# --------------------------------------------------

questions = get_quiz_questions("Basic Science")

if not questions:

    st.error(
        "No assessment questions were found. Please try again later."
    )

    st.stop()


# --------------------------------------------------
# ASSESSMENT INFORMATION
# --------------------------------------------------

total_questions = len(questions)

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.metric(
        "Total Questions",
        total_questions
    )

with info_col2:
    st.metric(
        "Subject",
        "Basic Science"
    )

st.write(
    "Choose the most appropriate answer for each question."
)

st.caption(
    "Please answer every question before submitting your assessment."
)

st.divider()


# --------------------------------------------------
# DISPLAY QUIZ
# --------------------------------------------------

with st.form("baseline_quiz_form"):

    answers = {}

    for index, question in enumerate(questions):

        question_id = question[0]
        question_text = question[2]

        options = {
            "A": question[3],
            "B": question[4],
            "C": question[5],
            "D": question[6]
        }

        with st.container(border=True):

            st.markdown(
                f"**QUESTION {index + 1} OF {total_questions}**"
            )

            st.subheader(question_text)

            selected_answer = st.radio(
                "Select your answer:",
                options=list(options.keys()),
                format_func=lambda key, opts=options: (
                    f"{key}. {opts[key]}"
                ),
                key=f"question_{question_id}",
                index=None
            )

            answers[question_id] = selected_answer

    st.write("")

    submitted = st.form_submit_button(
        "Submit Assessment",
        type="primary",
        use_container_width=True
    )


# --------------------------------------------------
# PROCESS SUBMISSION
# --------------------------------------------------

if submitted:

    unanswered = [
        question_id
        for question_id, answer in answers.items()
        if answer is None
    ]

    if unanswered:

        st.warning(
            f"You have {len(unanswered)} unanswered question(s). "
            "Please answer all questions before submitting."
        )

    else:

        try:

            result = save_quiz_attempt(
                profile_id,
                "Basic Science",
                answers
            )

            st.session_state["baseline_result"] = result

            st.success(
                "Your assessment has been saved successfully!"
            )

        except Exception as error:

            st.error(
                f"Unable to save assessment: {error}"
            )


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

if "baseline_result" in st.session_state:

    result = st.session_state["baseline_result"]

    st.divider()

    st.subheader("🎯 Your Assessment Results")

    st.write(
        "Here is a summary of your baseline assessment."
    )

    result_col1, result_col2, result_col3 = st.columns(3)

    with result_col1:

        st.metric(
            "Your Score",
            f"{result['score']}/{result['total_questions']}"
        )

    with result_col2:

        st.metric(
            "Accuracy",
            f"{result['accuracy']}%"
        )

    with result_col3:

        st.metric(
            "Attempt ID",
            result["attempt_id"]
        )

    st.progress(
        max(0.0, min(1.0, float(result["accuracy"]) / 100))
    )

    st.success(
        "Your baseline assessment is saved. "
        "LearnAble AI will use this result as an initial signal "
        "to personalise your learning experience."
    )

    st.write("")

    st.page_link(
        "pages/3_Personalised_Lesson.py",
        label="Continue to Personalised Learning",
        icon="➡️"
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "LearnAble AI | Every learner starts somewhere. "
    "Let's discover your next step."
)