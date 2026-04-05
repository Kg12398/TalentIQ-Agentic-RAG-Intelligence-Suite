import streamlit as st
import os
import time
from datetime import datetime

# ── IMPORTS ──
from Generation import build_rag_chain, run_rag_pipeline, get_cached_pipeline, run_matchmaker
from Parsing import parse_single_resume
from Embeddings import embed_single_resume, delete_candidate
import speech_recognition as sr
import io
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import pandas as pd

def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio_data = r.record(source)
            return r.recognize_google(audio_data)
    except sr.UnknownValueError:
        return "ERROR: Google Speech Recognition could not understand audio."
    except sr.RequestError as e:
        return f"ERROR: Could not request results; {e}"
    except Exception as e:
        return f"ERROR: {str(e)}"

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="TalentIQ | Executive Intelligence",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── PREMIUM CSS ──
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #F8FAFC !important;
    }
    .block-container {
        max-width: 900px !important;
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        margin: auto !important;
    }
    #MainMenu, footer {visibility: hidden;}

    .executive-logo { text-align: center; margin-bottom: 0.5rem; font-size: 3rem; }
    .main-title {
        font-family: 'Outfit', sans-serif !important;
        color: #FFFFFF
        font-size: 2.8rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748B;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2.5rem;
    }

    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 1rem 0 !important;
        margin-bottom: 1.5rem !important;
    }
    [data-testid="stChatMessage"][data-testid="stChatMessageAssistant"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li, [data-testid="stChatMessage"] span {
        color: #1E293B !important;
        line-height: 1.7 !important;
        font-size: 1.05rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown('<div class="executive-logo">💼</div>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">TalentIQ</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Advanced Candidate Intelligence Suite</p>', unsafe_allow_html=True)

# ── SIDEBAR ──
with st.sidebar:
    st.title("🤖 TalentIQ Intelligence Suite")
    st.divider()
    
    # 📁 AUTOMATED UPLOADER ENGINE
    st.markdown("### 📥 Candidate Uploader")
    uploaded_file = st.file_uploader("Upload internal PDF resume...", type=["pdf"], help="The engine will automatically parse, fragment, and vectorize this document.")
    if st.button("Process & Add", type="primary"):
        if uploaded_file is not None:
            # Generate a secure file path
            upload_path = os.path.join(r"C:\Users\dell\Project\Resume data", uploaded_file.name)
            
            # Save PDF locally
            with st.status("Ingesting Candidate File...", expanded=True) as status:
                st.write(f"Saving `{uploaded_file.name}` to secure persistence layer...")
                with open(upload_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 1. Parse PDF to MD
                st.write("Executing Visual & Semantic OCR via LlamaParse engine...")
                parsed_md_path = parse_single_resume(upload_path)
                
                # 2. Embed into ChromaDB via Hybrid Pipeline
                st.write("Generating hierarchical chunk embeddings (Cohere 1024d)...")
                embed_single_resume(parsed_md_path)
                
                status.update(label=f"Successfully Ingested: {uploaded_file.name}", state="complete", expanded=False)
                
            # Hot reload pipeline to include new vector space
            st.cache_resource.clear()
            st.success("Knowledge Graph Updated! Candidate is now live in memory.")
        else:
            st.error("Please upload a stable PDF document first.")
            
    st.divider()
    # 📁 ACTIVE CANDIDATE DELETION
    with st.expander("📁 Active Candidates", expanded=False):
        st.write("Candidates currently residing in Vector Memory:")
        parsed_dir = r"C:\Users\dell\Project\Parsed data"
        if os.path.exists(parsed_dir):
            candidates = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
            if candidates:
                for c in candidates:
                    col1, col2 = st.columns([4, 1])
                    col1.caption(f"📄 {c.replace('.md', '')}")
                    if col2.button("🗑️", key=f"del_{c}", help=f"Delete {c}"):
                        with st.spinner("Deleting..."):
                            delete_candidate(c)
                            st.cache_resource.clear()
                        st.rerun()
            else:
                st.caption("No candidates found.")
        else:
            st.caption("Database is empty.")

    st.markdown("### TalentIQ Control")
    if st.button("🗑️ Clear Session"):
        st.session_state.messages = []
        st.session_state.chat_summary = ""
        st.rerun()
    
    st.divider()
    st.markdown("### 🎙️ Voice Assistant")
    st.caption("Click the Mic icon to speak your query:")
    recorded_audio = audio_recorder(text="🎤", recording_color="#e8b50e", neutral_color="#6aa36f", icon_size="2x")
    
    voice_prompt = None
    if recorded_audio:
        with st.spinner("Transcribing..."):
            voice_prompt = transcribe_audio(recorded_audio)
        if voice_prompt and not voice_prompt.startswith("ERROR:"):
            st.success(f"Heard: '{voice_prompt}'")
        elif voice_prompt:
            st.error(voice_prompt)

    st.divider()
    st.caption("Engine: Groq Llama 3.3 70B (Ultra-Speed)")
    st.caption("Mode: Standalone Executive Suite")
    st.caption("Status: Active Intelligence")

# ── SESSION STATE ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_summary" not in st.session_state:
    st.session_state.chat_summary = ""

# ── STRUCTURAL TABS ──
tab1, tab2 = st.tabs(["💬 Recruitment Chat", "🎯 Matchmaker Engine"])

with tab1:
    st.markdown("### 💬 Live Recruitment Intelligence")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    text_prompt = st.chat_input("Ask about your candidate pool...")
    prompt = text_prompt or voice_prompt

    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.status("Analyzing Intelligence...", expanded=False) as status:
                status.write("🧬 Activating Personal Intelligence Layer...")
                status.write("📂 Loading Vector Database...")
                pipeline = get_cached_pipeline()
                
                # ── EMPTY DATABASE GUARD ──────────────────────────────────
                if pipeline is None:
                    answer = (
                        "⚠️ **No candidate data found in the database.**\n\n"
                        "Please upload one or more PDF resumes using the **📥 Candidate Uploader** "
                        "in the sidebar, then ask your question again."
                    )
                    status.update(label="No candidates loaded", state="error")
                else:
                    status.write("🧠 Querying Neural Engine...")
                    result = run_rag_pipeline(
                        prompt, 
                        pipeline=pipeline,
                        history=st.session_state.messages, 
                        summary=st.session_state.chat_summary
                    )
                    answer = result.get("answer", "I encountered an issue. Please re-submit your query.")
                    st.session_state.messages = result.get("history", st.session_state.messages)
                    st.session_state.chat_summary = result.get("summary", "")
                    route = result.get("route", "RAG")
                    status.update(label=f"Analysis Complete (Route: {route})", state="complete")

            st.markdown(answer)
            
            # 🔊 Voice Agent (TTS)
            try:
                tts = gTTS(text=answer, lang='en', slow=False)
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                st.audio(audio_fp, format='audio/mp3', autoplay=True)
            except Exception as e:
                st.caption(f"Voice synthesis failed: {e}")

        
        st.session_state.messages.append({"role": "assistant", "content": answer})

with tab2:
    st.markdown("### 🎯 Autonomous Candidate Matchmaker")
    st.write("Paste a raw Job Description below. The autonomous agents will extract, read, and mathematically score every single candidate in your database against the requirements.")
    
    jd = st.text_area("Job Description Requirements", height=250, placeholder="E.g. We are looking for a Senior Python Developer with 5 years of Django experience...")
    
    if st.button("🚀 Execute Map-Reduce Scoring Pipeline", type="primary"):
        if jd:
            with st.status("Executing Multi-Agent Evaluation Loop...", expanded=True) as status:
                status.write("Extracting unstructured candidate profiles...")
                status.write("Spawning evaluation agents...")
                
                parsed_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Parsed data")
                results = run_matchmaker(jd, parsed_dir)
                
                status.update(label="Evaluation Phase Complete!", state="complete", expanded=False)
                
            if results:
                st.markdown("#### 🏆 Evaluation Leaderboard")
                df = pd.DataFrame(results)
                
                for idx, row in df.iterrows():
                    st.markdown(f"**{idx+1}. {row['Candidate']}**")
                    st.progress(row['Match Percentage'] / 100.0, text=f"{row['Match Percentage']}% Match Score")
                    st.caption(f"**Agent Rationale:** {row['Evaluation Rationale']}")
                    st.divider()
        else:
            st.warning("Please paste a Job Description first.")

# ── FOOTER ──
if st.session_state.chat_summary:
    with st.expander("📝 Session Summary", expanded=False):
        st.info(st.session_state.chat_summary)

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("Enterprise Standalone Intelligence Suite | Proprietary TalentIQ Engine")
