import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Read API_KEY or GROQ_API_KEY from local .env or Streamlit Secrets
API_KEY = (
    os.getenv("API_KEY") 
    or os.getenv("GROQ_API_KEY") 
    or st.secrets.get("API_KEY") 
    or st.secrets.get("GROQ_API_KEY")
)

LLM_MODEL = "llama-3.3-70b-versatile"

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