from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import tempfile
from pdfminer.high_level import extract_text
import google.generativeai as genai

# ---------------- CONFIG ----------------
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

# ---------------- GEMINI FUNCTION ----------------
def get_gemini_response(input_prompt, resume_text, jd_text):
    model = genai.GenerativeModel("models/gemini-1.5-flash")

    response = model.generate_content(
        [
            input_prompt,
            resume_text[:12000],  # safety limit
            jd_text
        ]
    )
    return response.text


# ---------------- PDF TEXT EXTRACTION ----------------
def input_pdf_setup(uploaded_file):
    if uploaded_file is None:
        raise FileNotFoundError("No file uploaded")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    text = extract_text(tmp_path)
    return text


# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="ATS Resume Expert", layout="centered")
st.header("📄 ATS Resume Tracking System")

input_text = st.text_area("📌 Job Description", height=200)
uploaded_file = st.file_uploader("📎 Upload your Resume (PDF only)", type=["pdf"])

if uploaded_file:
    st.success("✅ Resume uploaded successfully")

    submit1 = st.button("🔍 Resume Review")
    submit2 = st.button("📊 Percentage Match")

    input_prompt1 = """
    You are an experienced Technical Human Resource Manager.
    Review the resume against the job description.
    Highlight strengths, weaknesses, and overall suitability.
    """

    input_prompt2 = """
    You are an advanced ATS (Applicant Tracking System).
    Evaluate the resume against the job description.
    Output format:
    1. Match Percentage
    2. Missing Keywords
    3. Final ATS Verdict
    """

    if submit1 or submit2:
        resume_text = input_pdf_setup(uploaded_file)

        with st.spinner("Analyzing resume..."):
            if submit1:
                response = get_gemini_response(
                    input_prompt1, resume_text, input_text
                )
            else:
                response = get_gemini_response(
                    input_prompt2, resume_text, input_text
                )

        st.subheader("📌 Result")
        st.write(response)
