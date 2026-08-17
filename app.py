import streamlit as st
import os
import shutil
import base64
from config import APP_TITLE, APP_SUBTITLE, UPLOAD_DIR, FAISS_INDEX_PATH
from src.pdf_processor import process_file
from src.embeddings import build_faiss_index, load_faiss_index, index_exists
from src.retriever import answer_question
from src.quiz_generator import generate_mcqs, generate_marks_based_questions
from src.summarizer import summarize_topic, SUMMARY_MODES


def load_css(path: str):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Custom professional geometric "A" logo for ASKORA
RAW_SVG = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" fill="#1E3A8A" rx="22"/>
  <g fill="#FFFFFF">
    <path d="M50,16 C47.5,16 45.2,17.4 44.1,19.6 L18.6,65.6 C17.1,68.3 19.1,71.6 22.2,71.6 L34.5,71.6 C37.8,71.6 39.7,68.9 40.5,66.1 L46.2,46.5 C46.8,44.2 49.5,43.2 51.5,44.7 C54.3,46.7 54.8,50.7 52.6,53.3 L42.8,64.8 C40.8,67.2 42.5,70.8 45.6,70.8 L77.8,70.8 C80.9,70.8 82.9,67.5 81.4,64.8 L55.9,19.6 C54.8,17.4 52.5,16 50,16 Z M50,30 L66,60 L54,60 C51.5,60 49.5,58 49.5,55.5 C49.5,54.2 50.1,53.1 51,52.3 L44,40 Z"/>
  </g>
</svg>"""

# Convert SVG to Base64 to safely embed as Favicon and Sidebar Image
B64_SVG = base64.b64encode(RAW_SVG.encode("utf-8")).decode("utf-8")
SVG_DATA_URI = f"data:image/svg+xml;base64,{B64_SVG}"

st.set_page_config(
    page_title="Askora",
    page_icon=SVG_DATA_URI,
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css("src/style.css")

# Main Page Header - Tagline structured underneath the brand name
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:16px; padding-bottom:8px;">
        <img src="{SVG_DATA_URI}" width="46" style="border-radius:8px;"/>
        <div>
            <div style="font-size:1.85rem; font-weight:800; letter-spacing:-0.03em; color:#1E3A8A; line-height:1.1;">ASKORA</div>
            <div style="font-size:0.82rem; color:#64748B; font-weight:500; letter-spacing:0.02em; margin-top:3px;">AI That Actually Reads With You</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

if "index" not in st.session_state:
    st.session_state.index = None
if "chunks" not in st.session_state:
    st.session_state.chunks = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_quiz" not in st.session_state:
    st.session_state.last_quiz = None
if "last_summary" not in st.session_state:
    st.session_state.last_summary = None


def render_confidence(conf: dict):
    color_map = {"green": "#22C55E", "orange": "#F59E0B", "red": "#EF4444"}
    bar_color = color_map.get(conf.get("color", "red"), "#EF4444")
    st.markdown(
        f"""
        <div style="margin-bottom:6px;">
            <span style="font-size:0.78rem; color:{bar_color};
                         font-weight:600; letter-spacing:0.02em;">
                {conf['label'].upper()} &nbsp;·&nbsp; {conf['percentage']}%
            </span>
        </div>
        <div style="background:#E2E8F0; border-radius:99px;
                    height:5px; width:100%; margin-bottom:14px;">
            <div style="background:{bar_color}; width:{conf['percentage']}%;
                        height:100%; border-radius:99px;
                        transition: width 0.4s ease;"></div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_sources(sources: list):
    with st.expander(f"Sources ({len(sources)})"):
        for src in sources:
            if isinstance(src, dict):
                st.markdown(
                    f"<p style='font-size:0.82rem; font-weight:600;"
                    f"color:#0F172A; margin-bottom:2px;'>"
                    f"{src['source']} &mdash; Page {src['page']}</p>",
                    unsafe_allow_html=True
                )
                st.caption(f'"{src["snippet"]}"')
                st.markdown(
                    "<hr style='border-color:#F1F5F9; margin:8px 0;'/>",
                    unsafe_allow_html=True
                )
            else:
                st.write(f"{src}")


