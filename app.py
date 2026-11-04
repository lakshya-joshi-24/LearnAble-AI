import streamlit as st

from database.db import (
    get_latest_profile,
    get_connection,
    initialize_database
)
from engines.learner_model import get_learning_recommendations


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="LearnAble AI | Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)
initialize_database()

# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown("""
<style>

    /* Main application */
    .stApp {
        background-color: #F8FAFC;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Main text */
    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp p,
    .stApp label {
        color: #1F2937;
    }

    /* Sidebar */
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

    /* Welcome section */
    .welcome-card {
        background: linear-gradient(120deg, #6C63FF, #8B5CF6);
        padding: 30px 34px;
        border-radius: 18px;
        margin: 12px 0 24px 0;
    }

    .welcome-card h2 {
        color: #FFFFFF !important;
        font-size: 28px;
        margin-bottom: 8px;
    }

    .welcome-card p {
        color: #F3F0FF !important;
        font-size: 16px;
        margin-bottom: 0;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 18px 20px;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] {
        color: #1F2937 !important;
    }

    /* Buttons */
    .stButton > button,
    [data-testid="stPageLink"] a {
        border-radius: 10px;
        font-weight: 600;
    }

    /* Links */
    a {
        color: #6C63FF;
    }

    /* Divider */
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

    st.caption("Your learning journey, your pace, your way.")


# --------------------------------------------------
# PROFILE RETRIEVAL
# --------------------------------------------------

profile_id = st.session_state.get("profile_id")

if profile_id:

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM student_profiles WHERE id = ?",
            (profile_id,)
        )

        profile = cursor.fetchone()

    finally:
        connection.close()

else:
    profile = get_latest_profile()


# --------------------------------------------------
# DASHBOARD HEADER
# --------------------------------------------------

st.title("Dashboard")

st.caption("Your personalised learning space.")


# --------------------------------------------------
# DASHBOARD CONTENT
# --------------------------------------------------

if profile:

    student_name = profile[1]

    # Welcome section
    st.markdown(f"""
    <div class="welcome-card">
        <h2>Welcome back, {student_name}! 👋</h2>
        <p>Keep learning, keep growing. Your next step starts here.</p>
    </div>
    """, unsafe_allow_html=True)


    # Learning preferences
    st.subheader("Your Learning Preferences")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Learning Style",
            profile[3]
        )

    with col2:
        st.metric(
            "Explanation Level",
            profile[4]
        )

    with col3:
        st.metric(
            "Learning Pace",
            profile[5]
        )


    # Recommendations
    learning_profile = {
        "learning_style": profile[3],
        "learning_pace": profile[5]
    }

    recommendations = get_learning_recommendations(
        profile[0],
        learning_profile
    )


    st.divider()

    st.subheader("🧠 Your Learning Insights")

    if recommendations["status"] == "Ready":

        result_col1, result_col2, result_col3 = st.columns(3)

        with result_col1:
            st.metric(
                "Knowledge Level",
                recommendations["knowledge_level"]
            )

        with result_col2:
            st.metric(
                "Quiz Accuracy",
                f"{recommendations['accuracy']}%"
            )

        with result_col3:
            st.metric(
                "Recommended Level",
                recommendations["recommended_complexity"]
            )


        st.subheader("Your Teaching Strategy")

        strategy_col1, strategy_col2 = st.columns(2)

        with strategy_col1:
            st.info(
                f"**Learning Approach**\n\n"
                f"{recommendations['teaching_approach']}"
            )

        with strategy_col2:
            st.info(
                f"**Learning Pace**\n\n"
                f"{recommendations['pace_strategy']}"
            )


        # Concepts requiring practice
        st.subheader("Concepts to Practise")

        concepts = recommendations["concepts_to_practice"]

        if concepts:

            concept_cols = st.columns(
                min(len(concepts), 3)
            )

            for index, concept in enumerate(concepts):

                with concept_cols[index % len(concept_cols)]:
                    st.warning(f"📖 {concept}")

        else:
            st.success(
                "No concepts are currently flagged for additional practice."
            )

    else:

        st.info(recommendations["message"])


    # Learning actions
    st.divider()

    st.subheader("Continue Your Learning Journey")

    st.write(
        "Choose your next step to continue building your knowledge."
    )

    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:
        with st.container(border=True):
            st.markdown("### 👤 My Profile")
            st.write(
                "Manage your learning preferences and accessibility settings."
            )
            st.page_link(
                "pages/1_Learning_Profile.py",
                label="View Profile",
                icon="➡️"
            )

    with action_col2:
        with st.container(border=True):
            st.markdown("### 📝 Assessment")
            st.write(
                "Evaluate your existing knowledge and learning level."
            )
            st.page_link(
                "pages/2_Baseline_Assessment.py",
                label="Start Assessment",
                icon="➡️"
            )

    with action_col3:
        with st.container(border=True):
            st.markdown("### 📖 Learn & Practise")
            st.write(
                "Explore topics through personalised lessons and activities."
            )
            st.page_link(
                "pages/3_Personalised_Lesson.py",
                label="Start Learning",
                icon="➡️"
            )


else:

    st.markdown("""
    <div class="welcome-card">
        <h2>Welcome to LearnAble AI! 👋</h2>
        <p>Your learning journey, your pace, your way.</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(
        "You haven't created a learning profile yet. "
        "Create your profile to get started with personalised learning."
    )

    st.page_link(
        "pages/1_Learning_Profile.py",
        label="Create My Learning Profile",
        icon="➡️"
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "LearnAble AI | Inclusive learning, personalised for everyone."
)