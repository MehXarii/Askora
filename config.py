import os
from dotenv import load_dotenv

load_dotenv()

# Groq API
API_KEY = os.getenv("API_KEY")
LLM_MODEL = "openai/gpt-oss-20b"

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
