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

import logging
import time
import os
from google.cloud import bigquery, dataplex_v1
from google.cloud.bigquery.table import TableReference
from proto.marshal.collections import maps, repeated

PROJECT_ID = os.getenv("BQ_DATA_PROJECT_ID", "")
DATASET_NAME = os.getenv("BQ_DATASET_NAME", "")
LOCATION = os.getenv("BQ_LOCATION", "")
TABLE_NAMES = os.getenv("BQ_TABLE_NAMES", "").split(",") if os.getenv("BQ_TABLE_NAMES") else []
ASPECT_TYPES = os.getenv("ASPECT_TYPES", "").split(",") if os.getenv("ASPECT_TYPES") else []

DISPLAY_NAME = os.getenv("AGENT_DISPLAY_NAME", "")
FEW_SHOT_EXAMPLES_TABLE_FULL_ID = os.getenv("FEW_SHOT_EXAMPLES_TABLE_FULL_ID", "")
DATA_PROFILES_TABLE_FULL_ID = os.getenv("DATA_PROFILES_TABLE_FULL_ID", "")

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def fetch_few_shot_examples() -> list[str]:
    """
    Fetches few-shot examples from a BigQuery table for the current dataset.
    This function is schema-agnostic; it fetches all columns and formats them
    as key-value strings for the prompt.
    """
    examples_table_id = FEW_SHOT_EXAMPLES_TABLE_FULL_ID
    if not examples_table_id:
        logger.info(
            f"[{DISPLAY_NAME}] FEW_SHOT_EXAMPLES_TABLE_FULL_ID is not configured. Skipping few-shot example fetching."
        )
        return []

    start_time = time.time()
    logger.info(
        f"[{DISPLAY_NAME}] Starting to fetch few-shot examples for dataset '{DATASET_NAME}' from '{examples_table_id}'."
    )
    client = bigquery.Client(project=PROJECT_ID)
    # Use SELECT * to remain schema-agnostic. The filtering column 'dataset' is assumed to exist.
    query = """
        SELECT *
        FROM `{table_id}`
        WHERE dataset = @dataset_name
    """.format(table_id=examples_table_id)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("dataset_name", "STRING", DATASET_NAME)
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        formatted_examples = []
        for row in results:
            # For each row, create a formatted string of key-value pairs.
            example_parts = [
                f"{key}: {value}" for key, value in row.items() if key != "dataset"
            ]
            formatted_examples.append("\n".join(example_parts))

        duration = time.time() - start_time
        logger.info(
            f"[{DISPLAY_NAME}] --- Successfully fetched {len(formatted_examples)} few-shot examples (Duration: {duration:.2f} seconds) ---"
        )
        return formatted_examples
    except Exception as e:
        # Catch exceptions like the 'dataset' column not being found.
        duration = time.time() - start_time
        logger.error(
            f"[{DISPLAY_NAME}] --- Failed to fetch few-shot examples after {duration:.2f} seconds. Check if the table exists and contains a 'dataset' column. Error: {e} ---",
            exc_info=True,
        )
        return []


def fetch_dataset_description() -> str:
    """
    Fetches the description for a given BigQuery dataset.
    """
    if not PROJECT_ID or not DATASET_NAME:
        logger.warning(
            f"[{DISPLAY_NAME}] PROJECT_ID or DATASET_NAME not configured. Skipping dataset description fetch."
        )
        return ""
    try:
        start_time = time.time()
        client = bigquery.Client(project=PROJECT_ID)
        dataset_id = f"{PROJECT_ID}.{DATASET_NAME}"
        dataset = client.get_dataset(dataset_id)
        duration = time.time() - start_time
        logger.info(
            f"[{DISPLAY_NAME}] --- Successfully fetched dataset description (Duration: {duration:.2f} seconds) ---",
        )
        return dataset.description if dataset.description else ""
    except Exception as e:
        logger.error(
            f"[{DISPLAY_NAME}] Failed to fetch dataset description for {PROJECT_ID}.{DATASET_NAME}: {e}",
            exc_info=True,
        )
        return ""


