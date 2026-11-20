import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Check Streamlit Cloud Secrets safely without throwing key errors
API_KEY = None
try:
    if "API_KEY" in st.secrets:
        API_KEY = st.secrets["API_KEY"]
    elif "GROQ_API_KEY" in st.secrets:
        API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

# Fallback to local environment variables if Secrets isn't available
if not API_KEY:
    API_KEY = os.getenv("API_KEY") or os.getenv("GROQ_API_KEY")

# Model available on this Groq account (from the app's own error message)
LLM_MODEL = "openai/gpt-oss-120b"

# Chunking settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Retrieval settings
TOP_K_RESULTS = 5

# Paths
UPLOAD_DIR = "uploads"
DOCUMENTS_DIR = "documents"
FAISS_INDEX_PATH = "faiss_index"

# App settings
APP_TITLE = "Askora"
APP_SUBTITLE = "Your Smart Academic Assistant"
