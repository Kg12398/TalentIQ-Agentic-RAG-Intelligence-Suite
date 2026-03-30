import os
import json
import time
import streamlit as st
from dotenv import load_dotenv

# Load API keys immediately when module is imported
load_dotenv()

# LangChain imports
from langchain_groq import ChatGroq
from langchain_cohere import CohereEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter

# Cohere Reranker
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank

# json is already imported above

def is_chitchat(prompt):
    cleaned = prompt.strip().lower()
    chitchat_triggers = [
        "hi", "hello", "hey", "good morning", "good evening", "how are you", 
        "who are you", "what are you", "what can you do", "help", "thanks", "thank you"
    ]
    # Exact match or starts with a greeting (e.g. "hi there")
    for trigger in chitchat_triggers:
        if cleaned == trigger or cleaned.startswith(trigger + " "):
            return True
        # also catch "hi!" or "hello,"
        if cleaned.startswith(trigger + "!") or cleaned.startswith(trigger + ","):
            return True
    return False


# ─────────────────────────────────────────────
#  SHARED HELPERS
# ─────────────────────────────────────────────

def format_docs(docs):
    """Formats retrieved docs with candidate name from metadata for Gemini to read."""
    formatted_chunks = []
    for doc in docs:
        candidate_name = doc.metadata.get('source', 'Unknown Candidate')
        formatted_chunks.append(f"--- CANDIDATE RESUME: {candidate_name} ---\n{doc.page_content}\n")
    return "\n\n".join(formatted_chunks)


# ─────────────────────────────────────────────
#  STEP A: QUERY ROUTER
#  Uses a ZERO-COST Python keyword classifier.
#  This saves one full LLM call per question,
#  cutting your API quota usage by 50%.
# ─────────────────────────────────────────────

def classify_query(user_question: str, llm=None, parsed_dir: str = None) -> dict:
    """
    Zero-cost Python-based query router.
    Extracts candidate names from filenames in 'Parsed data' and
    checks if any name is mentioned in the user's question.

    Returns:
        {"type": "SPECIFIC_CANDIDATE", "name": "gaurav"}
        {"type": "GENERAL"}
    """
    print(f"[ROUTER] Classifying query intent (Zero-Cost Keyword Mode)...")

    question_lower = user_question.lower()

    # Dynamically load candidate names from filenames
    candidate_names = []
    if parsed_dir and os.path.exists(parsed_dir):
        for fname in os.listdir(parsed_dir):
            if fname.endswith('.md'):
                # e.g. "Kumar-Gaurav.md" → ["kumar", "gaurav"]
                parts = fname.replace('.md', '').replace('_', '-').split('-')
                for part in parts:
                    clean = part.strip().lower()
                    if len(clean) > 2:  # Skip short suffixes like 'cv'
                        candidate_names.append(clean)

    # Check if any candidate name appears in the question
    for name in candidate_names:
        if name in question_lower:
            print(f"[ROUTER] ✅ SPECIFIC_CANDIDATE detected: '{name}'")
            return {"type": "SPECIFIC_CANDIDATE", "name": name}

    print(f"[ROUTER] Decision: GENERAL query.")
    return {"type": "GENERAL"}



def find_candidate_file(name_hint: str, parsed_dir: str) -> str | None:
    """
    Fuzzy-matches the candidate name from the router against
    the actual .md filenames in the Parsed data directory.

    e.g. "gaurav" → "Kumar-Gaurav.md"
         "himanshu" → "Himanshu-Tripathi.md"

    Returns the full path if found, or None.
    """
    name_lower = name_hint.strip().lower()
    if not os.path.exists(parsed_dir):
        return None

    for filename in os.listdir(parsed_dir):
        if filename.endswith('.md'):
            # Check if the hint is a substring of the filename (case-insensitive)
            if name_lower in filename.lower():
                return os.path.join(parsed_dir, filename)

    return None


