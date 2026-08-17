from groq import Groq
from config import API_KEY, LLM_MODEL
from src.embeddings import search_index

client = Groq(api_key=API_KEY)

SUMMARY_MODES = {
    "Detailed": "Give a thorough academic summary with all key concepts explained clearly.",
    "Bullet Points": "Summarize in clean bullet points covering all main ideas.",
    "ELI5": "Explain this like I am 10 years old, using very simple language and analogies."
}


def summarize_topic(topic: str, index, chunks: list[dict], mode: str = "Detailed") -> dict:
    relevant_chunks = search_index(topic, index, chunks, top_k=8)

    if not relevant_chunks:
        return {
            "error": False,
            "text": "I couldn't find enough information about this topic in the uploaded documents."
        }

    context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])
    instruction = SUMMARY_MODES.get(mode, SUMMARY_MODES["Detailed"])

    prompt = f"""You are Askora, a smart academic assistant.
{instruction}

Topic: {topic}

Context from uploaded documents:
{context}

Summary:"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "error": False,
            "text": response.choices[0].message.content
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