import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import re

load_dotenv()

# Page config
st.set_page_config(
    page_title="Smart ATS Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .match-score {
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
        margin: 2rem 0;
    }
    .keyword-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.3rem;
        background-color: #f0f2f6;
        border-radius: 20px;
        border-left: 4px solid #ff4b4b;
    }
    .summary-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Get API key
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ GOOGLE_API_KEY not found! Please configure it in Streamlit Cloud Secrets.")
    st.stop()

genai.configure(api_key=api_key)


@st.cache_resource
def get_available_model():
    """Find and return an available model that supports generateContent"""
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)

        if not available_models:
            return None

        preferred_models = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-pro',
            'models/gemini-1.0-pro'
        ]

        for preferred in preferred_models:
            if preferred in available_models:
                return preferred

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


def extract_percentage(match_str):
    """Extract numeric percentage from string"""
    match = re.search(r'(\d+\.?\d*)', str(match_str))
    if match:
        return float(match.group(1))
    return 0


def display_results(response_text):
    """Display the analysis results in an attractive format"""
    try:
        # Try to parse as JSON
        result = json.loads(response_text)

        # Extract match percentage
        match_percentage = extract_percentage(result.get("JD Match", "0%"))

        # Display match score with color coding
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if match_percentage >= 70:
                color = "#00C851"
                emoji = "🎉"
                status = "Excellent Match!"
            elif match_percentage >= 50:
                color = "#ffbb33"
                emoji = "👍"
                status = "Good Match"
            elif match_percentage >= 30:
                color = "#ff8800"
                emoji = "⚠️"
                status = "Moderate Match"
            else:
                color = "#ff4444"
                emoji = "📉"
                status = "Needs Improvement"

            st.markdown(f"<div class='match-score' style='color: {color};'>{emoji} {match_percentage}%</div>",
                        unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; color: {color};'>{status}</h3>", unsafe_allow_html=True)

        st.markdown("---")

        # Two column layout for keywords and summary
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### 🔑 Missing Keywords")
            missing_keywords = result.get("MissingKeywords", [])

            if missing_keywords:
                st.markdown(f"**Found {len(missing_keywords)} missing keywords:**")
                for keyword in missing_keywords:
                    st.markdown(f'<div class="keyword-badge">❌ {keyword}</div>', unsafe_allow_html=True)
            else:
                st.success("✅ No missing keywords! Your resume covers all key requirements.")

        with col2:
            st.markdown("### 📝 Profile Summary & Recommendations")
            summary = result.get("Profile Summary", "")
            st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Action items
        st.markdown("### 🎯 Quick Action Items")
        if match_percentage < 70:
            st.info(
                "💡 **Tip:** Focus on adding the missing keywords naturally into your resume, especially in your skills and experience sections.")

        # Download section
        st.markdown("### 📥 Export Results")
        st.download_button(
            label="Download Analysis as JSON",
            data=json.dumps(result, indent=2),
            file_name="ats_analysis.json",
            mime="application/json"
        )

    except json.JSONDecodeError:
        # If JSON parsing fails, display raw text in a nice format
        st.markdown("### 📊 Analysis Results")
        st.markdown(f'<div class="summary-box">{response_text}</div>', unsafe_allow_html=True)


# Header
st.markdown('<h1 class="main-header">📄 Smart ATS Resume Analyzer</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Get instant feedback on how well your resume matches the job description</p>',
            unsafe_allow_html=True)

# Show model info in sidebar
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.info(
        "This tool uses AI to analyze your resume against job descriptions and provides actionable feedback to improve your chances.")

    model_name = get_available_model()
    if model_name:
        st.success(f"✅ AI Model: {model_name.split('/')[-1]}")

    st.markdown("### 📌 How to Use")
    st.markdown("""
    1. Paste the job description
    2. Upload your resume (PDF)
    3. Click Submit to analyze
    4. Review your match score and recommendations
    """)

# Main input area
col1, col2 = st.columns([1, 1])

with col1:
    jd = st.text_area(
        "📋 Job Description",
        height=300,
        placeholder="Paste the complete job description here...",
        help="Include all requirements, qualifications, and responsibilities"
    )

with col2:
    uploaded_file = st.file_uploader(
        "📤 Upload Your Resume",
        type="pdf",
        help="Upload your resume in PDF format"
    )

    if uploaded_file:
        st.success(f"✅ Uploaded: {uploaded_file.name}")

# Prompt Template
input_prompt = """
Hey Act Like a skilled or very experience ATS(Application Tracking System)
with a deep understanding of tech field,software engineering,data science,data analyst
and big data engineer. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide 
best assistance for improving the resumes. Assign the percentage Matching based 
on JD and the missing keywords with high accuracy.
resume:{text}
description:{jd}

I want the response in one single string having the structure
{{"JD Match":"%","MissingKeywords":[],"Profile Summary":""}}
"""

# Submit button (centered)
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    submit = st.button("🚀 Analyze Resume", type="primary", use_container_width=True)

if submit:
    if not jd:
        st.warning("⚠️ Please paste the job description")
    elif uploaded_file is None:
        st.warning("⚠️ Please upload your resume")
    else:
        with st.spinner("🔍 Analyzing your resume... This may take a moment."):
            text = input_pdf_text(uploaded_file)

            if text:
                formatted_prompt = input_prompt.format(text=text, jd=jd)
                response = get_gemini_response(formatted_prompt)

                if response:
                    st.markdown("---")
                    st.markdown("## 📊 Analysis Results")
                    display_results(response)