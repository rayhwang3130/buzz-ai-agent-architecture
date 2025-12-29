# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
import json
import io
import sys
import asyncio
import base64
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import pandas as pd # --- MODIFICATION: Import pandas ---

# --- Basic Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# --- Project Path Setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Environment Variable Loading ---
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    logger.info(".env file loaded.")

# --- ADK and Agent Imports ---
try:
    from data_agent.agent import root_agent
    from data_agent.agent import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
    from google.genai import types as genai_types
    logger.info("Successfully imported ADK components and agents.")
except ImportError as e:
    logger.critical(f"FATAL: Could not import required components. Error: {e}", exc_info=True)
    sys.exit(1)

# --- Pydantic Models for Request/Response Validation ---
class ChatMessagePart(BaseModel):
    text: Optional[str] = None
    inline_data: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    parts: List[ChatMessagePart]
    role: str = 'user'

class AgentRunRequest(BaseModel):
    app_name: str
    user_id: str
    session_id: Optional[str] = None
    new_message: ChatMessage


def sanitize_for_json(data):
    """Recursively sanitizes data to be JSON serializable."""
    if isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(i) for i in data]
    elif isinstance(data, bytes):
        return base64.b64encode(data).decode('utf-8')
    elif isinstance(data, set):
        return list(data)
    return data

