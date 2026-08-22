# Askora — AI Academic Assistant

> AI That Actually Reads With You

🔗 **Live Demo:** https://askora-chatbot.streamlit.app/

---

## Overview

**Askora** is an AI-powered academic assistant built with **Python and Streamlit**. It uses a **Retrieval-Augmented Generation (RAG)** workflow to help students interact with their own course material — answering questions, generating quizzes, and summarizing topics with source citations.

---

## Key Features

- **Context-Aware Q&A** — Ask anything from your uploaded documents, get cited answers
- **Auto Quiz Generator** — MCQs and marks-based questions (2, 5, 10 marks) from your material
- **Smart Summarizer** — Detailed, Bullet Points, or ELI5 summaries on any topic
- **Confidence Scoring** — Every answer comes with a relevance confidence bar
- **Citation-Based Answers** — Shows exact source file and page number
- **Multi-Document Search** — Upload and search across multiple files at once
- **Supports PDF, DOCX, PPTX** — The three most common student file formats

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Web application interface |
| Groq API | Fast LLM inference engine |
| GPT OSS 20B | Large language model (via Groq) |
| FAISS | Vector similarity search |
| Sentence Transformers | Text embeddings (all-MiniLM-L6-v2) |
| LangChain | Document loading and chunking |
| PyMuPDF | PDF text extraction |
| Tesseract OCR | Fallback for scanned PDFs |

---

## How It Works

Academic Documents (PDF / DOCX / PPTX)
↓
Text Extraction (PyMuPDF / python-docx)
↓
Chunking (LangChain RecursiveCharacterTextSplitter)
↓
Embeddings (Sentence Transformers — all-MiniLM-L6-v2)
↓
FAISS Vector Index (cosine similarity)
↓
Semantic Retrieval (top-k relevant chunks)
↓
GPT OSS 20B via Groq API
↓
Answer + Confidence Score + Source Citation


---

## Project Structure

Askora/
│
├── app.py
├── config.py
├── requirements.txt
├── packages.txt
├── .gitignore
├── README.md
│
├── .streamlit/
│ └── config.toml
│
├── screenshots/
│ ├── interface.png
│ ├── ask.png
│ ├── quiz.png
│ └── summarizer.png
│
└── src/
├── init.py
├── embeddings.py
├── pdf_processor.py
├── quiz_generator.py
├── retriever.py
├── summarizer.py
└── style.css


---

## Application Screenshots

### Main Interface
![Askora Interface](screenshots/interface.png)

### Ask Questions
![Askora Question Answering](screenshots/ask.png)

### Quiz Generator
![Askora Quiz Generator](screenshots/quiz.png)

### Summarizer
![Askora Summarizer](screenshots/summarizer.png)

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/MehXarii/Askora.git
cd Askora
```

### 2. Create a virtual environment

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:
```env
API_KEY=your_groq_api_key_here
```

Get your free Groq API key at [console.groq.com](https://console.groq.com)

Do **not** commit your `.env` file to GitHub.

### 5. Run the application
```bash
streamlit run app.py
```

---

## Deployment

Deployed on **Streamlit Cloud**.

To deploy your own instance:
1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add your `API_KEY` in Streamlit Secrets
5. Deploy

---

## Use Cases

- Exam preparation from lecture notes
- Generating practice quizzes instantly
- Understanding complex topics through ELI5 summaries
- Searching across multiple course PDFs at once
- Revision before exams

---

## Security

API credentials are stored in environment variables and excluded from version control via `.gitignore`. Never commit API keys to GitHub.

---

## Future Improvements

- Multi-language support
- Voice input for questions
- Export quiz as PDF
- User authentication
- Advanced study analytics
- Personalized learning recommendations

---

## Author

**Mehak Ansari**
BSCS Student | AI & Computer Science
University of Central Punjab, Rawalpindi

GitHub: [@MehXarii](https://github.com/MehXarii)

---
## License

This project is available for educational and portfolio purposes.
