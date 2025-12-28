import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

load_dotenv()

# Get API key from Streamlit secrets or environment variable
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ GOOGLE_API_KEY not found! Please configure it in Streamlit Cloud Secrets.")
    st.stop()

genai.configure(api_key=api_key)


# Function to get available model
@st.cache_resource
def get_available_model():
    """Find and return an available model that supports generateContent"""
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)

        if not available_models:
            st.error("No models available for content generation")
            return None

        # Prefer these models in order
        preferred_models = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-pro',
            'models/gemini-1.0-pro'
        ]

        # Try to use preferred model if available
        for preferred in preferred_models:
            if preferred in available_models:
                return preferred

        # Otherwise use the first available model
        return available_models[0]

    except Exception as e:
        st.error(f"Error fetching models: {str(e)}")
        return None


def get_gemini_response(input_text):
    try:
        model_name = get_available_model()
        if not model_name:
            return None

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(input_text)
        return response.text
    except Exception as e:
        st.error(f"Error calling Gemini API: {str(e)}")
        return None


def input_pdf_text(uploaded_file):
    try:
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in range(len(reader.pages)):
            page = reader.pages[page]
            text += str(page.extract_text())
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None


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

## Streamlit app
st.title("Smart ATS")
st.text("Improve Your Resume ATS")

# Show which model is being used
model_name = get_available_model()
if model_name:
    st.sidebar.success(f"Using model: {model_name}")

jd = st.text_area("Paste the Job Description")
uploaded_file = st.file_uploader("Upload Your Resume", type="pdf", help="Please upload the pdf")

submit = st.button("Submit")

if submit:
    if not jd:
        st.warning("⚠️ Please paste the job description")
    elif uploaded_file is None:
        st.warning("⚠️ Please upload a resume PDF file")
    else:
        with st.spinner("Analyzing your resume..."):
            text = input_pdf_text(uploaded_file)

            if text:
                formatted_prompt = input_prompt.format(text=text, jd=jd)
                response = get_gemini_response(formatted_prompt)

                if response:
                    st.subheader("Analysis Result:")
                    st.write(response)

                    # Try to parse and display as JSON for better formatting
                    try:
                        result = json.loads(response)
                        st.json(result)
                    except:
                        pass