def fetch_bigquery_data_profiles() -> list[dict]:
    """
    Fetches data profile information from a BigQuery table specified in .env file.
    """
    start_time = time.time()
    dataset_name_to_filter = DATASET_NAME
    target_table_names = TABLE_NAMES
    profiles_table_id = DATA_PROFILES_TABLE_FULL_ID

    if not profiles_table_id: # Check if the ID is None or an empty string
        logger.info(
            f"[{DISPLAY_NAME}] DATA_PROFILES_TABLE_FULL_ID is not configured. Skipping data profile fetching."
        )
        return []

    if target_table_names:
        logger.info(
            f"[{DISPLAY_NAME}] Starting to fetch data profiles for tables {target_table_names} in dataset '{dataset_name_to_filter}' from '{profiles_table_id}'."
        )
    else:
        logger.info(
            f"[{DISPLAY_NAME}] Starting to fetch data profiles for all tables in dataset '{dataset_name_to_filter}' from '{profiles_table_id}'."
        )

    client = bigquery.Client(project=PROJECT_ID)

    select_clause = """
        SELECT
            CONCAT(data_source.table_project_id, '.', data_source.dataset_id, '.', data_source.table_id) AS source_table_id,
            column_name,
            percent_null,
            percent_unique,
            #min_string_length,
            #max_string_length,
            min_value,
            max_value,
            array_to_string(
                array(
                select item.value
                from unnest(top_n) as item
                limit 5 # extracting only top 5 values 
                ),', '
            ) as top_n
    """
    from_clause = f"FROM `{profiles_table_id}`"
    where_conditions = ["data_source.dataset_id = @dataset_name_param"]
    query_params = [
        bigquery.ScalarQueryParameter(
            "dataset_name_param", "STRING", dataset_name_to_filter
        )
    ]

    if target_table_names:
        where_conditions.append("data_source.table_id IN UNNEST(@table_names_param)")
        query_params.append(
            bigquery.ArrayQueryParameter(
                "table_names_param", "STRING", target_table_names
            )
        )

    where_clause = "WHERE " + " AND ".join(where_conditions)
    order_by_clause = "ORDER BY source_table_id, column_name"
    final_query = f"{select_clause}\n{from_clause}\n{where_clause}\n{order_by_clause};"
    logger.debug(
        f"[{DISPLAY_NAME}] Executing BigQuery data profiles query:\n{final_query}"
    )
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    profiles_data = []

    try:
        query_job = client.query(final_query, job_config=job_config)
        results = query_job.result()
        raw_profiles_data = [dict(row.items()) for row in results]

        profiles_data = []  # Initialize the final list for filtered profiles
        for profile in raw_profiles_data:
            ''' #You can uncomment this part if you want to apply filtering on profiles to reduce noise in instruction.
           
            percent_null_value = profile.get('percent_null')
            description_value = profile.get('description')

            remove_profile = False
            reason = ""

            # Check condition 1: percent_null > 80
            if isinstance(percent_null_value, (float, int)) and percent_null_value > 90:
                remove_profile = True
                reason = f"percent_null > 80% (Value: {percent_null_value}%)"

            if remove_profile:
                continue  # Skip adding this profile to the final list'''

            # Add profile if it doesn't meet any removal condition
            profiles_data.append(profile)

        num_profiles_fetched = len(profiles_data)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(
            f"[{DISPLAY_NAME}] --- Successfully fetched {num_profiles_fetched} column profiles (Duration: {duration:.2f} seconds) ---"
        )
        return profiles_data

    except Exception:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(
            f"[{DISPLAY_NAME}] --- Failed to fetch data profiles after {duration:.2f} seconds ---",
            exc_info=True,
        )
        return []


