import os
import logging
import chromadb
from google import genai
from src.vectorization.rag_pipeline import GeminiEmbeddingFunction, chunk_markdown

logger = logging.getLogger(__name__)

DB_PATH = "data/db"
CORPORATE_COLLECTION_NAME = "corporate_knowledge"
CORPORATE_DATA_DIR = "data/corporate"

def get_corporate_chroma_collection():
    """Initializes and returns the dedicated Corporate Knowledge ChromaDB collection."""
    os.makedirs(DB_PATH, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    
    emb_fn = GeminiEmbeddingFunction()
    
    collection = chroma_client.get_or_create_collection(
        name=CORPORATE_COLLECTION_NAME,
        embedding_function=emb_fn
    )
    return collection

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception

def is_retryable_error(exception):
    err_str = str(exception)
    return "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str

@retry(wait=wait_exponential(multiplier=1.5, min=10, max=60), stop=stop_after_attempt(5), retry=retry_if_exception(is_retryable_error))
def generate_content_with_retry(client, model, contents):
    logger.info(f"Generating content with {model} (with retry logic)...")
    return client.models.generate_content(model=model, contents=contents)

def extract_corporate_document(file_path: str) -> str:
    """Uses Gemini 3.5 Flash Multimodal to extract corporate content as structured markdown."""
    logger.info(f"Uploading {file_path} to Gemini for native corporate extraction...")
    client = genai.Client()
    
    try:
        uploaded_file = client.files.upload(file=file_path)
        
        prompt = "You are a corporate knowledge extractor. Read this document carefully. Extract all text, preserving tables, lists, methodologies, and pricing details. Output the entire content as clean, structured Markdown."
        
        response = generate_content_with_retry(
            client,
            model='gemini-3.1-flash-lite',
            contents=[uploaded_file, prompt]
        )
        
        logger.info(f"Extraction complete for {file_path}.")
        return response.text
    except Exception as e:
        logger.error(f"Failed to extract corporate document using Gemini: {e}")
        return ""

def process_and_index_corporate_documents():
    """Batch processes all documents in data/corporate/ and indexes them."""
    os.makedirs(CORPORATE_DATA_DIR, exist_ok=True)
    collection = get_corporate_chroma_collection()
    
    files = [f for f in os.listdir(CORPORATE_DATA_DIR) if f.endswith(('.pdf', '.docx', '.doc'))]
    
    if not files:
        logger.info("No corporate documents found in data/corporate/")
        return False
        
    for file_name in files:
        file_path = os.path.join(CORPORATE_DATA_DIR, file_name)
        doc_id = file_name.replace(" ", "_").lower()
        
        # 1. Native Extraction
        markdown_text = extract_corporate_document(file_path)
        if not markdown_text:
            continue
            
        # 2. Chunking
        chunks = chunk_markdown(markdown_text)
        logger.info(f"Created {len(chunks)} chunks for {file_name}.")
        
        # 3. Vectorization and Indexing
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"doc_id": doc_id, "chunk_index": i, "source": "corporate_memory"} for i in range(len(chunks))]
        
        logger.info(f"Indexing chunks for {file_name} into corporate_knowledge collection...")
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
    
    logger.info("Corporate Vectorization & Indexing complete.")
    return True

if __name__ == "__main__":
    process_and_index_corporate_documents()
