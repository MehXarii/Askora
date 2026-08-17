# Askora — AI Academic Assistant

> AI That Actually Reads With You

Askora is a RAG-based academic assistant that answers questions, generates quizzes, and summarizes topics directly from your uploaded course material.

## Features
- Context-aware Q&A with source citations
- Auto Quiz Generator (MCQs, 2/5/10 marks)
- Smart Summarizer (Detailed, Bullet Points, ELI5)
- Confidence scoring on every answer
- Supports PDF, DOCX, PPTX

## Tech Stack
- Python · Streamlit · Groq API · LLaMA 3.3 70B
- FAISS · Sentence Transformers · LangChain · PyMuPDF

## Architecture
RAG (Retrieval Augmented Generation) — documents are chunked, embedded with Sentence Transformers, indexed in FAISS, and retrieved semantically before LLaMA generates a grounded answer.

## Setup

1. Clone the repo
```bash
   git clone https://github.com/yourusername/askora.git
   cd askora
```

2. Install dependencies
```bash
   pip install -r requirements.txt
```

3. Add your API key — create a `.env` file:
API_KEY=your_groq_api_key_here


4. Run the app
```bash
   streamlit run app.py
```

## Project Structure

Askora/
├── app.py
├── config.py
├── requirements.txt
├── src/
│ ├── pdf_processor.py
│ ├── embeddings.py
│ ├── retriever.py
│ ├── quiz_generator.py
│ ├── summarizer.py
│ └── style.css


## Built By
Mehak Ansari — BSCS 6C, University of Central Punjab, Rawalpindi
Project Day 2026