def fetch_sample_data_for_tables(num_rows: int = 3) -> list[dict]:
    """
    Fetches a few sample rows from tables defined in .env file (PROJECT_ID, DATASET_NAME, TABLE_NAMES),
    Args:
        num_rows: The number of sample rows to fetch for each table.
    Returns:
        A list of dictionaries, where each dictionary contains 'table_name' (fully qualified)
        and 'sample_rows'. Returns an empty list if no data can be fetched or an error occurs.
    """
    start_time = time.time()
    sample_data_results: list[dict] = []
    project_id = PROJECT_ID
    dataset_id = DATASET_NAME
    table_names_list = TABLE_NAMES

    if not project_id or not dataset_id:
        logger.error(
            f"[{DISPLAY_NAME}] PROJECT_ID and DATASET_NAME must be configured."
        )
        return sample_data_results
    try:
        client = bigquery.Client(project=project_id)
    except Exception as e:
        logger.error(
            f"[{DISPLAY_NAME}] Failed to create BigQuery client for project {project_id}: {e}",
            exc_info=True,
        )
        return sample_data_results

    tables_to_fetch_samples_from_ids: list[str] = []
    if table_names_list:
        tables_to_fetch_samples_from_ids = table_names_list
        logger.info(
            f"[{DISPLAY_NAME}] Fetching sample data for specified tables in {project_id}.{dataset_id}: {table_names_list}"
        )
    else:
        logger.info(
            f"[{DISPLAY_NAME}] Fetching sample data for all tables in dataset: {project_id}.{dataset_id}"
        )
        try:
            dataset_ref = client.dataset(dataset_id, project=project_id)
            for bq_table in client.list_tables(dataset_ref):
                if bq_table.table_type == "TABLE":
                    tables_to_fetch_samples_from_ids.append(bq_table.table_id)
                else:
                    logger.info(
                        f"[{DISPLAY_NAME}] Skipping non-base table: {bq_table.project}.{bq_table.dataset_id}.{bq_table.table_id} (Type: {bq_table.table_type})"
                    )
        except Exception as e:
            logger.error(
                f"[{DISPLAY_NAME}] Error listing tables for {project_id}.{dataset_id}: {e}",
                exc_info=True,
            )
            return sample_data_results

    if not tables_to_fetch_samples_from_ids:
        logger.info(
            f"[{DISPLAY_NAME}] No tables identified to fetch samples from in {project_id}.{dataset_id}."
        )
        return sample_data_results

    for table_id_str in tables_to_fetch_samples_from_ids:
        full_table_name = f"{project_id}.{dataset_id}.{table_id_str}"
        try:
            logger.info(
                f"[{DISPLAY_NAME}] Fetching sample data for table: {full_table_name}"
            )
            table_reference = TableReference.from_string(
                full_table_name, default_project=project_id
            )
            rows_iterator = client.list_rows(table_reference, max_results=num_rows)
            table_sample_rows = [dict(row.items()) for row in rows_iterator]
            if table_sample_rows:
                sample_data_results.append(
                    {"table_name": full_table_name, "sample_rows": table_sample_rows}
                )
            else:
                logger.info(
                    f"[{DISPLAY_NAME}] No sample data found for table '{full_table_name}'."
                )
        except Exception as e:
            logger.error(
                f"[{DISPLAY_NAME}] Error fetching sample data for table {full_table_name}: {e}",
                exc_info=True,
            )
            continue

    end_time = time.time()
    duration = end_time - start_time
    logger.info(
        f"[{DISPLAY_NAME}] --- Successfully fetched {len(sample_data_results)} sample data sets (Duration: {duration:.2f} seconds) ---"
    )
    return sample_data_results


def convert_proto_to_dict(obj):
    if isinstance(obj, maps.MapComposite):
        return {k: convert_proto_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, repeated.RepeatedComposite):
        return [convert_proto_to_dict(elem) for elem in obj]
    else:
        return obj


