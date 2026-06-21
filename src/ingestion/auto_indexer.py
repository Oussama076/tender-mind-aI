import os
import logging
import asyncio

from src.ingestion.drive_client import list_files_in_folder, download_rfp_from_drive
from src.vectorization.rag_pipeline import process_and_index_document, get_chroma_collection
from src.vectorization.corporate_rag import extract_corporate_document, chunk_markdown, get_corporate_chroma_collection

logger = logging.getLogger(__name__)

def is_file_indexed(collection, file_id: str) -> bool:
    """Checks if a file_id already exists in the given ChromaDB collection."""
    results = collection.get(where={"doc_id": file_id})
    return bool(results and results.get("ids"))

def sync_drive_to_chroma():
    """Scans Google Drive folders and idempotently indexes new PDFs/Docx into ChromaDB."""
    logger.info("Starting Auto-Indexer sync...")
    
    rfp_folder_id = os.getenv("DRIVE_RFP_FOLDER_ID")
    corporate_folder_id = os.getenv("DRIVE_CORPORATE_FOLDER_ID")
    
    if not rfp_folder_id or not corporate_folder_id:
        logger.warning("Auto-Indexer skipped: DRIVE_RFP_FOLDER_ID or DRIVE_CORPORATE_FOLDER_ID not set.")
        return

    # 1. Sync RFPs
    try:
        rfp_collection = get_chroma_collection()
        rfp_files = list_files_in_folder(rfp_folder_id)
        
        for file in rfp_files:
            file_id = file.get("id")
            file_name = file.get("name")
            
            if not is_file_indexed(rfp_collection, file_id):
                logger.info(f"New RFP detected: {file_name}")
                dest_path = download_rfp_from_drive(file_id, destination_folder="data/raw")
                process_and_index_document(dest_path, file_id, filename=file_name)
    except Exception as e:
        logger.error(f"Error syncing RFPs: {e}")

    # 2. Sync Corporate Memory
    try:
        corp_collection = get_corporate_chroma_collection()
        corp_files = list_files_in_folder(corporate_folder_id)
        
        for file in corp_files:
            file_id = file.get("id")
            file_name = file.get("name")
            
            # The corporate_rag uses filename without spaces as doc_id, but for consistency with drive we should use file_id
            if not is_file_indexed(corp_collection, file_id):
                logger.info(f"New Corporate Document detected: {file_name}")
                dest_path = download_rfp_from_drive(file_id, destination_folder="data/corporate")
                
                # Inline extraction and indexing for corporate docs using file_id as doc_id
                markdown_text = extract_corporate_document(dest_path)
                if markdown_text:
                    chunks = chunk_markdown(markdown_text)
                    ids = [f"{file_id}_chunk_{i}" for i in range(len(chunks))]
                    metadatas = [{"doc_id": file_id, "chunk_index": i, "source": "corporate_memory", "filename": file_name} for i in range(len(chunks))]
                    
                    corp_collection.add(documents=chunks, metadatas=metadatas, ids=ids)
                    logger.info(f"Successfully indexed Corporate Document: {file_name}")
    except Exception as e:
        logger.error(f"Error syncing Corporate Memory: {e}")
        
    logger.info("Auto-Indexer sync complete.")

def get_pending_rfps() -> list[dict]:
    """Returns a list of unique RFPs with name and id currently indexed in the RFP collection."""
    try:
        collection = get_chroma_collection()
        results = collection.get(include=["metadatas"])
        
        metadatas = results.get("metadatas", [])
        # Build a deduplicated map of doc_id -> filename
        seen: dict[str, str] = {}
        for meta in metadatas:
            if meta and meta.get("doc_id"):
                doc_id = meta["doc_id"]
                if doc_id not in seen:
                    seen[doc_id] = meta.get("filename", doc_id)
        
        return [{"id": doc_id, "name": name} for doc_id, name in seen.items()]
    except Exception as e:
        logger.error(f"Error fetching pending RFPs: {e}")
        return []
