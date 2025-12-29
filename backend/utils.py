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
from google.cloud import bigquery
import datetime
from dotenv import load_dotenv

current_file_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file_path))
abs_path = os.path.join(project_root, '.env')

# Load environment variables from a .env file for local development
load_dotenv(dotenv_path=abs_path)

PROJECT_ID = os.getenv("BQ_DATA_PROJECT_ID", "")
DATASET_NAME = os.getenv("BQ_DATASET_NAME", "")

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def get_table_description(table_name: str) -> str:
    """Fetches the description for a given table from BigQuery."""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.{DATASET_NAME}.{table_name}"
        table = client.get_table(table_id)
        return table.description or "No description available for this table."
    except Exception as e:
        logging.error(f"Error fetching table description for {table_name}: {e}")
        return "Error fetching table description."

# --- ADDED: Function to get detailed schema for a table ---
def get_table_schema(table_name: str) -> list[dict]:
    """Fetches the detailed schema (name, type, description) for a given table."""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.{DATASET_NAME}.{table_name}"
        table = client.get_table(table_id)
        schema_info = []
        for field in table.schema:
            schema_info.append({
                "name": field.name,
                "type": field.field_type,
                "description": field.description or "N/A"
            })
        return schema_info
    except Exception as e:
        logging.error(f"Error fetching table schema for {table_name}: {e}")
        return []


def get_table_ddl_strings() -> list[dict]:
    """Fetches the DDL strings for all base tables in the dataset."""
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
        SELECT table_name, ddl
        FROM `{PROJECT_ID}.{DATASET_NAME}.INFORMATION_SCHEMA.TABLES`
        WHERE table_type = 'BASE TABLE'
        ORDER BY table_name;
    """
    try:
        query_job = client.query(query)
        return [dict(row.items()) for row in query_job.result()]
    except Exception as e:
        logging.error(f"Failed to fetch DDL strings: {e}")
        return []

def get_total_rows(table_name: str) -> int:
    """Fetches the total number of rows for a given table."""
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_NAME}.{table_name}`"
    try:
        query_job = client.query(query)
        return list(query_job.result())[0][0]
    except Exception as e:
        logging.error(f"Error fetching total rows for {table_name}: {e}")
        return 0

def get_total_column_count() -> int:
    """Fetches the total number of columns across all tables."""
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_NAME}.INFORMATION_SCHEMA.COLUMNS`"
    try:
        query_job = client.query(query)
        return list(query_job.result())[0][0]
    except Exception as e:
        logging.error(f"Error fetching total column count: {e}")
        return 0

def fetch_sample_data_for_single_table(table_name: str, num_rows: int = 3) -> list[dict]:
    """Fetches a few sample rows from a specific table."""
    client = bigquery.Client(project=PROJECT_ID)
    full_table_name = f"{PROJECT_ID}.{DATASET_NAME}.{table_name}"
    try:
        rows_iterator = client.list_rows(full_table_name, max_results=num_rows)
        return [dict(row.items()) for row in rows_iterator]
    except Exception as e:
        logging.error(f"Error fetching sample data for table {full_table_name}: {e}")
        return []