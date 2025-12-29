# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from typing import Dict, Any
from typing import Optional
import json, logging
from google.adk.agents.callback_context import CallbackContext
from datetime import date
from .instructions import return_instructions_bigquery
from typing import Optional
from google.adk.models import LlmResponse
import copy
from google.genai import types

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def callback_before_agent(callback_context: CallbackContext) -> None:
    """
    Pre-processing callback executed before an agent is called.

    At the start of a new session, this function dynamically gets the current date
    and prepends it to the agent's instructions. This ensures the agent is always
    aware of the current date.
    """

    if "session_initialized" not in callback_context.state:
        callback_context.state["session_initialized"] = "true"

        date_today = date.today()

        callback_context._invocation_context.agent.instruction = (
                f""" today's date : {date_today} (UTC). """ + return_instructions_bigquery()
        )
    return None


def callback_after_tool(tool: BaseTool, 
                        args: Dict[str, Any], 
                        tool_context: ToolContext, 
                        tool_response: Dict
                        ) -> Optional[Dict]:
    """
    Post-processing callback executed after a tool has been called.

    If the executed tool was 'execute_sql', this function retrieves the query
    result from the tool's response and saves it into the `tool_context.state`.
    This makes the query result available to subsequent tools, specifically for the visualization agent to use.

    Args:
        tool (BaseTool): The tool instance that was called.
        args (Dict[str, Any]): The arguments passed to the tool.
        tool_context (ToolContext): The context containing agent and tool information.
        tool_response (Dict): The response returned by the tool.

    Returns:
        Optional[Dict]: A modified tool response dictionary if changes are made, or None to use the original response.
    """

    # Get the contextual information from CallbackContext
    agent_name = tool_context.agent_name
    tool_name = tool.name

    print(f"[After Tool] Tool call for tool '{tool_name}' in agent '{agent_name}' and args: {args}, tool_response: {tool_response}")

    if tool_name == "execute_sql" and "rows" in tool_response:
        query_result  = tool_response.get('rows',[])
        tool_context.state['query_result'] = query_result

    return None

# --- Define the Callback Function ---
def callback_after_model(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    After the model responds, this callback replaces any '~' characters
    in the response text with '-'.
    """
    if not (
        llm_response.content
        and llm_response.content.parts
        and llm_response.content.parts[0].text
    ):
        return None

    original_text = llm_response.content.parts[0].text
    modified_text = original_text.replace("~", "-")

    if original_text == modified_text:
        return None

    modified_parts = [copy.deepcopy(part) for part in llm_response.content.parts]
    modified_parts[0].text = modified_text

    new_response = LlmResponse(
        content=types.Content(role="model", parts=modified_parts),
        grounding_metadata=llm_response.grounding_metadata,
    )

    return new_response