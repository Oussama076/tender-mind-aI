# TenderMind AI - Enterprise-Grade RFP Automation Suite

**TenderMind AI** is an enterprise-grade, multi-agent SaaS platform designed to automate Request for Proposal (RFP) analysis and proposal generation. Developed as a Capstone project for the Kaggle *5-Day AI Agents* course, it strictly adheres to a **Google-Maximalist** technology stack, demonstrating advanced interoperability, multi-agent orchestration, and human-in-the-loop security.

## Architecture Overview

The system operates on an end-to-end, fully decoupled data pipeline:

1. **Acquisition (MCP Server):** A Model Context Protocol (MCP) server securely connects to Google Drive via a Service Account to ingest targeted RFP PDFs/Docx files.
2. **Native Multimodal Extraction:** Utilizing Gemini 3.5 Flash, the raw documents are natively processed, preserving complex structural integrity (tables, lists, hierarchies) and converting them into clean Markdown.
3. **Dual-Vector Database Strategy:** To prevent hallucination and ensure data privacy, TenderMind AI enforces strict separation of context via two isolated ChromaDB collections, embedded using Google's `models/text-embedding-004`:
   - **Client RFP Database:** Contains vectorized chunks of the target client's RFP.
   - **Corporate Memory Database:** A dedicated collection containing historical company data, past proposals, and methodologies.
4. **Agentic Pipeline:** Leverages a 3-agent orchestration system managed by a custom `ADKOrchestrator` using the pure `google-genai` SDK:
   - **Analyst Agent:** Extracts technical specifications and mandatory requirements.
   - **Legal/Compliance Agent:** Reviews extracted specs to flag potential compliance constraints and legal risks.
   - **Bid Writer Agent:** Synthesizes the Analyst's specs and Legal Agent's risk report, querying Corporate Memory to generate a highly professional, structured proposal.

## Prerequisites

Before deploying the application, ensure you have the following installed and configured:
- **Python 3.11+**
- **Docker & Docker Compose**
- **Google Cloud Service Account** (with Google Drive API enabled)
- **Google Gemini API Key**

## Quick Start Guide

Follow these steps to transition from cloning the repository to running the full application locally.

### Step 1: Clone the Repository
```bash
git clone https://github.com/Oussama076/tender-mind-aI.git
cd tender-mind-aI
```

### Step 2: Configure Environment Variables
Create a `.env` file in the root directory and populate it with the following required variables:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
DRIVE_RFP_FOLDER_ID=your_rfp_folder_id_here
DRIVE_CORPORATE_FOLDER_ID=your_corporate_folder_id_here
```

### Step 3: Configure Google Drive & Credentials
- Place your Service Account JSON key in the root directory and name it `credentials.json` (or map it accurately in the `.env`).
- Create two distinct folders in Google Drive: one for RFPs and one for Corporate Memory. Update the `.env` file with their respective IDs.

### Step 4: Generate Mock Data (Optional)
If you are testing locally and want to populate the system with mock engineering data, run the automated setup scripts:
```bash
pip install -r requirements.txt
python scripts/generate_corporate_docs.py
python scripts/generate_rfp_docs.py
```
*Note: The auto-indexer will automatically synchronize these into ChromaDB on backend startup.*

### Step 5: Start the Platform
Start the FastAPI backend and Streamlit frontend using Docker:
```bash
docker-compose up --build
```
Access the application UI via `http://localhost:8501`.

## Security Features

TenderMind AI was built with a "Defense in Depth" security philosophy:

- **Human-In-The-Loop (HITL) Guardrails:** The ADK Orchestrator halts execution after the Legal Agent concludes its analysis. The user is presented with a prominent "⚠️ Human Validation Required" guardrail in the UI. The Bid Writer Agent is fundamentally blocked from executing until explicit human approval is received regarding the identified legal risks.
- **Fail-Fast Startup:** The backend validates the presence of critical environment variables (`GEMINI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`) on startup, preventing the application from running in an insecure state.
- **Directory Traversal Protection:** All downloaded Google Drive files are strictly sanitized (`os.path.basename`) and path-checked to ensure files are rigidly confined to their intended destination directories.
- **Input Validation:** All FastAPI endpoints utilize Pydantic field validators to strictly reject malformed requests.

## Deployment

TenderMind AI is fully containerized and **Google Cloud Run** ready. The included `Dockerfile` and multi-service architecture support immediate deployment to scalable cloud infrastructure without modification to the core business logic.
