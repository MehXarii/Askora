import json
import re

from config import LLM_MODEL
from src.embeddings import search_index
from src.retriever import get_groq_client, describe_groq_error, build_context, make_snippet


def _parse_cards(text: str) -> list:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No card list found.")
    cards = json.loads(text[start:end + 1])
    return [c for c in cards if isinstance(c, dict) and c.get("front") and c.get("back")]


def _sources(chunks: list) -> list:
    out, seen = [], set()
    for chunk in chunks:
        name = chunk["source"].split("\\")[-1].split("/")[-1]
        key = f"{name}-{chunk['page']}"
        if key not in seen:
            seen.add(key)
            out.append({"source": name, "page": chunk["page"], "snippet": make_snippet(chunk["text"])})
    return out


def _retrieve(topic, index, chunks):
    client = get_groq_client()
    if client is None:
        return None, None, {"error": True, "message": "No API key found. Add API_KEY to your Streamlit Secrets, save, and reboot the app."}
    relevant = search_index(topic, index, chunks, top_k=8)
    if not relevant:
        return None, None, {"error": True, "message": "I could not find this topic in the uploaded documents."}
    return client, relevant, None


def generate_flashcards(topic: str, num_cards: int, index, chunks: list) -> dict:
    client, relevant, err = _retrieve(topic, index, chunks)
    if err:
        return err

    system_prompt = f"""You help a student memorize slides for an exam.
Using ONLY the material provided, create {num_cards} flashcards.
- "front": a short question or prompt, such as "List the layers of the OSI model" or "Define deadlock".
- "back": the answer in the same wording the slides use, kept short. Lists should be numbered.
Reply with only a JSON array like [{{"front": "...", "back": "..."}}] and nothing else."""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Topic: {topic}\n\nMaterial:\n{build_context(relevant)}"},
            ],
            temperature=0.2,
        )
        cards = _parse_cards(response.choices[0].message.content)
    except (ValueError, json.JSONDecodeError):
        return {"error": True, "message": "The flashcards came back in an unreadable format. Please try again."}
    except Exception as e:
        return {"error": True, "message": describe_groq_error(e, client)}

    if not cards:
        return {"error": True, "message": "No flashcards could be made from this topic. Try a broader topic."}
    return {"error": False, "cards": cards, "sources": _sources(relevant)}


def generate_revision_sheet(topic: str, index, chunks: list) -> dict:
    client, relevant, err = _retrieve(topic, index, chunks)
    if err:
        return err

    system_prompt = """You prepare one-page exam revision sheets for a student who has to memorize slides.
Using ONLY the material provided, write in Markdown with these sections:
## Key Definitions
(exact wording from the slides)
## Lists and Steps to Memorize
(numbered lists, in the slide order)
## Comparisons
(short bullet comparisons where the slides contrast two things)
## Likely Exam Questions
(5 questions a teacher could ask from this material)
Keep it compact enough to fit on one printed page. Do not add facts that are not in the material."""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Topic: {topic}\n\nMaterial:\n{build_context(relevant)}"},
            ],
            temperature=0.2,
        )
        sheet = (response.choices[0].message.content or "").strip()
    except Exception as e:
        return {"error": True, "message": describe_groq_error(e, client)}

    if not sheet:
        return {"error": True, "message": "The model returned an empty sheet. Please try again."}
    return {"error": False, "sheet": sheet, "sources": _sources(relevant)}