# ─────────────────────────────────────────────
#  STEP B: DIRECT CANDIDATE LOOKUP
#  When the router detects a specific candidate,
#  we BYPASS ChromaDB and load the full .md file.
#  This gives Gemini 100% of the resume data.
# ─────────────────────────────────────────────

DIRECT_LOOKUP_PROMPT = """You are an elite Technical Recruiter and HR Assistant.
You have been given the COMPLETE resume of a specific candidate.
Answer the user's question based STRICTLY on this resume content.

Follow these rules:
1. PRECISION: Extract exact facts from the resume. Do not guess.
2. TYPOS & OCR: The text is extracted from PDFs. Decode OCR typos intelligently:
   - "201632020" means "2016 to 2020"
   - "202332025" means "2023 to 2025"
   - "NOV 2020 - FEB 2022" is straightforward: Nov 2020 to Feb 2022
3. DATE ANALYSIS: If asked about timelines, gaps, or total experience:
   Step 1: Extract ALL dates mentioned (both Education and Work Experience).
   Step 2: Build a complete chronological timeline from earliest to latest.
   Step 3: Identify any gaps (periods > 3 months where no job or education is listed).
   Step 4: Show your math explicitly (e.g., "Feb 2022 to Jun 2025 = 3 years 4 months").
4. TABLE PARSING: Dates in the resume may appear in Markdown table format. 
   Columns are separated by | pipes. Look carefully across all rows and columns.
5. CANDIDATE: Always begin your answer by clearly stating the candidate's name.

COMPLETE RESUME CONTENT:
{full_resume}

PREVIOUS CONVERSATION SUMMARY:
{memory_summary}

RECENT CHAT HISTORY:
{chat_history}

User Question: {question}

Detailed Answer (Think Step-by-Step):"""


def run_direct_lookup(candidate_name: str, user_question: str, llm, parsed_dir: str) -> str:
    """
    Bypasses the vector database entirely.
    Loads the full .md resume file for the named candidate
    and sends it directly to Gemini for analysis.
    """
    print(f"[DIRECT LOOKUP] Searching for candidate: '{candidate_name}'")
    candidate_file = find_candidate_file(candidate_name, parsed_dir)

    if not candidate_file:
        print(f"[DIRECT LOOKUP] No matching file found for '{candidate_name}'. Falling back to Hybrid Search.")
        return None  # Signal to caller to fall back to RAG

    filename = os.path.basename(candidate_file)
    print(f"[DIRECT LOOKUP] Found: {filename}. Loading full resume...")

    with open(candidate_file, 'r', encoding='utf-8') as f:
        full_resume = f.read()

    print(f"[DIRECT LOOKUP] Injecting {len(full_resume)} characters directly into Gemini context...")

    prompt = PromptTemplate.from_template(DIRECT_LOOKUP_PROMPT)
    direct_chain = prompt | llm | StrOutputParser()
    response = direct_chain.invoke({"full_resume": full_resume, "question": user_question})
    print(f"[DIRECT LOOKUP] Done.\n")
    return response


# ─────────────────────────────────────────────
#  BUILD THE HYBRID RAG CHAIN (cached in Streamlit)
# ─────────────────────────────────────────────

@st.cache_resource
def get_cached_pipeline():
    """
    Returns the cached RAG pipeline tuple: (rag_chain, llm, parsed_dir).
    This ensures we only load ChromaDB and model weight once.
    """
    return build_rag_chain()

