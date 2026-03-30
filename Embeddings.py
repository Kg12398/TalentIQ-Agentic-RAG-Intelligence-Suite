import os
import time
import uuid
import json
from dotenv import load_dotenv

from langchain_cohere import CohereEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ─────────────────────────────────────────────────────────────
#  PARENT-CHILD CHUNKING PIPELINE
#
#  Parent chunks (2000 chars) → saved to parent_docstore/ as JSON files
#  Child  chunks (300  chars) → embedded into chroma_db/
#  Each child has metadata["parent_id"] linking it to its parent
# ─────────────────────────────────────────────────────────────

PARENT_CHUNK_SIZE    = 2000
PARENT_CHUNK_OVERLAP = 250
CHILD_CHUNK_SIZE     = 300
CHILD_CHUNK_OVERLAP  = 45


def save_parent(parent_doc: Document, store_folder: str) -> str:
    """Save one parent Document to disk as a JSON file. Returns its unique ID."""
    parent_id = str(uuid.uuid4())
    data = {
        "id":           parent_id,
        "page_content": parent_doc.page_content,
        "metadata":     parent_doc.metadata,
    }
    path = os.path.join(store_folder, f"{parent_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return parent_id


def embed_single_resume(md_file_path: str):
    """Embeds a single parsed markdown file into ChromaDB and saves its parent chunks."""
    load_dotenv()
    
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    db_folder    = os.path.join(script_dir, "chroma_db")
    store_folder = os.path.join(script_dir, "parent_docstore")
    os.makedirs(store_folder, exist_ok=True)
    
    filename = os.path.basename(md_file_path)
    print(f"\n[STEP 1] Loading {filename} for embedding...")
    
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    doc = Document(page_content=content, metadata={"source": filename})
    
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=PARENT_CHUNK_SIZE,
        chunk_overlap=PARENT_CHUNK_OVERLAP,
    )
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHILD_CHUNK_SIZE,
        chunk_overlap=CHILD_CHUNK_OVERLAP,
    )
    
    print("\n[STEP 2] Splitting into Parent and Child chunks...")
    all_child_docs = []
    
    parents = parent_splitter.create_documents(
        [doc.page_content],
        metadatas=[{"source": filename}]
    )

    for parent_doc in parents:
        parent_id = save_parent(parent_doc, store_folder)
        children = child_splitter.create_documents(
            [parent_doc.page_content],
            metadatas=[{"source": filename, "parent_id": parent_id}]
        )
        all_child_docs.extend(children)
        
    print(f"  {filename}: {len(parents)} parents → {len(all_child_docs)} children")
    
    print("\n[STEP 3] Embedding child chunks into ChromaDB...")
    embeddings_model = CohereEmbeddings(model="embed-english-v3.0")
    vector_db = Chroma(
        persist_directory=db_folder,
        embedding_function=embeddings_model
    )
    
    batch_size = 10
    for i in range(0, len(all_child_docs), batch_size):
        batch = all_child_docs[i : i + batch_size]
        vector_db.add_documents(documents=batch)
        if i + batch_size < len(all_child_docs):
            time.sleep(1) # Reduced sleep for single doc since Cohere limits are forgiving
            
    print(f"  SUCCESS! {filename} embedded ({len(all_child_docs)} chunks added).")

def delete_candidate(filename: str):
    """Purges a candidate from ChromaDB, JSON docstore, and local parsed/resume data."""
    load_dotenv()
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    db_folder    = os.path.join(script_dir, "chroma_db")
    store_folder = os.path.join(script_dir, "parent_docstore")
    parsed_dir   = os.path.join(script_dir, "Parsed data")
    raw_dir      = os.path.join(script_dir, "Resume data")
    
    # 1. Delete from ChromaDB
    print(f"\n[DELETE] Purging '{filename}' from ChromaDB...")
    try:
        embeddings_model = CohereEmbeddings(model="embed-english-v3.0")
        vector_db = Chroma(persist_directory=db_folder, embedding_function=embeddings_model)
        
        # We must find the distinct IDs associated with this source
        results = vector_db.get(where={"source": filename})
        if results and results.get('ids'):
            vector_db._collection.delete(ids=results['ids'])
            print(f"  Deleted {len(results['ids'])} child chunks from VectorDB.")
        else:
            print("  No child chunks found for this candidate.")
    except Exception as e:
        print(f"  Error deleting from ChromaDB: {e}")

    # 2. Delete from parent_docstore
    print(f"[DELETE] Purging '{filename}' from Parent Docstore...")
    if os.path.exists(store_folder):
        deleted_parents = 0
        for fname in os.listdir(store_folder):
            if fname.endswith(".json"):
                fpath = os.path.join(store_folder, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("metadata", {}).get("source") == filename:
                        os.remove(fpath)
                        deleted_parents += 1
                except Exception:
                    pass
        print(f"  Deleted {deleted_parents} parent JSON files.")

    # 3. Delete .md file
    md_path = os.path.join(parsed_dir, filename)
    if os.path.exists(md_path):
        os.remove(md_path)
        print(f"  [DELETE] Removed parsed file: {filename}")

    # 4. Delete .pdf file
    pdf_filename = filename.replace('.md', '.pdf')
    pdf_path = os.path.join(raw_dir, pdf_filename)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        print(f"  [DELETE] Removed raw resume: {pdf_filename}")
        
    print(f"✅ Successfully wiped '{filename}' from the system.")

def generate_embeddings():
    """Builds the Parent-Child vector database for all files in Parsed data."""
    print("=" * 60)
    print("  PARENT-CHILD CHUNKING PIPELINE")
    print("=" * 60)

    script_dir   = os.path.dirname(os.path.abspath(__file__))
    parsed_dir   = os.path.join(script_dir, "Parsed data")

    if not os.path.exists(parsed_dir):
        print("ERROR: 'Parsed data' folder not found. Run Parsing.py first!")
        return

    md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
    if not md_files:
        print("ERROR: No .md files found. Run Parsing.py first!")
        return

    for filename in md_files:
        md_file_path = os.path.join(parsed_dir, filename)
        embed_single_resume(md_file_path)
        
    print(f"\n{'='*60}\n  ALL DONE!\n{'='*60}")

if __name__ == "__main__":
    generate_embeddings()
