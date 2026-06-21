import os
import logging
import chromadb
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

DB_PATH = "data/db"
COLLECTION_NAME = "rfp_documents"

class GeminiEmbeddingFunction:
    """Custom embedding function for ChromaDB using Google GenAI SDK."""
    
    def name(self) -> str:
        return "GeminiEmbeddingFunction"
    
    def __init__(self):
        self.client = genai.Client()
        self.model_name = 'gemini-embedding-2'
        
    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            try:
                response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=text
                )
                embeddings.append(response.embeddings[0].values)
            except Exception as e:
                logger.error(f"Error embedding text: {e}")
                # Fallback to keep dimensionalities aligned
                embeddings.append([0.0] * 768) 
        return embeddings

def get_chroma_collection():
    """Initializes and returns the ChromaDB collection."""
    os.makedirs(DB_PATH, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    
    emb_fn = GeminiEmbeddingFunction()
    
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
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

def extract_pdf_to_markdown(pdf_path: str) -> str:
    """Uses Gemini 3.5 Flash Multimodal to extract PDF content as structured markdown."""
    logger.info(f"Uploading {pdf_path} to Gemini for native extraction...")
    client = genai.Client()
    
    try:
        # Upload the file
        uploaded_file = client.files.upload(file=pdf_path)
        
        prompt = "Read this document carefully. Extract all text, preserving tables, lists, and structural hierarchy. Output the entire content as clean, structured Markdown."
        
        response = generate_content_with_retry(
            client,
            model='gemini-3.1-flash-lite',
            contents=[uploaded_file, prompt]
        )
        
        logger.info("Extraction complete.")
        return response.text
    except Exception as e:
        logger.error(f"Failed to extract PDF using Gemini: {e}")
        return ""

def chunk_markdown(markdown_text: str, chunk_size: int = 1500, overlap: int = 300) -> list[str]:
    """A simplistic chunker for markdown."""
    # In a production setting, you'd use a MarkdownTextSplitter.
    chunks = []
    start = 0
    text_length = len(markdown_text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = markdown_text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
        
    return chunks

def process_and_index_document(file_path: str, doc_id: str, filename: str = ""):
    """End-to-end pipeline to extract, chunk, and index a document."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    # Derive a display name if not provided
    if not filename:
        filename = os.path.basename(file_path)
        
    # 1. Native Extraction using Gemini Multimodal
    markdown_text = extract_pdf_to_markdown(file_path)
    if not markdown_text:
        return False
        
    # 2. Chunking
    chunks = chunk_markdown(markdown_text)
    logger.info(f"Created {len(chunks)} chunks.")
    
    # 3. Vectorization and Indexing
    collection = get_chroma_collection()
    
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id, "chunk_index": i, "filename": filename} for i in range(len(chunks))]
    
    logger.info(f"Indexing chunks into ChromaDB using text-embedding-004...")
    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    logger.info("Vectorization & Indexing complete.")
    return True