def build_rag_chain():
    """
    Builds and returns a tuple: (rag_chain, llm, parsed_dir)
    
    This function is EXPENSIVE — it should ONLY be called ONCE per server session.
    In Streamlit, decorate the calling function with @st.cache_resource.

    Returns:
        rag_chain: The full LangChain hybrid retrieval chain.
        llm: The Gemini LLM instance (reused by the router and direct lookup).
        parsed_dir: The path to the Parsed data directory.
    """
    print("\n[RAG INIT] Building pipeline components (this runs only ONCE)...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_folder = os.path.join(script_dir, "chroma_db")
    parsed_dir = os.path.join(script_dir, "Parsed data")

    # --- STEP 1: Connect to ChromaDB (stores CHILD chunks, 300 chars each) ---
    print("[RAG INIT] Connecting to ChromaDB (child embeddings)...")
    
    # Robust API Key fetching for Streamlit Cloud
    api_key = os.getenv("GOOGLE_API_KEY")
    
    cohere_api_key = os.getenv("COHERE_API_KEY")
    embeddings_model = CohereEmbeddings(
        model="embed-english-v3.0",
        cohere_api_key=cohere_api_key
    )
    vector_db = Chroma(
        persist_directory=db_folder,
        embedding_function=embeddings_model
    )
    child_count = vector_db._collection.count()
    print(f"[RAG INIT] ChromaDB loaded: {child_count} child chunks.")

    # --- STEP 2: Load Parent Docstore (JSON files on disk, 2000 chars each) ---
    store_folder = os.path.join(script_dir, "parent_docstore")
    print(f"[RAG INIT] Loading parent JSON files from '{store_folder}'...")
    parent_map = {}   # { parent_id (UUID str) : Document }
    if os.path.exists(store_folder):
        for fname in os.listdir(store_folder):
            if fname.endswith(".json"):
                with open(os.path.join(store_folder, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                parent_map[data["id"]] = Document(
                    page_content=data["page_content"],
                    metadata=data["metadata"]
                )
    print(f"[RAG INIT] Loaded {len(parent_map)} parent chunks into memory.")

    # --- STEP 3: BM25 Keyword Retriever on child chunks ---
    print("[RAG INIT] Building BM25 Keyword Index on child chunks...")
    db_data = vector_db.get()
    child_docs = [Document(page_content=t, metadata=m)
                  for t, m in zip(db_data['documents'], db_data['metadatas'])]
    bm25_child_retriever = BM25Retriever.from_documents(child_docs)
    bm25_child_retriever.k = 15

    # Chroma child retriever (searches small 300-char embeddings for precision)
    chroma_child_retriever = vector_db.as_retriever(search_kwargs={"k": 20})

    def children_to_parents(child_results: list) -> list:
        """Maps a list of child Documents to their parent Documents using parent_id metadata."""
        seen = set()
        parents = []
        for child in child_results:
            pid = child.metadata.get("parent_id")
            if pid and pid not in seen and pid in parent_map:
                seen.add(pid)
                parents.append(parent_map[pid])
        return parents

    def hybrid_parent_retriever(query: str) -> list:
        """
        Parent-Child Hybrid Retrieval:
        1. BM25  searches child chunks (300 chars) → maps to 2000-char parents
        2. Chroma searches child chunks (300 chars) → maps to 2000-char parents
        3. Results merged, deduplicated, returned for Cohere to rerank
        """
        # BM25 on children → fetch parents
        bm25_children  = bm25_child_retriever.invoke(query)
        bm25_parents   = children_to_parents(bm25_children)

        # Semantic on children → fetch parents
        chroma_children  = chroma_child_retriever.invoke(query)
        chroma_parents   = children_to_parents(chroma_children)

        # Merge and deduplicate by first 100 chars of content
        seen_content = set()
        unique_parents = []
        for doc in bm25_parents + chroma_parents:
            key = doc.page_content[:100]
            if key not in seen_content:
                seen_content.add(key)
                unique_parents.append(doc)

        print(f"[RETRIEVER] BM25 parents: {len(bm25_parents)} | "
              f"Chroma parents: {len(chroma_parents)} | "
              f"Unique merged: {len(unique_parents)}")
        return unique_parents

    # --- STEP 4: Wrap hybrid retriever into LangChain interface for Cohere ---
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.callbacks import CallbackManagerForRetrieverRun
    from typing import List

    class HybridParentRetrieverWrapper(BaseRetriever):
        """LangChain-compatible wrapper around our custom hybrid_parent_retriever."""
        def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
        ) -> List[Document]:
            return hybrid_parent_retriever(query)

    # --- STEP 5: Cohere Reranker (scores full 2000-char parent chunks) ---
    print("[RAG INIT] Activating Cohere AI Reranker (reranks full parent chunks)...")
    cohere_api_key = os.getenv("COHERE_API_KEY")
    if cohere_api_key:
        base_retriever_obj = HybridParentRetrieverWrapper()
        # Optimization: top_n=6 is usually enough for HR and faster than 8
        compressor  = CohereRerank(cohere_api_key=cohere_api_key, model="rerank-english-v3.0", top_n=6)
        retriever   = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=base_retriever_obj
        )
    else:
        print("[RAG INIT] WARNING: COHERE_API_KEY not found. Using hybrid parents without reranking.")
        retriever = HybridParentRetrieverWrapper()

    # --- STEP 5: Groq LLM (High-Speed Llama 3.3 70B) ---
    print("[RAG INIT] Connecting to Groq Llama-3.3-70B-Versatile...")
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.1
    )

    # --- STEP 6: The Enhanced HR Prompt Template (for Hybrid RAG path) ---
    prompt_template = """
    You are an expert Technical Recruiter and HR Assistant.

Answer the user's question using ONLY the provided context chunks from the vector database (candidate resumes).

Rules:
1. Use only the information present in the context. Do not add outside knowledge.
2. If the answer is not found in the context, respond: "I do not have enough information."
3. Always mention the candidate's name at the beginning if it is available in the context.
4. Correct obvious OCR or parsing errors (e.g., "201632020" → "2016–2020").
5. Extract and consider all relevant dates from education and work experience.
6. When relevant, analyze the candidate’s timeline and identify gaps.
7. Support answers with specific skills, tools, achievements, or metrics mentioned in the resume.

Be clear, concise, and evidence-based.
    
    PREVIOUS CONVERSATION SUMMARY:
    {memory_summary}

    RECENT CHAT HISTORY:
    {chat_history}
    
    Context from Vector Database (Hybrid Search + Cohere Reranked):
    {context}

    Question: {question}
    
    Elite HR Answer (Think Step-by-Step):"""

    prompt = PromptTemplate.from_template(prompt_template)

    # --- STEP 7: Assemble the LangChain LCEL Chain ---
    rag_chain = (
        {
            "context": itemgetter("question") | retriever | format_docs, 
            "question": itemgetter("question"), 
            "chat_history": itemgetter("chat_history"), 
            "memory_summary": itemgetter("memory_summary")
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    print("[RAG INIT] Pipeline ready!\n")
    return rag_chain, llm, parsed_dir


# ─────────────────────────────────────────────
#  MAIN ORCHESTRATOR
#  This is what Streamlit calls every time a
#  user sends a message in the chatbot.
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
#  STEP C: MEMORY SUMMARIZATION
# ─────────────────────────────────────────────

SUMMARIZE_PROMPT = """You are a Memory Manager for an HR Assistant.
Your task is to consolidate a long chat history and an existing summary into a single, dense, high-utility summary.

RULES:
1. Keep ALL specific details: candidate names mentioned, specific skills discussed, year gaps identified, and previous decisions.
2. Remove "noise": greetings, filler words, and redundant questions.
3. Keep it under 2,000 characters.

Existing Summary: {current_summary}
New Messages to Integrate: {new_messages}

Condensed Summary:"""

def summarize_history(history_list, current_summary, llm):
    """
    Summarizes the entire history into a single cohesive paragraph.
    Returns: New Summary String
    """
    history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history_list])
    chain = PromptTemplate.from_template(SUMMARIZE_PROMPT) | llm | StrOutputParser()
    
    print(f"[MEMORY] Condensing {len(history_text)} characters of history...")
    new_summary = chain.invoke({
        "current_summary": current_summary or "No previous summary.",
        "new_messages": history_text
    })
    return new_summary

