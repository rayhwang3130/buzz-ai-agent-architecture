#!/bin/bash

# This file contains configuration variables for the DEPLOYMENT INFRASTRUCTURE.
# Variables related to the APPLICATION/AGENT RUNTIME (e.g., BigQuery details,
# agent behavior) should be set in the .env file.

# Edit these values to match your GCP environment and application needs.

# --- Project Configuration ---
# Your GCP Project ID. This is the most critical setting to deploy this application to Cloud Run
export PROJECT_ID="<gcp-project-id>"
# The region where resources will be deployed.
#export GCP_REGION="asia-northeast3"
export GCP_REGION="<gcp-region>"
# The name of the Artifact Registry repository to store Docker images.
export ARTIFACT_REGISTRY_REPO="<artifact-registry-repo-name>"


# --- Application Configuration ---
# A short identifier for the main application, used as a command-line argument.
export APP_IDENTIFIER="app"
# The name for the main application's Cloud Run service.
export APP_SERVICE_NAME="<application-name>"


# --- Image Configuration ---
# The base name for the Docker image that will be built.
export IMAGE_NAME="main-app"
# The tag for the Docker image (e.g., "latest", "v1.0").
export TAG="latest"