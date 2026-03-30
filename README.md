# 🤖 TalentIQ: Agentic RAG Intelligence Suite

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/)

**TalentIQ** is an enterprise-grade Résumé Intelligence platform that transforms static PDF resumes into a dynamic, queryable knowledge base. Built for senior AI/ML engineering roles, it employs **Agentic RAG (Retrieval-Augmented Generation)** to provide high-precision answers about candidate experience, skill gaps, and role suitability.

---

## 🚀 Key Features

*   **🧠 Intelligence-Driven Query Routing**: Automatically classifies questions with **Gemini 2.5 Flash** to decide between "Direct Full-CV Lookup" (for timeline/gap analysis) or "Hybrid Fragment Search" (for general queries).
*   **📂 Advanced Parent-Child Chunking**: Combines high-precision **Child Chunks (300 chars)** for retrieval with rich **Parent Chunks (2000 chars)** for LLM context.
*   **🔍 Hybrid Search Engine**: Fuses **ChromaDB Semantic Search** (Vector) with **BM25 Keyword Search** (Lexical) using a **75/25 weight ratio**.
*   **🎯 Cohere AI Reranking**: Utilizes `rerank-english-v3.0` to filter the top retrieved chunks, ensuring the LLM only reads the most hyper-relevant data.
*   **📄 Premium Parsing**: Uses **LlamaParse (Markdown-mode)** to intelligently extract tables and layout structures from complex PDF resumes.
*   **📊 Enterprise Dashboard**: A professional, light-themed Streamlit UI featuring metric cards, document viewers, and real-time pipeline timing breakdowns.

---

## 🛠️ Tech Stack

- **Core**: Python 3.11, LangChain
- **LLM/Embeddings**: Google Gemini 2.5 Flash, Gemini-Embedding-001
- **Database**: ChromaDB (Vector), Local JSON Store (Parent Documents)
- **Reranker**: Cohere AI
- **Parsing**: LlamaParse
- **UI**: Streamlit

---

## 📐 Architecture Overview

```mermaid
graph TD
    A[User Query] --> B{Gemini Router}
    B -- "Specific Candidate" --> C[Direct Doc Lookup]
    B -- "General Query" --> D[Hybrid Search Engine]
    
    C --> G[Gemini 2.5 Flash]
    
    D --> E1[ChromaDB Child Search]
    D --> E2[BM25 Keyword Search]
    
    E1 & E2 --> F[Map to Parent Documents]
    F --> H[Cohere Reranker]
    H --> G
    
    G --> I[Verified HR Response]
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/talentiq-agentic-rag.git
cd talentiq-agentic-rag
```

### 2. Set up Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure API Keys
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY="your_google_key"
LLAMA_CLOUD_API_KEY="your_llama_key"
COHERE_API_KEY="your_cohere_key"
```

### 4. Run the Pipeline
```bash
python Parsing.py     # Convert PDFs to Markdown
python Embeddings.py  # Build the Parent-Child Database
streamlit run visualizer.py
```

---

## 🛡️ License
MIT License.

---
*Created with ❤️ by [Your Name]*