def run_rag_pipeline(user_question, pipeline=None, history=None, summary="", **kwargs):
    """
    Stateful orchestrator with Summarization Memory.
    """
    if history is None: history = []
    
    # Build pipeline if not provided
    if pipeline is None:
        pipeline = build_rag_chain()
    rag_chain, llm, parsed_dir = pipeline

    # Trigger Summarization if history is too long (> 10,000 chars)
    history_chars = sum(len(m['content']) for m in history)
    if history_chars > 10000:
        summary = summarize_history(history, summary, llm)
        # Keep only the current question (the last message) for continuity
        history = history[-1:] if len(history) >= 1 else []
        print(f"[MEMORY] Summary triggered. New history size: {len(history)} messages.")

    # Format history for the prompt (excluding the current question which is passed separately)
    history_formatted = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history[:-1]])

    # ── STEP 0: CHITCHAT ROUTER (Zero-Cost, Zero-RAG) ──
    if is_chitchat(user_question):
        print(f"[ORCHESTRATOR] Route: CHITCHAT detected.")
        chitchat_prompt = PromptTemplate.from_template(
            "You are TalentIQ, an elite AI HR Assistant. Be friendly, professional, and concise. "
            "Reply strictly to this user message: {question}"
        )
        chain = chitchat_prompt | llm | StrOutputParser()
        answer = chain.invoke({"question": user_question})
        return {"answer": answer, "route": "Chitchat / Greeting", "history": history, "summary": summary}

    # ── STEP 1: ROUTE THE QUERY (Zero-Cost) ──
    route_info = classify_query(user_question, parsed_dir=parsed_dir)
    query_type = route_info.get("type", "GENERAL")

    # ── STEP 2A: SPECIFIC CANDIDATE → DIRECT LOOKUP ──
    if query_type == "SPECIFIC_CANDIDATE":
        candidate_name = route_info.get("name", "")
        print(f"[ORCHESTRATOR] Route: DIRECT LOOKUP for candidate '{candidate_name}'")
        response = _call_with_retry(
            lambda: run_direct_lookup_with_mem(candidate_name, user_question, history_formatted, summary, llm, parsed_dir)
        )
        if response is None:
            print("[ORCHESTRATOR] Direct lookup failed. Falling back to Hybrid Search.")
            query_type = "GENERAL (fallback)"
        else:
            return {"answer": response, "route": f"Direct Lookup ({candidate_name})", "history": history, "summary": summary}

    # ── STEP 2B: GENERAL → HYBRID SEARCH + COHERE + GEMINI ──
    print(f"[ORCHESTRATOR] Route: HYBRID SEARCH")
    
    input_data = {
        "question": user_question,
        "chat_history": history_formatted or "None.",
        "memory_summary": summary or "None yet."
    }

    print("[ORCHESTRATOR] Generator: Invoking RAG Chain...")
    response = _call_with_retry(lambda: rag_chain.invoke(input_data))
    print("[ORCHESTRATOR] Done.\n")
    return {"answer": response, "route": "Hybrid Search + Cohere Reranker", "history": history, "summary": summary}

