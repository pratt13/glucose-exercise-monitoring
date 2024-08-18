#!/usr/bin/env bash
set -eou pipefail

: "${DB_IMAGE_NAME:="diabetes-db"}"
: "${DB_IMAGE_VERSION:="latest"}"
: "${BACKEND_IMAGE_NAME:="diabetes-backend"}"
: "${BACKEND_IMAGE_VERSION:="latest"}"
: "${BACKEND_ENV_FILE:=".backend.env"}"

DB_IMAGE_NAME="${DB_IMAGE_NAME}" \
    DB_IMAGE_VERSION="${DB_IMAGE_VERSION}" \
    BACKEND_IMAGE_NAME="${BACKEND_IMAGE_NAME}" \
    BACKEND_IMAGE_VERSION="${BACKEND_IMAGE_VERSION}" \
    BACKEND_ENV_FILE="${BACKEND_ENV_FILE}" \
    docker compose up -d
