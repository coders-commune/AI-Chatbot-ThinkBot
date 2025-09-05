import streamlit as st 
import os
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables and configure Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Streamlit page setup
st.set_page_config(page_title="ThinkBot: AI Powered Tutor for Personalized Education", layout="wide")
st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# Store session data
if "history" not in st.session_state:
    st.session_state.history = []

if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""

if "image_data" not in st.session_state:
    st.session_state.image_data = None

# SIDEBAR
with st.sidebar:
    st.image("logo.jpg", width=90)
    st.title("ThinkBot: AI Powered Tutor for Personalized Education")

    if st.session_state.history:
        history_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in st.session_state.history])
        st.download_button("📥 Download Chat History", history_text, file_name="chat_history.txt")

# HEADER
logo = Image.open('logo.jpg')
c1, c2 = st.columns([0.9, 3.2])
with c1:
    st.caption('')
    st.image(logo, width=150)
with c2:
    st.title('ThinkBot : AI Powered Tutor for Personalized Education')

st.markdown("""
ThinkBot is an intelligent AI-powered tutoring system designed to revolutionize the way students learn. Leveraging advanced Retrieval-Augmented Generation (RAG) techniques, ThinkBot dynamically pulls relevant information from your uploaded course materials and delivers accurate, personalized responses to educational queries.
""")

# FILE UPLOAD SECTION
st.markdown("#### 📚 Upload Study Material")
doc_file = st.file_uploader("Upload PDF / DOCX / TXT", type=["pdf", "docx", "txt"])

def extract_text(file):
    if not file:
        return ""
    text = ""
    if file.name.endswith(".pdf"):
        pdf = PdfReader(file)
        for page in pdf.pages:
            text += page.extract_text() or ""
    elif file.name.endswith(".docx"):
        doc = Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file.name.endswith(".txt"):
        text = file.read().decode("utf-8")
    return text

# Save uploaded doc content in session
if doc_file:
    st.session_state.doc_text = extract_text(doc_file)

# IMAGE UPLOAD
st.markdown("#### 🖼️ Upload an Image")
image_file = st.file_uploader("Upload PNG / JPG / JPEG", type=["png", "jpg", "jpeg"])
if image_file:
    try:
        st.session_state.image_data = Image.open(image_file)
    except Exception as e:
        st.error(f"Error opening image: {str(e)}")

# CHAT SECTION
st.markdown("#### 💬 Ask a Question to ThinkBot")

# Show full history
for q, a in st.session_state.history:
    st.chat_message("user").markdown(q)
    st.chat_message("assistant").markdown(a)

# Input for new question
user_question = st.chat_input("Type your question here...")

if user_question:
    if not st.session_state.doc_text and not st.session_state.image_data:
        st.warning("⚠️ Please upload a course document or image before asking a question.")
    else:
        with st.spinner("Thinking..."):
            inputs = []
            if st.session_state.doc_text:
                inputs.append("Context from uploaded study material:\n" + st.session_state.doc_text)
            inputs.append(user_question)
            if st.session_state.image_data:
                inputs.append(st.session_state.image_data)

            try:
                response = model.generate_content(inputs)
                st.chat_message("user").markdown(user_question)
                st.chat_message("assistant").markdown(response.text)
                st.session_state.history.append((user_question, response.text))
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# QUIZ GENERATION
if len(st.session_state.history) >= 4:
    st.markdown("---")
    st.subheader("🧠 Practice Quiz")
    if st.button("Generate Quiz Based on My Questions"):
        with st.spinner("Generating quiz..."):
            user_questions = [q for q, _ in st.session_state.history]
            prompt = (
                "Create a short multiple-choice quiz (4-5 questions) based on the following student questions:\n\n"
                + "\n".join(f"- {q}" for q in user_questions)
                + "\n\nEach question should have 4 options (A, B, C, D) and indicate the correct answer clearly."
            )
            try:
                quiz_response = model.generate_content(prompt)
                st.markdown("#### 📝 Quiz")
                st.markdown(quiz_response.text)
            except Exception as e:
                st.error(f"❌ Quiz generation failed: {str(e)}")