def reset_project():
    try:
        if os.path.exists(UPLOAD_DIR):
            shutil.rmtree(UPLOAD_DIR)
        if os.path.exists(FAISS_INDEX_PATH):
            shutil.rmtree(FAISS_INDEX_PATH)
        st.session_state.index = None
        st.session_state.chunks = None
        st.session_state.chat_history = []
        st.session_state.last_quiz = None
        st.session_state.last_summary = None
        st.success("Project reset. Ready for a fresh session.")
    except Exception as e:
        st.error(f"Reset failed: {str(e)}")


with st.sidebar:
    # Sidebar Minimal Logo Brand Mark
    sidebar_html = f'<div style="display:flex; align-items:center; margin-bottom:1.5rem; padding-bottom:1.2rem; border-bottom:1px solid #E2E8F0;"><img src="{SVG_DATA_URI}" width="44" style="border-radius:8px;"/></div>'
    st.markdown(sidebar_html, unsafe_allow_html=True)

    st.header("Documents")
    uploaded_files = st.file_uploader(
        "Upload course material",
        type=["pdf", "docx", "pptx"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files and st.button("Process Documents", type="primary"):
        with st.spinner("Processing..."):
            try:
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                all_chunks = []
                for uploaded_file in uploaded_files:
                    save_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    chunks = process_file(save_path)
                    all_chunks.extend(chunks)

                if not all_chunks:
                    st.error("No text could be extracted. Check your files and try again.")
                else:
                    build_faiss_index(all_chunks)
                    index, chunks = load_faiss_index()
                    st.session_state.index = index
                    st.session_state.chunks = chunks
                    st.success(f"{len(all_chunks)} passages indexed from {len(uploaded_files)} file(s).")
            except Exception as e:
                st.error(f"Processing failed: {str(e)[:100]}")

    if st.session_state.index is None and index_exists():
        index, chunks = load_faiss_index()
        st.session_state.index = index
        st.session_state.chunks = chunks
        st.info("Previous index loaded.")

    st.divider()

    if st.session_state.chat_history:
        st.header("This Session")
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            short_q = chat["question"][:45] + "..." if len(chat["question"]) > 45 else chat["question"]
            st.caption(f"Q{len(st.session_state.chat_history) - i}. {short_q}")

        if st.button("Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    st.divider()

    if st.button("Reset Project", use_container_width=True, type="secondary"):
        reset_project()
        st.rerun()

    st.divider()
    st.markdown(
        "<p class='powered-by'>Powered by Groq &nbsp;+&nbsp; FAISS</p>",
        unsafe_allow_html=True
    )

tab1, tab2, tab3 = st.tabs(["Ask Askora", "Quiz Generator", "Summarizer"])

with tab1:
    st.subheader("Ask anything from your documents")
    st.caption("Upload your course material and get grounded answers, quizzes, and summaries — all sourced from your own files.")

    if st.session_state.index is None:
        st.warning("Upload and process your documents to get started.")
    else:
        for chat in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(chat["question"])
            with st.chat_message("assistant"):
                if "confidence" in chat:
                    render_confidence(chat["confidence"])
                st.write(chat["answer"])
                if chat["sources"]:
                    render_sources(chat["sources"])

with tab2:
    st.subheader("Quiz Generator")
    st.caption("Generate exam-ready MCQs and structured questions directly from your uploaded material.")

    if st.session_state.index is None:
        st.warning("Upload and process your documents to get started.")
    else:
        quiz_type = st.selectbox(
            "Quiz Type",
            ["MCQs", "2 Marks Questions", "5 Marks Questions", "10 Marks Questions"]
        )

        col1, col2 = st.columns(2)
        with col1:
            quiz_topic = st.text_input("Topic", placeholder="e.g. AI")
        with col2:
            if quiz_type == "MCQs":
                num_q = st.slider("Number of Questions", 3, 20, 5)
            elif quiz_type == "2 Marks Questions":
                num_q = st.slider("Number of Questions", 2, 10, 3)
            elif quiz_type == "5 Marks Questions":
                num_q = st.slider("Number of Questions", 2, 8, 3)
            else:
                num_q = st.slider("Number of Questions", 1, 5, 2)

        if st.button("Generate Quiz", type="primary"):
            if not quiz_topic:
                st.error("Enter a topic first.")
            else:
                with st.spinner("Generating..."):
                    if quiz_type == "MCQs":
                        result = generate_mcqs(
                            quiz_topic, st.session_state.index,
                            st.session_state.chunks, num_q
                        )
                    elif quiz_type == "2 Marks Questions":
                        result = generate_marks_based_questions(
                            quiz_topic, st.session_state.index,
                            st.session_state.chunks, marks=2, num_questions=num_q
                        )
                    elif quiz_type == "5 Marks Questions":
                        result = generate_marks_based_questions(
                            quiz_topic, st.session_state.index,
                            st.session_state.chunks, marks=5, num_questions=num_q
                        )
                    else:
                        result = generate_marks_based_questions(
                            quiz_topic, st.session_state.index,
                            st.session_state.chunks, marks=10, num_questions=num_q
                        )

                    if result.get("error"):
                        st.error(result["message"])
                    else:
                        st.session_state.last_quiz = {
                            "type": quiz_type,
                            "topic": quiz_topic,
                            "questions": result.get("questions", [])
                        }

        if st.session_state.last_quiz:
            q_data = st.session_state.last_quiz
            st.markdown(f"### {q_data['type']} — {q_data['topic']}")

            if q_data["type"] == "MCQs":
                for i, q in enumerate(q_data["questions"]):
                    st.markdown(f"**Q{i+1}. {q['question']}**")
                    for opt, text in q["options"].items():
                        st.write(f"  {opt}. {text}")
                    with st.expander("Show Answer"):
                        st.success(f"Correct: {q['correct']}")
                        st.info(f"{q['explanation']}")
                    st.divider()
            else:
                for i, q in enumerate(q_data["questions"]):
                    marks = q.get("marks", "")
                    st.markdown(f"**Q{i+1}. {q['question']}** ({marks} marks)")
                    with st.expander("Show Answer"):
                        st.success(q["answer"])
                        if q.get("key_points"):
                            st.markdown("**Key Points:**")
                            for point in q["key_points"]:
                                st.write(f"- {point}")
                    st.divider()

with tab3:
    st.subheader("Summarizer")
    st.caption("Get concise, structured summaries of any topic from your uploaded documents.")

    if st.session_state.index is None:
        st.warning("Upload and process your documents to get started.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            summary_topic = st.text_input("Topic to summarize", placeholder="e.g. AI/ML")
        with col2:
            summary_mode = st.selectbox("Summary Mode", list(SUMMARY_MODES.keys()))

        if st.button("Summarize", type="primary"):
            if not summary_topic:
                st.error("Enter a topic first.")
            else:
                with st.spinner("Summarizing..."):
                    result = summarize_topic(
                        summary_topic,
                        st.session_state.index,
                        st.session_state.chunks,
                        summary_mode
                    )
                    if result.get("error"):
                        st.error(result["message"])
                    else:
                        st.session_state.last_summary = {
                            "topic": summary_topic,
                            "mode": summary_mode,
                            "text": result.get("text", "")
                        }

        if st.session_state.last_summary:
            s_data = st.session_state.last_summary
            st.markdown(
                f"<p style='font-size:0.78rem; font-weight:600; color:#94A3B8;"
                f"letter-spacing:0.06em; text-transform:uppercase;'>"
                f"{s_data['mode']} &nbsp;—&nbsp; {s_data['topic']}</p>",
                unsafe_allow_html=True
            )
            st.markdown(s_data["text"])

if st.session_state.index is not None:
    question = st.chat_input("Ask a question from your course material...")
    if question:
        with st.spinner("Thinking..."):
            result = answer_question(
                question,
                st.session_state.index,
                st.session_state.chunks,
                chat_history=st.session_state.chat_history
            )

        if result.get("error"):
            st.error(result["message"])
        else:
            st.session_state.chat_history.append({
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"],
                "confidence": result["confidence"]
            })
            st.rerun()