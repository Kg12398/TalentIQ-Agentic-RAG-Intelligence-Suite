import os
from dotenv import load_dotenv
from llama_parse import LlamaParse
import nest_asyncio

# We have to do this so that standard Python scripts can handle the complex "async" 
# (background) tasks that LlamaParse does under the hood. 
try:
    nest_asyncio.apply()
except Exception as e:
    # On some platforms like Streamlit Cloud with specific event loop policies,
    # nest_asyncio might fail to patch. We catch it here to prevent app crash.
    print(f"Note: nest_asyncio could not be applied: {e}")

__parser_instance = None

def get_parser():
    global __parser_instance
    if __parser_instance is None:
        print("Loading API keys from .env...")
        load_dotenv()
        print("Initializing LlamaParse...")
        __parser_instance = LlamaParse(result_type="markdown")
    return __parser_instance

def parse_single_resume(file_path: str) -> str:
    """Parses a single PDF and saves it as Markdown. Returns the path to the saved .md file."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    parser = get_parser()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, "Parsed data")
    os.makedirs(output_folder, exist_ok=True)
    
    filename = os.path.basename(file_path)
    print(f"\nSending '{filename}' to LlamaParse servers...")
    
    try:
        # 🛡️ SENIOR-GRADE ASYNC HANDLING
        # LlamaParse.load_data is a synchronous wrapper around an async call.
        # On Streamlit Cloud, nest_asyncio often fails. We use a ThreadPoolExecutor
        # to run the parsing in a separate thread, which gets its own clean event loop.
        def _parse():
            return parser.load_data(file_path)

        with ThreadPoolExecutor() as executor:
            future = executor.submit(_parse)
            documents = future.result()
            
    except Exception as e:
        print(f"Failed to parse {filename}: {e}")
        raise e
        
    output_filename = filename.replace('.pdf', '.md')
    output_path = os.path.join(output_folder, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for doc in documents:
            f.write(doc.text + "\n\n")
            
    print(f"Successfully saved as '{output_filename}'! 🎊")
    return output_path

def parse_resumes():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(script_dir, "Resume data")
    
    if not os.path.exists(input_folder):
        print("Resume data folder not found.")
        return
        
    pdf_files = [f for f in os.listdir(input_folder) if f.endswith('.pdf')]
    print(f"Found {len(pdf_files)} resumes to parse!")
    
    for filename in pdf_files:
        file_path = os.path.join(input_folder, filename)
        parse_single_resume(file_path)
        
    print("\n✅ All resumes parsed successfully! Go look inside the 'Parsed data' folder.")

if __name__ == "__main__":
    parse_resumes()
