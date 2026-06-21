# TenderMind AI - Enterprise RFP Automation Suite

An enterprise-grade RFP automation platform powered by a Multi-Agent Swarm (Analyst, Strategy, Legal, Writer) and Dual-RAG architecture. TenderMind AI intelligently analyzes technical requirements, evaluates strategic Go/No-Go alignment, and generates compliant proposals with strict Human-in-the-Loop governance.

## Architecture Overview

The system operates on an end-to-end, fully decoupled data pipeline:

1. **Acquisition:** Securely connects to Google Drive via a Service Account (or accepts local uploads) to ingest targeted RFP PDFs/Docx files.
2. **Native Multimodal Extraction:** Utilizing Gemini 1.5 Flash, the raw documents are natively processed, preserving complex structural integrity (tables, lists, hierarchies) and converting them into clean Markdown.
3. **Dual-Vector Database Strategy:** To prevent hallucination and ensure data privacy, TenderMind AI enforces strict separation of context via two isolated ChromaDB collections, embedded using Google's `models/text-embedding-004`:
   - **Client RFP Database:** Contains vectorized chunks of the specific client's RFP.
   - **Corporate Memory Database:** A dedicated collection containing historical company data, past proposals, and corporate capabilities.
4. **Agentic Pipeline (Swarm Architecture):** Leverages a 4-agent orchestration system managed by a custom `ADKOrchestrator` using the `google-genai` SDK:
   - **Analyst Agent:** Extracts technical specifications and mandatory requirements.
   - **Strategy Agent:** Performs a strategic Go/No-Go alignment check by cross-referencing RFP requirements against the Corporate Memory.
   - **Legal/Compliance Agent:** Reviews extracted specs to flag potential compliance constraints and legal risks.
   - **Bid Writer Agent:** Synthesizes the Analyst's specs, Strategy assessment, and Legal Agent's risk report to generate a highly professional, structured proposal.

## Prerequisites

Before deploying the application, ensure you have the following installed:
- **Python 3.11+**
- **Node.js 18+** (for frontend execution without Docker)
- **Docker & Docker Compose** (optional, for containerized execution)
- **Google Cloud Service Account** (with Google Drive API enabled)
- **Google Gemini API Key**

## Installation & Configuration

### Step 1: Clone the Repository
```bash
git clone https://github.com/Oussama076/tender-mind-aI.git
cd tender-mind-aI
```

### Step 2: Configure Environment Variables
Create a `.env` file in the root directory and populate it:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
DRIVE_RFP_FOLDER_ID=your_rfp_folder_id_here
DRIVE_CORPORATE_FOLDER_ID=your_corporate_folder_id_here
```

### Step 3: Google Drive & Credentials
- Place your Service Account JSON key in the root directory and name it `credentials.json`.
- Create two folders in Google Drive: one for RFPs and one for Corporate Memory. Update the `.env` file with their IDs.

---

## Running Locally (Without Docker)

To run the project natively, you must start the backend and frontend separately.

### 1. Start the FastAPI Backend
Open a terminal in the root directory:
```bash
# Create and activate a virtual environment
python -m venv venv
# On Windows: .\venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --env-file .env
```
The backend API will be available at `http://localhost:8000`.

### 2. Start the React Frontend
Open a new terminal and navigate to the `frontend` directory:
```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
Access the application UI via `http://localhost:5173`.

---

## Running Locally (With Docker)

If you prefer a fully containerized environment, you can use Docker Compose to spin up both the frontend and backend simultaneously.

```bash
docker-compose up --build
```
- The **Frontend** will be available at `http://localhost:5173`.
- The **Backend API** will be available at `http://localhost:8000`.

---

## Security Features

TenderMind AI was built with a "Defense in Depth" security philosophy:

- **Human-In-The-Loop (HITL) Guardrails:** The ADK Orchestrator halts execution after the Legal Agent concludes its analysis. The user is presented with the Analyst Findings, Strategic Alignment, and Legal Risks. The Bid Writer Agent is fundamentally blocked from executing until explicit human approval is received.
- **State Isolation:** Agents cannot corrupt each other's memory. State mutations are managed strictly by the Orchestrator.
- **Fail-Fast Startup:** The backend validates the presence of critical environment variables (`GEMINI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`) on startup, preventing the application from running in an insecure state.
- **Input Validation:** All FastAPI endpoints utilize Pydantic field validators to strictly reject malformed requests.
