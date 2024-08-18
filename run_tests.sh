#!/usr/bin/env bash
set -eou pipefail

: "${BACKEND_IMAGE_NAME:="diabetes-backend-unit-test"}"
: "${BACKEND_IMAGE_VERSION:="latest"}"

docker run --rm \
    --name diabetes-backend-tests \
    "${BACKEND_IMAGE_NAME}:${BACKEND_IMAGE_VERSION}"
