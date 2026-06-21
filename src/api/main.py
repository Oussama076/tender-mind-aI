"""FastAPI Application Entry Point for TenderMind AI.

Contains endpoints for file ingestion, RAG indexing, workflow coordination,
and proposal generation with centralized exception handling and A2UI support.
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import os
import logging
import threading
import shutil
from typing import Any, Dict, List

from src.ingestion.drive_client import download_rfp_from_drive
from src.vectorization.rag_pipeline import process_and_index_document
from src.agents.adk_orchestrator import ADKOrchestrator
from src.ingestion.auto_indexer import sync_drive_to_chroma, get_pending_rfps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TenderMind AI API", version="1.0.0")

# Setup CORS for local development with React/Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Schemas ---

class DriveIngestRequest(BaseModel):
    """Schema for Google Drive file ingestion requests."""
    file_id: str = Field(..., min_length=1, description="Google Drive File ID must not be empty")


class AnalyzeRequest(BaseModel):
    """Schema for analyzing an RFP focus area."""
    focus_area: str = Field("General requirements and deliverables", description="Key areas to focus the analysis on")
    rfp_id: str = Field(..., description="Target RFP ID")


class WriteProposalRequest(BaseModel):
    """Schema for rehydrating state to draft the final proposal."""
    analyst_output: str = Field(..., description="Raw output text from the Analyst agent")
    strategy_output: str = Field(..., description="Raw output text from the Strategy agent")
    legal_output: str = Field(..., description="Raw output text from the Legal agent")


# --- Centralized Exception Handling ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handles HTTPExceptions and returns clean, structured JSON errors."""
    logger.warning(f"HTTP exception: {exc.detail} (Status code: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches all unhandled exceptions, logs them with traceback, and returns a 500 error."""
    logger.error(f"Unhandled error occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "Internal Server Error", "message": str(exc)}
    )


# --- Routes ---

@app.get("/health")
def health_check() -> Dict[str, str]:
    """Basic health check endpoint.
    
    Returns:
        Dict[str, str]: Status key indicating system health.
    """
    return {"status": "healthy"}


@app.on_event("startup")
def verify_environment() -> None:
    """Verifies that mandatory API keys and credentials exist on startup, and spawns the auto-indexer."""
    required_vars = ["GEMINI_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        error_msg = f"CRITICAL SECURITY ERROR: Missing required environment variables: {', '.join(missing)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    logger.info("Environment variables verified successfully.")
    
    # Launch auto-indexer in a background thread so it doesn't block FastAPI startup
    logger.info("Starting Auto-Indexer background task...")
    threading.Thread(target=sync_drive_to_chroma, daemon=True).start()


@app.get("/list-rfps")
def list_rfps() -> Dict[str, Any]:
    """Returns a list of all RFPs currently available in the system.
    
    Returns:
        Dict[str, Any]: Status and a list of indexed RFPs.
    """
    pending_rfps = get_pending_rfps()
    return {"status": "success", "rfps": pending_rfps}


@app.post("/ingest/drive")
def ingest_drive_file(request: DriveIngestRequest, background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Downloads an RFP from Google Drive and indexes it via Gemini.
    
    Args:
        request: Request body containing the file_id.
        background_tasks: FastAPI background task manager.
        
    Returns:
        Dict[str, str]: Success status message and the local file path.
    """
    dest_path = download_rfp_from_drive(request.file_id)
    filename = os.path.basename(dest_path)
    success = process_and_index_document(dest_path, request.file_id, filename=filename)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to extract and index the document.")
        
    return {"status": "success", "message": "File downloaded, extracted, and indexed.", "file_path": dest_path}


@app.post("/upload/rfp")
async def upload_local_rfp(file: UploadFile = File(...)) -> Dict[str, str]:
    """Uploads a local RFP document and indexes it.
    
    Args:
        file: Multipart uploaded file.
        
    Returns:
        Dict[str, str]: Ingestion confirmation status and the derived file_id.
    """
    os.makedirs("data/raw", exist_ok=True)
    dest_path = os.path.join("data/raw", file.filename)
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    success = process_and_index_document(dest_path, file.filename, filename=file.filename)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to extract and index the document.")
        
    return {"status": "success", "message": "File uploaded and indexed.", "file_id": file.filename}


@app.post("/analyze")
def analyze_rfp(request: AnalyzeRequest) -> Dict[str, Any]:
    """Phase 1: Runs Analyst, Strategy, and Legal agents on the RFP.
    
    Stops before writing the proposal to enforce Human-In-The-Loop review.
    
    Args:
        request: Focus area and target RFP ID.
        
    Returns:
        Dict[str, Any]: Findings from all three pre-review agents along with the A2UI payload.
    """
    orchestrator = ADKOrchestrator(rfp_id=request.rfp_id)
    state = orchestrator.execute_pre_review_pipeline(focus_area=request.focus_area)
    
    analyst_out = state.get("analyst_output", "")
    legal_out = state.get("legal_output", "")
    
    from src.agents.a2ui_converter import generate_a2ui_payload
    a2ui_data = generate_a2ui_payload(analyst_out, legal_out)
    
    return {
        "status": "success",
        "analyst_findings": analyst_out,
        "strategy_assessment": state.get("strategy_output", ""),
        "legal_review": legal_out,
        "a2ui": a2ui_data
    }


@app.post("/write_proposal")
def write_proposal(request: WriteProposalRequest) -> Dict[str, Any]:
    """Phase 2: Runs Bid Writer agent after human approval of pre-review outputs.
    
    Args:
        request: Pre-review outputs to feed as context.
        
    Returns:
        Dict[str, Any]: The finalized drafted bid proposal text.
    """
    initial_state = {
        "analyst_output": request.analyst_output,
        "strategy_output": request.strategy_output,
        "legal_output": request.legal_output,
        "writer_output": None
    }
    orchestrator = ADKOrchestrator(initial_state=initial_state)
    state = orchestrator.execute_post_review_pipeline()
    
    return {
        "status": "success",
        "final_proposal": state.get("writer_output", "")
    }
