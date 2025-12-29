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
from google.genai import types
from google.adk.agents import Agent
from .instructions import return_instructions_bigquery
from dotenv import load_dotenv
from .tools import get_bigquery_toolset
from .callback import callback_after_tool, callback_before_agent, callback_after_model

current_file_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file_path))
abs_path = os.path.join(project_root, '.env')

# Load environment variables from a .env file for local development
load_dotenv(dotenv_path=abs_path)

# Call the function to create the BigQueryToolset instance.
bigquery_toolset = get_bigquery_toolset()

root_agent = Agent(
    model=os.getenv("DATA_AGENT_MODEL","gemini-2.5-flash"),
    name=os.getenv("AGENT_DISPLAY_NAME","Data_Agent"),
    description=os.getenv("AGENT_DESCRIPTION", "An agent that can answer questions about data in BigQuery."),
    instruction=return_instructions_bigquery(),
    before_agent_callback=callback_before_agent,
    after_tool_callback=callback_after_tool,
    after_model_callback=callback_after_model,
    tools=[bigquery_toolset],
    generate_content_config=types.GenerateContentConfig(temperature=0.001)
)
