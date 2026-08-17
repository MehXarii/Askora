from groq import Groq
from config import API_KEY, LLM_MODEL, TOP_K_RESULTS
from src.embeddings import search_index

client = Groq(api_key=API_KEY)


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
        error_type = type(e).__name__
        if "Connection" in error_type or "timeout" in str(e).lower():
            return {
                "error": True,
                "message": "🌐 Connection Error: Unable to reach the AI service. Please check your internet connection and try again."
            }
        elif "rate_limit" in str(e).lower() or "429" in str(e):
            return {
                "error": True,
                "message": "⏱️ Rate Limit: Too many requests. Please wait a moment and try again."
            }
        elif "authentication" in str(e).lower() or "401" in str(e) or "invalid" in str(e).lower():
            return {
                "error": True,
                "message": "🔑 Authentication Error: Invalid API key. Please check your .env file and restart the app."
            }
        else:
            return {
                "error": True,
                "message": f"⚠️ Error: {str(e)[:100]}"
            }

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
        "answer": response.choices[0].message.content,
        "sources": sources,
        "confidence": confidence
    }