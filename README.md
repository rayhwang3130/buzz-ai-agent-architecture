# Buzz AI Agent

This project implements a Data Agent capable of analyzing social media buzz around Samsung Galaxy products using BigQuery and Vertex AI.

## Project Structure

```text
buzz-ai-agent/
├── .env                       # Environment variables (API keys, project settings)
├── 251229_final_UNPK_Test.csv # Data file with buzz/sentiment data
├── requirements.txt           # Python dependencies
├── run_local.sh               # Script to run the backend and frontend locally
├── backend/                   # FastAPI Server
│   ├── fastapi_app.py         # Main entry point for the API
│   ├── utils.py               # Backend utility functions
│   └── suggested_questions.json 
├── data_agent/                # Agent Logic
│   ├── agent.py               # Main agent class definition
│   ├── tools.py               # BigQuery and other tool definitions
│   ├── instructions.py        # Logic for fetching system instructions
│   ├── system_instructions.yaml # Prompt engineering for the agent
│   ├── custom_instructions.yaml
│   ├── utils.py               # Helper functions for data retrieval
│   └── callback.py            # Event callbacks for the agent
├── frontend/                  # React Frontend
│   ├── public/                # Static assets
│   ├── src/                   # Source code
│   │   ├── App.js             # Main React component
│   │   └── components/        # UI components
│   └── package.json           # Frontend dependencies
└── infrastructure/            # Setup and Deployment
    ├── init.sh                # Configuration for deployment variables
    ├── deploy.sh              # Script to deploy to Google Cloud Run
    └── setup_agent_infrastructure.py # Python script to setup BigQuery, Dataplex, and Vector Search
```

## Main Components

### 1. `backend/`
Contains the FastAPI server (`fastapi_app.py`) which acts as the bridge between the frontend and the agent. It manages sessions, handles chat requests, and streams responses (SSE).

### 2. `data_agent/`
Houses the core intelligence of the application.
- `agent.py`: Defines the `root_agent` and how it interacts with models.
- `tools.py`: Configures the tools the agent can use (primarily BigQuery SQL generation and execution).
- `system_instructions.yaml`: The "brain" of the agent, defining its persona (Samsung Social Data Analyst), rules (Constraints, SQL guidelines), and workflow.

### 3. `frontend/`
A React-based user interface that provides a chat-like experience. It communicates with the backend to send user queries and display the agent's responses (text, tables, SQL logs).

### 4. `infrastructure/`
Scripts to manage the underlying cloud resources.
- `setup_agent_infrastructure.py`: Automates the creation of the BigQuery table (from CSV), sets up a Dataplex Lake/Zone/Asset for governance, and backfills text embeddings for vector search.
- `deploy.sh` & `init.sh`: Used for deploying the application to Google Cloud Run.

## How to Use

### Prerequisites
1.  **Environment Setup**: Ensure you have Python 3.10+ and a Google Cloud Project.
2.  **Configuration**:
    -   Copy `.env-example` to `.env` (if not done automatically).
    -   Fill in your `GOOGLE_CLOUD_PROJECT`, `BQ_DATASET_NAME`, etc., in `.env`.

### 1. Initial Setup (One-time)
To set up your BigQuery tables, Dataplex resources, and generate embeddings:

```bash
# Activate virtual environment
source venv/bin/activate 

# Install dependencies
pip install -r requirements.txt

# Run the infrastructure setup script
python infrastructure/setup_agent_infrastructure.py
```

### 2. Running Locally
To start the agent and the UI on your machine:

```bash
./run_local.sh
```
This script will:
-   Check your `.env`.
-   Install Python dependencies.
-   Build the React frontend.
-   Start the FastAPI server at `http://localhost:8080`.

Open **http://localhost:8080** in your browser to interact with the agent.