def fetch_table_entry_metadata() -> list[dict]:
    """
    Fetches metadata for table entries from Dataplex, focusing on custom aspects.
    The aspects to be fetched are controlled by the ASPECT_TYPES environment variable.
    If ASPECT_TYPES is set (as a comma-separated list of aspect type IDs), only those aspects are fetched.
    If ASPECT_TYPES is empty, no aspects are fetched.
    This function is designed to fail gracefully, returning an empty list if it
    encounters any issues (e.g., permissions errors during a CI/CD build).
    """
    try:
        start_time = time.time()
        project_id_val = PROJECT_ID
        location_val = LOCATION
        dataset_id_val = DATASET_NAME
        table_names_val = TABLE_NAMES

        logger.info(
            f"[{DISPLAY_NAME}] Fetching Dataplex metadata for "
            f"project='{project_id_val}', location='{location_val}', dataset='{dataset_id_val}', "
            f"tables='{table_names_val if table_names_val else 'All'}'"
        )
        all_entry_metadata: list[dict] = []
        client = dataplex_v1.CatalogServiceClient()
        target_entry_names: list[str] = []

        if table_names_val:
            entry_group_name = f"projects/{project_id_val}/locations/{location_val}/entryGroups/@bigquery"
            for table_name in table_names_val:
                entry_id_for_bq = f"bigquery.googleapis.com/projects/{project_id_val}/datasets/{dataset_id_val}/tables/{table_name}"
                target_entry_names.append(
                    f"{entry_group_name}/entries/{entry_id_for_bq}"
                )
        else:
            search_request = dataplex_v1.SearchEntriesRequest(
                name=f"projects/{project_id_val}/locations/global",
                scope=f"projects/{project_id_val}",
                query=f"name:projects/{project_id_val}/datasets/{dataset_id_val}/tables/",
                page_size=100,
            )
            for entry in client.search_entries(request=search_request):
                target_entry_names.append(entry.dataplex_entry.name)

        if not target_entry_names:
            logger.info(
                f"[{DISPLAY_NAME}] No target tables found in Dataplex for the specified scope."
            )
            return []

        for entry_name in target_entry_names:
            try:
                get_entry_request = dataplex_v1.GetEntryRequest(
                    name=entry_name, view=dataplex_v1.EntryView.CUSTOM
                )
                if ASPECT_TYPES:
                    get_entry_request.aspect_types = [
                        f"projects/{project_id_val}/locations/{location_val}/aspectTypes/{aspect}"
                        for aspect in ASPECT_TYPES
                    ]
                    logger.debug(f"get_entry_request.aspect_types : {get_entry_request.aspect_types}")
                else:
                    continue

                entry = client.get_entry(request=get_entry_request)
                aspects_data = {
                    aspect_key: convert_proto_to_dict(aspect.data)
                    for aspect_key, aspect in entry.aspects.items()
                    if hasattr(aspect, "data") and aspect.data
                }
                if aspects_data:
                    metadata = {
                        "table_name": entry_name.split("/")[-1],
                        "aspects": aspects_data,
                    }
                    all_entry_metadata.append(metadata)
            except Exception as e:
                logger.warning(
                    f"[{DISPLAY_NAME}] Could not fetch metadata for single entry {entry_name}. Skipping. Error: {e}"
                )
                continue

        duration = time.time() - start_time
        logger.info(
            f"[{DISPLAY_NAME}] --- Successfully fetched {len(all_entry_metadata)} entry metadata sets (Duration: {duration:.2f} seconds) ---"
        )
        return all_entry_metadata

    except Exception as e:
        logger.warning(
            f"[{DISPLAY_NAME}] Could not fetch Dataplex metadata. This can be expected during a build process "
            f"if the service account lacks Dataplex permissions. The agent will proceed without this metadata. Error: {e}"
        )
        return []

def get_table_info():
    """Retrieves schema and generates DDL with example values for a BigQuery dataset.


    Returns:
        str: A string containing the generated DDL statements.
    """

    start_time = time.time()
    project_id_val = PROJECT_ID
    dataset_id_val = DATASET_NAME
    table_names_val = TABLE_NAMES

    client = bigquery.Client(project=project_id_val)

    dataset_ref = bigquery.DatasetReference(project_id_val, dataset_id_val)

    if not table_names_val:
        table_names_val = [table.table_id for table in client.list_tables(dataset_ref)]

    ddl_statements = ""

    for table_name in table_names_val:
        table_ref = dataset_ref.table(table_name)
        table_obj = client.get_table(table_ref)

        ddl_statement = f"CREATE TABLE `{table_ref}`\n(\n"
        
        fields_ddl = []
        for field in table_obj.schema:
            field_type_mapping = {
                'INTEGER': 'INT64',
                'FLOAT': 'FLOAT64',
                'BOOLEAN': 'BOOL'
            }
            field_type = field_type_mapping.get(field.field_type, field.field_type)

            field_ddl = f"  {field.name} {field_type}"
            
            description = field.description or ""

            if description:
                escaped_description = description.replace('"', '\"')
                field_ddl += f' OPTIONS(description="{escaped_description}")'
            
            fields_ddl.append(field_ddl)

        ddl_statement += ",\n".join(fields_ddl)
        ddl_statement += "\n)"

        if table_obj.description:
            escaped_table_description = table_obj.description.replace('"', '\"')
            ddl_statement += f"\nOPTIONS(\n  description=\"{escaped_table_description}\"\n)"

        ddl_statement += ";\n\n"

        ddl_statements += ddl_statement
    
    end_time = time.time()
    duration = end_time - start_time
    logger.info(
        f"--- Successfully fetched schema of {len(table_names_val)} tables "
        f"(Duration: {duration:.2f} seconds) ---"
    )

    return ddl_statements