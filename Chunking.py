import os
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

def chunk_markdown_files():
    # Get the directory where this script lives
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(script_dir, "Parsed data")
    
    # Let's make sure we have files to chunk
    if not os.path.exists(input_folder):
        print("Error: Could not find 'Parsed data' folder!")
        return
        
    md_files = [f for f in os.listdir(input_folder) if f.endswith('.md')]
    if not md_files:
        print("No markdown files found to chunk.")
        return

    print(f"Found {len(md_files)} markdown files. Preparing the Chunker...")

    # --- THE APPROACH ---
    # Phase 1: Logical Chunking (by Headers)
    # We tell the splitter to look for Markdown headers (#, ##, ###)
    # This keeps related concepts together (e.g., everything under "Education" stays together).
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)

    # Phase 2: Size Limit Chunking (if a section is too big)
    # If a section under a header is massively long, we still need to break it down.
    # chunk_size: Max characters per chunk 
    # chunk_overlap: Characters shared between chunks so we don't lose context if a sentence is cut in half
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    all_chunks = []

    # Process each file
    for filename in md_files:
        print(f"\nChunking '{filename}'...")
        file_path = os.path.join(input_folder, filename)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Step 1: Split by headers
        header_splits = markdown_splitter.split_text(markdown_content)
        
        # Step 2: Ensure no chunk is too large
        final_chunks = text_splitter.split_documents(header_splits)
        
        # We also need to remember WHICH document this chunk came from, 
        # so we inject the filename into the metadata of each chunk!
        for chunk in final_chunks:
            chunk.metadata['source'] = filename
            all_chunks.append(chunk)
            
        print(f"  -> Sliced into {len(final_chunks)} chunks.")

    print(f"\n✅ Total chunks created across all documents: {len(all_chunks)}")
    print("\nSneak peek at a random chunk:")
    print("-" * 50)
    # Print the content
    print(all_chunks[3].page_content[:200] + "...") 
    # Print the metadata (what headers it belonged to, what file it came from)
    print("\nMetadata attached to this chunk:")
    print("-" * 50)

    # Return the chunks so Step 3 can use them!
    return all_chunks

if __name__ == "__main__":
    chunk_markdown_files()
