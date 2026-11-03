
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="LearnAble AI",
    page_icon="📚",
    layout="wide"
)

# Application heading
st.title("📚 LearnAble AI")
st.subheader("Learning that adapts to you.")

st.write(
    "An inclusive learning platform designed "
    "around every student's individual needs."
)

st.success("Welcome! Your learning journey starts here.")

# First section
st.header("Let's get to know you")
student_name = st.text_input("What should we call you?")

if st.button("Continue"):
    if student_name.strip():
        st.write(f"Welcome, {student_name}!")
    else:
        st.warning("Please enter your name.")