def run_direct_lookup_with_mem(candidate_name, user_question, history, summary, llm, parsed_dir):
    """Wrapper for direct lookup that includes memory."""
    candidate_file = find_candidate_file(candidate_name, parsed_dir)
    if not candidate_file: return None
    
    with open(candidate_file, 'r', encoding='utf-8') as f:
        full_resume = f.read()

    prompt = PromptTemplate.from_template(DIRECT_LOOKUP_PROMPT)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "full_resume": full_resume, 
        "question": user_question,
        "chat_history": history or "None.",
        "memory_summary": summary or "None yet."
    })

def stream_direct_lookup(candidate_name, user_question, history, summary, llm, parsed_dir):
    """Streams the direct lookup response with retry logic."""
    candidate_file = find_candidate_file(candidate_name, parsed_dir)
    if not candidate_file: yield "Candidate not found." ; return
    
    with open(candidate_file, 'r', encoding='utf-8') as f:
        full_resume = f.read()

    prompt = PromptTemplate.from_template(DIRECT_LOOKUP_PROMPT)
    chain = prompt | llm | StrOutputParser()
    
    max_stream_retries = 2
    for attempt in range(max_stream_retries + 1):
        try:
            yield "" # Start/Reset the stream
            for chunk in chain.stream({
                "full_resume": full_resume, 
                "question": user_question,
                "chat_history": history or "None.",
                "memory_summary": summary or "None yet."
            }):
                if chunk: yield chunk
            return # Success
        except Exception as e:
            error_msg = str(e).lower()
            if ("429" in error_msg or "exhausted" in error_msg) and attempt < max_stream_retries:
                yield f"\n\n[RATE LIMIT] Server is busy. Auto-retrying in 30s... (Attempt {attempt+1})"
                import time
                time.sleep(30)
                continue
            yield f"\n\n[SERVICE ALERT] Connection interrupted: {e}. Please re-submit your query."
            break


