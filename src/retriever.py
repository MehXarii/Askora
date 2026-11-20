import os
import streamlit as st
import groq
from groq import Groq
from config import API_KEY, LLM_MODEL, TOP_K_RESULTS
from src.embeddings import search_index


def _clean_key(key):
    """Remove stray spaces, newlines and quotes that often sneak in when pasting."""
    if not key:
        return None
    return str(key).strip().strip('"').strip("'").strip()


def resolve_api_key():
    key = _clean_key(API_KEY)
    if not key:
        try:
            for name in ("API_KEY", "GROQ_API_KEY"):
                if name in st.secrets:
                    key = _clean_key(st.secrets[name])
                    break
        except Exception:
            pass
    if not key:
        key = _clean_key(os.getenv("API_KEY") or os.getenv("GROQ_API_KEY"))
    return key


def get_groq_client():
    key = resolve_api_key()
    if not key:
        return None
    return Groq(api_key=key)


def list_chat_models(client) -> list:
    """Ask Groq which models this key can actually use."""
    try:
        models = client.models.list()
        ids = [m.id for m in models.data]
        skip = ("whisper", "orpheus", "guard", "tts")
        return [i for i in ids if not any(s in i.lower() for s in skip)]
    except Exception:
        return []


def describe_groq_error(e: Exception, client) -> str:
    if isinstance(e, groq.AuthenticationError):
        key = resolve_api_key() or ""
        return (
            f"Groq rejected the API key (401). The key the app loaded is {len(key)} "
            f"characters long and starts with {key[:4]!r}. A valid Groq key starts with 'gsk_'. "
            "Create a new key at console.groq.com, paste it into Streamlit Secrets as "
            'API_KEY = "gsk_..." on a single line, save, then reboot the app.'
        )
    if isinstance(e, groq.NotFoundError):
        available = list_chat_models(client)
        msg = f"The model '{LLM_MODEL}' is not available on this Groq account (404)."
        if available:
            msg += (
                " Models your key can use: " + ", ".join(available[:12])
                + ". Copy one into LLM_MODEL in config.py."
            )
        return msg
    if isinstance(e, groq.PermissionDeniedError):
        return "Your Groq account is not allowed to use this model (403). Choose another model in config.py."
    if isinstance(e, groq.RateLimitError):
        return "Rate limit reached (429). Wait a minute and try again."
    if isinstance(e, (groq.APIConnectionError, groq.APITimeoutError)):
        return "Could not reach Groq. Check the internet connection and try again."
    if isinstance(e, groq.BadRequestError):
        return f"Groq rejected the request (400): {str(e)[:200]}"
    return f"Unexpected error ({type(e).__name__}): {str(e)[:200]}"


def build_context(chunks: list[dict]) -> str:
    context_parts = []
    for chunk in chunks:
        source = chunk["source"].split("\\")[-1].split("/")[-1]
        context_parts.append(
            f"[Source: {source} | Page {chunk['page']}]\n{chunk['text']}"
        )
    return "\n\n---\n\n".join(context_parts)


def make_snippet(text: str, max_words: int = 35) -> str:
    """Create a short preview snippet from a chunk's text."""
    words = text.strip().split()
    snippet = " ".join(words[:max_words])
    if len(words) > max_words:
        snippet += "..."
    return snippet


def calculate_confidence(chunks: list[dict]) -> dict:
    """Convert cosine similarity score into a clean 0-100 confidence percentage with color."""
    if not chunks:
        return {"label": "Low relevance", "percentage": 15, "color": "red"}

    avg_score = sum(chunk["score"] for chunk in chunks) / len(chunks)
    percentage = max(10, min(98, int((avg_score / 0.65) * 100)))

    if percentage >= 60:
        label = "High relevance"
        color = "green"
    elif percentage >= 35:
        label = "Moderate relevance"
        color = "orange"
    else:
        label = "Low relevance"
        color = "red"

    return {"label": label, "percentage": percentage, "color": color}


def build_chat_history_messages(chat_history: list[dict]) -> list[dict]:
    messages = []
    for chat in chat_history[-6:]:
        messages.append({"role": "user", "content": chat["question"]})
        messages.append({"role": "assistant", "content": chat["answer"]})
    return messages


def answer_question(query: str, index, chunks: list[dict], chat_history: list[dict] = None) -> dict:
    client = get_groq_client()
    if client is None:
        return {
            "error": True,
            "message": "No API key found. Add API_KEY to your Streamlit Secrets, save, and reboot the app."
        }

    relevant_chunks = search_index(query, index, chunks, top_k=TOP_K_RESULTS)

    if not relevant_chunks:
        return {
            "error": False,
            "answer": "I couldn't find relevant information in the uploaded documents.",
            "sources": [],
            "confidence": {"label": "Low relevance", "percentage": 10, "color": "red"}
        }

    context = build_context(relevant_chunks)
    confidence = calculate_confidence(relevant_chunks)

    system_prompt = """You are Askora, a smart academic assistant. Answer the student's question 
using ONLY the context provided. If the answer is not in the context, 
say "I don't have enough information in the uploaded documents to answer this."
Answer clearly and in an academic tone. You remember the conversation history 
and can refer back to previous questions and answers."""

    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        messages.extend(build_chat_history_messages(chat_history))

    messages.append({
        "role": "user",
        "content": f"""Context from uploaded documents:
{context}

Current Question: {query}"""
    })

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages
        )
    except Exception as e:
        return {"error": True, "message": describe_groq_error(e, client)}

    sources = []
    seen = set()
    for chunk in relevant_chunks:
        source_name = chunk["source"].split("\\")[-1].split("/")[-1]
        key = f"{source_name}-{chunk['page']}"
        if key not in seen:
            seen.add(key)
            sources.append({
                "source": source_name,
                "page": chunk["page"],
                "snippet": make_snippet(chunk["text"])
            })

    return {
        "error": False,
        "answer": response.choices[0].message.content or "The model returned an empty answer. Please try again.",
        "sources": sources,
        "confidence": confidence
    }