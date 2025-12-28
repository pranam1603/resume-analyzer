import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

load_dotenv()  ## load all our environment variables

# Get API key from Streamlit secrets or environment variable
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ GOOGLE_API_KEY not found! Please configure it in Streamlit Cloud Secrets.")
    st.stop()

genai.configure(api_key=api_key)


def get_gemini_response(input):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(input)
        return response.text
    except Exception as e:
        st.error(f"Error calling Gemini API: {str(e)}")
        return None


def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text


# Prompt Template
input_prompt = """
Hey Act Like a skilled or very experience ATS(Application Tracking System)
with a deep understanding of tech field,software engineering,data science ,data analyst
and big data engineer. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide 
best assistance for improving the resumes. Assign the percentage Matching based 
on Jd and the missing keywords with high accuracy
resume:{text}
description:{jd}

I want the response in one single string having the structure
{{"JD Match":"%","MissingKeywords":[],"Profile Summary":""}}
"""

## streamlit app
st.title("Smart ATS")
st.text("Improve Your Resume ATS")
jd = st.text_area("Paste the Job Description")
uploaded_file = st.file_uploader("Upload Your Resume", type="pdf", help="Please upload the pdf")

submit = st.button("Submit")

if submit:
    if uploaded_file is not None and jd:
        with st.spinner("Analyzing your resume..."):
            text = input_pdf_text(uploaded_file)
            formatted_prompt = input_prompt.format(text=text, jd=jd)
            response = get_gemini_response(formatted_prompt)

            if response:
                st.subheader("Analysis Result:")
                st.write(response)
    elif uploaded_file is None:
        st.warning("⚠️ Please upload a resume PDF file")
    elif not jd:
        st.warning("⚠️ Please paste the job description")