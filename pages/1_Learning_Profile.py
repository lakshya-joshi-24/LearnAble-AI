import streamlit as st

from database.db import initialize_database, save_profile


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="My Learning Profile | LearnAble AI",
    page_icon="👤",
    layout="wide"
)


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

initialize_database()


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

    .profile-banner {
        background: linear-gradient(120deg, #6C63FF, #8B5CF6);
        padding: 28px 32px;
        border-radius: 18px;
        margin: 12px 0 24px 0;
    }

    .profile-banner h2 {
        color: #FFFFFF !important;
        font-size: 26px;
        margin-bottom: 8px;
    }

    .profile-banner p {
        color: #F3F0FF !important;
        font-size: 15px;
        margin-bottom: 0;
    }

    .section-description {
        color: #64748B !important;
        font-size: 14px;
        margin-top: -8px;
        margin-bottom: 18px;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 15px;
        border-color: #E5E7EB;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        min-height: 44px;
    }

    div[data-testid="stCheckbox"] label {
        color: #1F2937 !important;
    }

    hr {
        border-color: #E5E7EB;
    }

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR
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

    st.caption("Personalise your learning experience.")


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("My Learning Profile")

st.markdown("""
<div class="profile-banner">
    <h2>Let's personalise your learning! 👋</h2>
    <p>
        Everyone learns differently. Tell us what works best for you
        so LearnAble AI can adapt your learning experience.
    </p>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# PROFILE FORM
# --------------------------------------------------

with st.container(border=True):

    st.subheader("1. About You")

    st.markdown(
        '<p class="section-description">'
        'A few basic details to personalise your experience.'
        '</p>',
        unsafe_allow_html=True
    )

    name = st.text_input(
        "What should we call you?",
        placeholder="Enter your name"
    )

    age_group = st.selectbox(
        "Select your age group",
        [
            "Under 13",
            "13–17",
            "18–24",
            "25 and above"
        ]
    )


st.write("")


with st.container(border=True):

    st.subheader("2. Learning Preferences")

    st.markdown(
        '<p class="section-description">'
        'Choose how you understand and process information best.'
        '</p>',
        unsafe_allow_html=True
    )

    learning_style = st.radio(
        "How do you prefer to learn?",
        [
            "Visual explanations",
            "Reading text",
            "Listening to audio",
            "Step-by-step explanations"
        ],
        horizontal=False
    )

    language_level = st.select_slider(
        "Preferred explanation complexity",
        options=[
            "Very simple",
            "Simple",
            "Moderate",
            "Detailed"
        ],
        value="Simple"
    )

    learning_pace = st.radio(
        "What learning pace suits you?",
        [
            "Slow and steady",
            "Normal",
            "Self-paced"
        ],
        horizontal=True
    )


st.write("")


with st.container(border=True):

    st.subheader("3. Accessibility Settings")

    st.markdown(
        '<p class="section-description">'
        'Adjust the learning experience to make content more comfortable.'
        '</p>',
        unsafe_allow_html=True
    )

    font_size = st.select_slider(
        "Preferred text size",
        options=[
            "Small",
            "Medium",
            "Large",
            "Extra Large"
        ],
        value="Medium"
    )

    accessibility_col1, accessibility_col2 = st.columns(2)

    with accessibility_col1:

        text_to_speech = st.checkbox(
            "🔊 Enable text-to-speech",
            value=False
        )

    with accessibility_col2:

        reduced_animations = st.checkbox(
            "♿ Prefer reduced animations",
            value=False
        )


# --------------------------------------------------
# SAVE PROFILE
# --------------------------------------------------

st.write("")

st.markdown("### Ready to personalise your learning?")

st.caption(
    "You can update your preferences by saving a new profile."
)

if st.button(
    "Save My Preferences",
    type="primary",
    use_container_width=True
):

    if not name.strip():

        st.warning("Please enter your name before saving your profile.")

    else:

        profile = {
            "name": name.strip(),
            "age_group": age_group,
            "learning_style": learning_style,
            "language_level": language_level,
            "learning_pace": learning_pace,
            "font_size": font_size,
            "text_to_speech": text_to_speech,
            "reduced_animations": reduced_animations
        }

        profile_id = save_profile(profile)

        st.session_state["student_profile"] = profile
        st.session_state["profile_id"] = profile_id

        st.success(
            f"Great, {name.strip()}! Your learning preferences have been saved."
        )

        st.divider()

        st.subheader("Your Profile Summary")

        summary_col1, summary_col2 = st.columns(2)

        with summary_col1:

            st.markdown("**Basic Information**")

            st.write(f"Name: {profile['name']}")
            st.write(f"Age Group: {profile['age_group']}")

            st.markdown("**Learning Preferences**")

            st.write(f"Learning Style: {profile['learning_style']}")
            st.write(f"Explanation Level: {profile['language_level']}")
            st.write(f"Learning Pace: {profile['learning_pace']}")

        with summary_col2:

            st.markdown("**Accessibility Settings**")

            st.write(f"Text Size: {profile['font_size']}")

            st.write(
                "Text-to-Speech: "
                + ("Enabled" if profile["text_to_speech"] else "Disabled")
            )

            st.write(
                "Reduced Animations: "
                + ("Enabled" if profile["reduced_animations"] else "Disabled")
            )

        st.caption(f"Profile ID: {profile_id}")

        st.divider()

        st.info(
            "Your profile is ready. Continue to the baseline assessment "
            "to begin your personalised learning journey."
        )

        st.page_link(
            "pages/2_Baseline_Assessment.py",
            label="Continue to Baseline Assessment",
            icon="➡️"
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "LearnAble AI | Your learning journey, your pace, your way."
)