class DataAgentWebServer:
    """
    A class that encapsulates the FastAPI application, services, and runners for both agents.
    """
    def __init__(self, data_agent, session_service, artifact_service):
        self.session_service = session_service
        self.artifact_service = artifact_service
        self.app_name = "data_agent_chatbot"
        
        self.data_agent_runner = Runner(
            app_name="data_agent_chatbot",
            agent=data_agent,
            session_service=self.session_service,
            artifact_service=self.artifact_service,
        )
        self.data_agent_runner = Runner(
            app_name="data_agent_chatbot",
            agent=data_agent,
            session_service=self.session_service,
            artifact_service=self.artifact_service,
        )
        logger.info("DataAgentWebServer initialized with data runner.")

    def get_fast_api_app(self):
        """Creates and configures the FastAPI application instance."""
        app = FastAPI(title="Data Agent Chatbot API")

        # --- API Routes ---
        @app.post("/api/run_sse")
        async def agent_run_sse(req: AgentRunRequest):
            """Handles chat requests with server-sent events (SSE)."""
            async def event_generator():
                session_id = req.session_id
                try:
                    if session_id:
                        session = await self.session_service.get_session(app_name=req.app_name, user_id=req.user_id, session_id=session_id)
                        if not session:
                            session = await self.session_service.create_session(app_name=req.app_name, user_id=req.user_id)
                            session_id = session.id
                    else:
                        session = await self.session_service.create_session(app_name=req.app_name, user_id=req.user_id)
                        session_id = session.id

                    session_event = json.dumps({'session_id': session_id})
                    yield f"data: {session_event}\n\n"

                    processed_parts = []
                    for part_data in req.new_message.parts:
                        if part_data.inline_data:
                            mime_type = part_data.inline_data.get('mime_type')
                            data_b64 = part_data.inline_data.get('data')

                            excel_mimes = [
                                'application/vnd.ms-excel',
                                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            ]

                            if mime_type in excel_mimes:
                                try:
                                    decoded_data = base64.b64decode(data_b64)
                                    df = pd.read_excel(io.BytesIO(decoded_data))
                                    csv_data = df.to_csv(index=False)
                                    
                                    # Replace the file part with a text part containing CSV data
                                    processed_parts.append({
                                        "text": f"The user uploaded an Excel file. Here is its content in CSV format:\n\n---\n{csv_data}\n---"
                                    })
                                    logger.info("Successfully converted an uploaded Excel file to CSV.")
                                except Exception as e:
                                    logger.error(f"Failed to process Excel file: {e}")
                                    processed_parts.append({
                                        "text": "(System error: Could not read the uploaded Excel file.)"
                                    })
                                continue # Move to the next part
                        
                        # If it's not an excel file or has no inline_data, add it as is
                        processed_parts.append(part_data.model_dump(exclude_none=True))
                    
                    new_message = genai_types.Content(parts=processed_parts, role='user')

                    async_generator = self.data_agent_runner.run_async(user_id=req.user_id, session_id=session_id, new_message=new_message)

                    async for event in async_generator:
                        event_dict = event.model_dump(exclude_none=True)
                        logger.debug(f"Raw event from runner: {event_dict}")

                        if event_dict.get('content'):
                            for part in event_dict['content'].get('parts', []):
                                if 'code_execution_result' in part and part['code_execution_result'].get('artifacts'):
                                    artifact_delta = {
                                        artifact_info.get('name'): str(artifact_info.get('version', 0))
                                        for artifact_info in part['code_execution_result']['artifacts']
                                        if artifact_info.get('name')
                                    }
                                    if artifact_delta:
                                        signal_event = {"actions": {"artifact_delta": artifact_delta}}
                                        logger.info(f"ARTIFACT DETECTED. Sending signal: {signal_event}")
                                        yield f"data: {json.dumps(signal_event)}\n\n"

                        sanitized_event = json.dumps(sanitize_for_json(event_dict))
                        yield f"data: {sanitized_event}\n\n"

                except Exception as e:
                    logger.error(f"Error during agent execution: {e}", exc_info=True)
                    error_event = json.dumps({'error': str(e)})
                    yield f"data: {error_event}\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")

        @app.get("/api/users/{user_id}/sessions/{session_id}/artifacts/{artifact_id}/versions/{version_id}")
        async def get_artifact(user_id: str, session_id: str, artifact_id: str, version_id: int):
            try:
                artifact_part = await self.artifact_service.load_artifact(
                    app_name=self.app_name, user_id=user_id, session_id=session_id,
                    filename=artifact_id, version=version_id
                )
                if not artifact_part or not hasattr(artifact_part, 'inline_data'):
                    raise HTTPException(status_code=404, detail="Artifact not found")
                return Response(content=artifact_part.inline_data.data, media_type=artifact_part.inline_data.mime_type)
            except Exception as e:
                logger.error(f"Error serving artifact {artifact_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/api/suggested-questions")
        async def get_suggested_questions():
            json_path = os.path.join(os.path.dirname(__file__), 'suggested_questions.json')
            return FileResponse(json_path)
        
        @app.get("/api/tables")
        async def list_tables():
            from backend.utils import get_table_ddl_strings, get_total_rows, get_total_column_count
            try:
                tables = get_table_ddl_strings()
                table_names = [table["table_name"] for table in tables]
                total_rows = sum(get_total_rows(name) for name in table_names)
                total_columns = get_total_column_count()
                return JSONResponse(content={
                    "tables": table_names,
                    "num_tables": len(table_names),
                    "total_columns": total_columns,
                    "total_rows": total_rows
                })
            except Exception as e:
                logger.error(f"Error listing tables: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        @app.get("/api/table_data")
        async def get_table_data(table_name: str):
            try:
                from backend.utils import get_table_description, fetch_sample_data_for_single_table, json_serial
                sample_rows = fetch_sample_data_for_single_table(table_name=table_name)
                table_description = get_table_description(table_name)

                content = {
                    "data": sample_rows,
                    "description": table_description
                }
                json_content = json.dumps(content, default=json_serial)
                return Response(content=json_content, media_type="application/json")

            except Exception as e:
                logger.error(f"Error getting table data for '{table_name}': {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        @app.get("/api/table_schema")
        async def get_table_schema_endpoint(table_name: str):
            try:
                from backend.utils import get_table_schema
                schema_info = get_table_schema(table_name=table_name)
                if not schema_info:
                    raise HTTPException(status_code=404, detail="Schema not found or table does not exist.")
                return JSONResponse(content={"schema": schema_info})
            except Exception as e:
                logger.error(f"Error getting table schema for '{table_name}': {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


        @app.get("/api/code")
        async def get_code_file(filepath: str):
            if not filepath:
                raise HTTPException(status_code=400, detail="Filepath is required")

            if not filepath.startswith("data_agent/"):
                logger.warning(f"Access to disallowed file attempted: {filepath}")
                raise HTTPException(status_code=400, detail="Invalid filepath")

            abs_filepath = os.path.normpath(os.path.join(project_root, filepath))
            if not abs_filepath.startswith(os.path.join(project_root, "data_agent")):
                logger.warning(f"Attempted directory traversal: {filepath}")
                raise HTTPException(status_code=400, detail="Invalid filepath")

            try:
                with open(abs_filepath, 'r') as f:
                    content = f.read()
                return JSONResponse(content={"content": content})
            except FileNotFoundError:
                logger.error(f"Code file not found: {filepath}")
                raise HTTPException(status_code=404, detail="File not found")
            except Exception as e:
                logger.error(f"Error reading code file {filepath}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


        # --- Static File Serving for React App ---
        build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build'))
        if os.path.exists(build_dir):
            app.mount("/static", StaticFiles(directory=os.path.join(build_dir, "static")), name="static")
            @app.get("/{full_path:path}")
            async def serve_react_app(request: Request, full_path: str):
                index_path = os.path.join(build_dir, 'index.html')
                if not os.path.exists(index_path):
                    raise HTTPException(status_code=404, detail="React app index.html not found.")
                return FileResponse(index_path)
        else:
            logger.critical(f"React build directory not found at {build_dir}. The UI will not be served.")

        return app

# --- Application Entry Point ---
server = DataAgentWebServer(
    data_agent=root_agent,
    session_service=InMemorySessionService(),
    artifact_service=InMemoryArtifactService()
)
app = server.get_fast_api_app()

if __name__ == '__main__':
    import uvicorn
    logger.info("Starting Uvicorn server for local development.")
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=port, reload=True)