def _call_with_retry(fn, max_attempts=3):
    """Wraps any LLM call with auto-retry for Google 429 rate limit errors."""
    import time
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "exhausted" in error_msg or "quota" in error_msg:
                wait = 5 * (attempt + 1)  # 5s, 10s, 15s
                print(f"[RETRY] Rate Limit Hit! Sleeping {wait}s (Attempt {attempt+1}/{max_attempts})...")
                if attempt < max_attempts - 1:
                    time.sleep(wait)
                    continue
            return f"Service reached its capacity temporarily. Please try again in a moment. (Error: {e})"


# ─────────────────────────────────────────────
#  MATCHMAKER ORCHESTRATOR (Agentic Loop)
# ─────────────────────────────────────────────
def run_matchmaker(job_description, parsed_dir):
    """Map-Reduce autonomous evaluation of all candidates against a Job Description."""
    import os
    import json
    from langchain_groq import ChatGroq
    from langchain_core.prompts import PromptTemplate
    
    if not os.path.exists(parsed_dir):
        return []
        
    candidates = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
    if not candidates:
        return []
        
    print("[MATCHMAKER] Initializing Evaluation Protocol...")
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.0) # Zero temp for analytical grading
    
    prompt = PromptTemplate.from_template('''
    You are an expert Technical Recruiter evaluating a candidate against a Job Description.
    
    JOB DESCRIPTION:
    {jd}
    
    CANDIDATE RESUME:
    {resume}
    
    Task: Analyze the candidate thoroughly against the job requirements.
    Assign a strict "score" from 0 to 100 representing their percent match. 
    Write a concise 1-2 sentence "reasoning" justifying your score.
    
    You MUST output valid JSON and nothing else. Do not use markdown backticks.
    Example Format:
    {{"score": 85, "reasoning": "Strong python background but lacks cloud architecture experience."}}
    ''')
    
    results = []
    for c in candidates:
        filepath = os.path.join(parsed_dir, c)
        with open(filepath, 'r', encoding='utf-8') as f:
            resume_text = f.read()
            
        print(f"[MATCHMAKER] Evaluating: {c}...")
        try:
            chain = prompt | llm
            res = chain.invoke({"jd": job_description, "resume": resume_text})
            
            raw_text = res.content
            # Safely extract JSON from Markdown code blocks if generated
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = raw_text[start:end]
                data = json.loads(json_str)
                score = int(data.get("score", 0))
                reasoning = data.get("reasoning", "No valid reasoning generated.")
            else:
                score = 0
                reasoning = "Critical Agent Failure: Invalid JSON returned."
        except Exception as e:
            score = 0
            reasoning = f"Evaluation Crash: {str(e)}"
            
        results.append({
            "Candidate": c.replace('_Parsed.md', '').replace('.md', ''),
            "Match Percentage": score,
            "Evaluation Rationale": reasoning
        })
        
    # Sort leaderboards
    results.sort(key=lambda x: x["Match Percentage"], reverse=True)
    return results


if __name__ == "__main__":
    pipeline = build_rag_chain()
    # Updated to pass pipeline as a keyword argument to match the new signature
    result = run_rag_pipeline(
        user_question="List all education and work experience dates for Kumar Gaurav. Are there any year gaps?", 
        pipeline=pipeline
    )
    print(f"\nRoute taken: {result['route']}")
    print(f"Answer:\n{result['answer']}")
