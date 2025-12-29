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

import logging, os
import google.auth
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig 
from google.adk.auth.auth_credential import AuthCredentialTypes
from google.adk.tools.bigquery.bigquery_credentials import BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import WriteMode

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

DISPLAY_NAME = os.getenv("AGENT_DISPLAY_NAME", "Data Agent")
BQ_CREDENTIALS_TYPE=os.getenv("BQ_CREDENTIALS_TYPE","None")
BQ_COMPUTE_PROJECT_ID=os.getenv("BQ_COMPUTE_PROJECT_ID")
OAUTH_CLIENT_ID=os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET=os.getenv("OAUTH_CLIENT_SECRET")

def get_bigquery_toolset() -> BigQueryToolset:
    """Initializes and returns a BigQueryToolset.
    Bigquery tool source code : https://github.com/google/adk-python/tree/main/src/google/adk/tools/bigquery
    """
    logger.info(f"[{DISPLAY_NAME}] --- Initiating bigquery toolset ---")
    # Define an appropriate credential type
    if BQ_CREDENTIALS_TYPE == "OAUTH2":
        CREDENTIALS_TYPE = AuthCredentialTypes.OAUTH2
    else:
        CREDENTIALS_TYPE = None

    if CREDENTIALS_TYPE == AuthCredentialTypes.OAUTH2:
        # Initiaze the tools to do interactive OAuth
        # The environment variables OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET
        # must be set
        credentials_config = BigQueryCredentialsConfig(
            client_id=OAUTH_CLIENT_ID,
            client_secret=OAUTH_CLIENT_SECRET,
        )
    else:
        # Initialize the tools to use the application default credentials.
        # https://cloud.google.com/docs/authentication/provide-credentials-adc
        application_default_credentials, _ = google.auth.default()
        credentials_config = BigQueryCredentialsConfig(
            credentials=application_default_credentials
        )

    bq_tool_config = BigQueryToolConfig(
        write_mode=WriteMode.BLOCKED, # This config makes the tool read-only.(default mode) If you want to allow write operations, change it to WriteMode.ALLOWED
        compute_project_id=BQ_COMPUTE_PROJECT_ID #GCP project ID to use for the BigQuery compute operations.  
    )

    # Create the BigQueryToolset
    bigquery_toolset = BigQueryToolset(
        bigquery_tool_config=bq_tool_config,
        credentials_config=credentials_config,
        tool_filter=["execute_sql"] # Add other tools as needed
    )

    return bigquery_toolset

