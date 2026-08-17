from groq import Groq
import json
from config import API_KEY, LLM_MODEL
from src.embeddings import search_index

client = Groq(api_key=API_KEY)


def safe_json_parse(text: str) -> list[dict]:
    """Safely extract and parse JSON from text with markdown code blocks."""
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return []


def generate_mcqs(topic: str, index, chunks: list[dict], num_questions: int = 5) -> dict:
    relevant_chunks = search_index(topic, index, chunks, top_k=8)
    context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])

    prompt = f"""You are an academic quiz generator. Based on the context below, generate exactly {num_questions} multiple choice questions.

Context:
{context}

Return ONLY a JSON array in this exact format, nothing else:
[
  {{
    "question": "Question text here?",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    }},
    "correct": "A",
    "explanation": "Brief explanation why this is correct"
  }}
]"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.choices[0].message.content.strip()
        questions = safe_json_parse(text)
        
        if not questions:
            return {
                "error": True,
                "message": "⚠️ Quiz Generation Failed: Could not parse the response. Please try again."
            }
        
        return {
            "error": False,
            "questions": questions
        }
    except Exception as e:
        error_type = type(e).__name__
        if "Connection" in error_type or "timeout" in str(e).lower():
            return {
                "error": True,
                "message": "🌐 Connection Error: Unable to reach the AI service. Please check your internet and try again."
            }
        elif "rate_limit" in str(e).lower() or "429" in str(e):
            return {
                "error": True,
                "message": "⏱️ Rate Limit: Too many requests. Please wait a moment and try again."
            }
        elif "authentication" in str(e).lower() or "401" in str(e):
            return {
                "error": True,
                "message": "🔑 Authentication Error: Invalid API key. Please check your .env file."
            }
        else:
            return {
                "error": True,
                "message": f"⚠️ Error: {str(e)[:80]}"
            }


def generate_marks_based_questions(topic: str, index, chunks: list[dict], marks: int, num_questions: int = 3) -> dict:
    relevant_chunks = search_index(topic, index, chunks, top_k=10)
    context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])

    if marks == 2:
        detail_instruction = "Each answer should be 2-3 sentences. Focus on definitions and key concepts."
    elif marks == 5:
        detail_instruction = "Each answer should be a well-structured paragraph of 5-7 sentences. Include explanation, examples, and key points."
    else:
        detail_instruction = "Each answer should be a comprehensive, exam-quality response of 10-15 sentences. Include introduction, detailed explanation, examples, diagrams description if needed, and conclusion."

    prompt = f"""You are an academic exam question generator. Based on the context below, generate exactly {num_questions} questions worth {marks} marks each.

Context:
{context}

Instructions for answers: {detail_instruction}

Return ONLY a JSON array in this exact format, nothing else:
[
  {{
    "question": "Question text here?",
    "marks": {marks},
    "answer": "Detailed answer here based on context",
    "key_points": ["Key point 1", "Key point 2", "Key point 3"]
  }}
]"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.choices[0].message.content.strip()
        questions = safe_json_parse(text)
        
        if not questions:
            return {
                "error": True,
                "message": f"⚠️ Quiz Generation Failed: Could not parse the response. Please try again."
            }
        
        return {
            "error": False,
            "questions": questions
        }
    except Exception as e:
        error_type = type(e).__name__
        if "Connection" in error_type or "timeout" in str(e).lower():
            return {
                "error": True,
                "message": "🌐 Connection Error: Unable to reach the AI service. Please check your internet and try again."
            }
        elif "rate_limit" in str(e).lower() or "429" in str(e):
            return {
                "error": True,
                "message": "⏱️ Rate Limit: Too many requests. Please wait a moment and try again."
            }
        elif "authentication" in str(e).lower() or "401" in str(e):
            return {
                "error": True,
                "message": "🔑 Authentication Error: Invalid API key. Please check your .env file."
            }
        else:
            return {
                "error": True,
                "message": f"⚠️ Error: {str(e)[:80]}"
            }