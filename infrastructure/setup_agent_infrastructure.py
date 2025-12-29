
import os
import sys
import logging
import pandas as pd
import time
from typing import List, Optional

from google.cloud import bigquery
from google.cloud import dataplex_v1
from google.api_core.exceptions import AlreadyExists, NotFound, GoogleAPICallError
from dotenv import load_dotenv

import vertexai
from vertexai.language_models import TextEmbeddingModel

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load Environment ---
# Assuming script is run from project root, or we find .env relative to script
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
env_path = os.path.join(project_root, '.env')

if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment from {env_path}")
else:
    logger.warning("No .env file found. Relying on system environment variables.")

# --- Configuration ---
PROJECT_ID = os.getenv("BQ_DATA_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("BQ_LOCATION", "us-central1")
DATASET_NAME = os.getenv("BQ_DATASET_NAME", "labeling_pipeline_dataset")
TABLE_NAME = os.getenv("BQ_TABLE_NAMES", "agent-test").split(',')[0]
CSV_FILE_PATH = os.path.join(project_root, "251229_final_UNPK_Test.csv")

DATAPLEX_LAKE_ID = "test-buzz-ai-lake"
DATAPLEX_ZONE_ID = "test-primary-zone"
DATAPLEX_ASSET_ID = "test-agent-asset"

# --- Globals ---
bq_client = None
dataplex_client = None

def init_clients():
    global bq_client, dataplex_client
    bq_client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    dataplex_client = dataplex_v1.DataplexServiceClient()
    vertexai.init(project=PROJECT_ID, location=LOCATION)

def infer_bq_schema_from_csv(csv_path: str) -> List[bigquery.SchemaField]:
    """Reads CSV header/types and returns BigQuery Schema."""
    logger.info(f"Inferring schema from {csv_path}...")
    df = pd.read_csv(csv_path, nrows=100) # Read sample
    schema = []
    
    for col, dtype in df.dtypes.items():
        bq_type = "STRING"
        if pd.api.types.is_integer_dtype(dtype):
            bq_type = "INTEGER"
        elif pd.api.types.is_float_dtype(dtype):
            bq_type = "FLOAT"
        elif pd.api.types.is_bool_dtype(dtype):
            bq_type = "BOOLEAN"
        elif "time" in col.lower() or "date" in col.lower():
             # Basic heuristic for timestamp columns
             bq_type = "TIMESTAMP" 
        
        # Sanitize column name (replace non-alphanumeric with _)
        sanitized_name = "".join([c if c.isalnum() else "_" for c in col])
        schema.append(bigquery.SchemaField(sanitized_name, bq_type))
    
    # Add embedding column definition
    schema.append(bigquery.SchemaField("text_embedding", "FLOAT", mode="REPEATED"))
    return schema

def create_bq_table_if_needed(schema: List[bigquery.SchemaField]):
    dataset_ref = bq_client.dataset(DATASET_NAME)
    
    # 1. Check/Create Dataset
    try:
        bq_client.get_dataset(dataset_ref)
        logger.info(f"Dataset {DATASET_NAME} exists.")
    except NotFound:
        logger.info(f"Dataset {DATASET_NAME} not found. Creating...")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = LOCATION
        bq_client.create_dataset(dataset)
        logger.info(f"Dataset {DATASET_NAME} created.")

    # 2. Check/Create Table
    table_ref = dataset_ref.table(TABLE_NAME)
    try:
        table = bq_client.get_table(table_ref)
        logger.info(f"Table {TABLE_NAME} exists.")
        
        # Check if embedding column exists
        has_embedding = any(field.name == 'text_embedding' for field in table.schema)
        if not has_embedding:
            logger.info("Adding 'text_embedding' column to existing table...")
            new_schema = table.schema[:]
            new_schema.append(bigquery.SchemaField("text_embedding", "FLOAT", mode="REPEATED"))
            table.schema = new_schema
            bq_client.update_table(table, ["schema"])
            logger.info("Table schema updated with 'text_embedding'.")
            
    except NotFound:
        logger.info(f"Table {TABLE_NAME} not found. Creating with inferred schema...")
        table = bigquery.Table(table_ref, schema=schema)
        bq_client.create_table(table)
        logger.info(f"Table {TABLE_NAME} created.")

def create_dataplex_resources():
    """Creates Lake, Zone, and Asset."""
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
    
    # 1. Create Lake
    lake_id = DATAPLEX_LAKE_ID
    lake_name = f"{parent}/lakes/{lake_id}"
    
    try:
        dataplex_client.get_lake(name=lake_name)
        logger.info(f"Lake {lake_id} already exists.")
    except NotFound:
        logger.info(f"Creating Lake {lake_id}...")
        lake = dataplex_v1.Lake(
            display_name="Buzz AI Lake",
            description="Lake for Social Buzz Data",
            labels={"env": "dev"}
        )
        operation = dataplex_client.create_lake(parent=parent, lake_id=lake_id, lake=lake)
        operation.result(timeout=600)
        logger.info(f"Lake {lake_id} created.")

    # 2. Create Zone
    zone_id = DATAPLEX_ZONE_ID
    zone_name = f"{lake_name}/zones/{zone_id}"
    
    try:
        dataplex_client.get_zone(name=zone_name)
        logger.info(f"Zone {zone_id} already exists.")
    except NotFound:
        logger.info(f"Creating Zone {zone_id}...")
        zone = dataplex_v1.Zone(
            display_name="Primary Zone",
            type_=dataplex_v1.Zone.Type.RAW, # or CURATED
            resource_spec=dataplex_v1.Zone.ResourceSpec(location_type=dataplex_v1.Zone.ResourceSpec.LocationType.SINGLE_REGION),
            discovery_spec=dataplex_v1.Zone.DiscoverySpec(enabled=True)
        )
        operation = dataplex_client.create_zone(parent=lake_name, zone_id=zone_id, zone=zone)
        operation.result(timeout=600)
        logger.info(f"Zone {zone_id} created.")

    # 3. Create Asset (Link to BigQuery Dataset)
    asset_id = DATAPLEX_ASSET_ID
    asset_name = f"{zone_name}/assets/{asset_id}"
    
    try:
        dataplex_client.get_asset(name=asset_name)
        logger.info(f"Asset {asset_id} already exists.")
    except NotFound:
        logger.info(f"Creating Asset {asset_id} linked to {DATASET_NAME}...")
        asset = dataplex_v1.Asset(
            display_name="Agent Test Dataset",
            resource_spec=dataplex_v1.Asset.ResourceSpec(
                type_=dataplex_v1.Asset.ResourceSpec.Type.BIGQUERY_DATASET,
                name=f"projects/{PROJECT_ID}/datasets/{DATASET_NAME}"
            ),
            discovery_spec=dataplex_v1.Asset.DiscoverySpec(enabled=True)
        )
        operation = dataplex_client.create_asset(parent=zone_name, asset_id=asset_id, asset=asset)
        operation.result(timeout=600)
        logger.info(f"Asset {asset_id} created.")

def generate_embeddings_for_missing_rows():
    """Backfills embeddings for rows where text_embedding is NULL."""
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    # Fetch rows pending embedding
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_NAME}.{TABLE_NAME}`
        WHERE text_embedding IS NULL
        AND text IS NOT NULL
        LIMIT 1000
    """
    logger.info("Fetching rows with missing embeddings...")
    query_job = bq_client.query(query)
    rows = list(query_job.result())
    
    if not rows:
        logger.info("No rows found needing embeddings.")
        return

    logger.info(f"Found {len(rows)} rows to embed. Processing...")
    
    BATCH_SIZE = 5
    updates = []
    
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i+BATCH_SIZE]
        texts = [row.text for row in batch]
        
        try:
            embeddings = model.get_embeddings(texts)
            for j, embedding in enumerate(embeddings):
                # We need a unique identifier. Assuming 'id' column exists based on CSV.
                # If no ID, we might need to rely on row uniqueness or add a temporary ID.
                row_id = batch[j].id 
                updates.append({"id": row_id, "text_embedding": embedding.values})
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            continue
            
    # Update back to BigQuery
    # Efficient update via temporary table + MERGE
    if updates:
        _update_bq_with_embeddings(updates)

def _update_bq_with_embeddings(updates):
    """Updates BQ table using a temporary staging table and MERGE statement."""
    logger.info(f"Updating {len(updates)} rows in BigQuery...")
    
    temp_table_id = f"{DATASET_NAME}.temp_embedding_updates"
    
    # Create DF
    df = pd.DataFrame(updates)
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
    )
    
    # Load to temp table
    load_job = bq_client.load_table_from_dataframe(df, temp_table_id, job_config=job_config)
    load_job.result()
    
    # MERGE
    merge_query = f"""
        MERGE `{PROJECT_ID}.{DATASET_NAME}.{TABLE_NAME}` T
        USING `{PROJECT_ID}.{temp_table_id}` S
        ON T.id = S.id
        WHEN MATCHED THEN
          UPDATE SET text_embedding = S.text_embedding
    """
    bq_client.query(merge_query).result()
    logger.info("Update complete.")
    
    # Cleanup
    bq_client.delete_table(temp_table_id, not_found_ok=True)

def main():
    if not PROJECT_ID:
        logger.error("PROJECT_ID not set. Please check your .env file.")
        return

    init_clients()
    
    print("--- 1. Inferring Schema & Setting up BigQuery ---")
    if os.path.exists(CSV_FILE_PATH):
        schema = infer_bq_schema_from_csv(CSV_FILE_PATH)
        create_bq_table_if_needed(schema)
    else:
        logger.error(f"CSV file not found at {CSV_FILE_PATH}. Cannot infer schema.")
        return

    print("--- 2. Setting up Dataplex (Lake -> Zone -> Asset) ---")
    try:
        create_dataplex_resources()
    except Exception as e:
        logger.error(f"Dataplex setup failed: {e}")

    print("--- 3. Generating Embeddings (Vertex AI) ---")
    try:
        generate_embeddings_for_missing_rows()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        
    print("\n\nDone! Infrastructure setup complete.")
    print("To verify, check your BigQuery table schema for 'text_embedding' and visit the Dataplex console.")

if __name__ == "__main__":
    main()
