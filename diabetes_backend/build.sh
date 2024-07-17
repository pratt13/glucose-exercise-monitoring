#!/usr/bin/env bash
set -eou pipefail

: "${IMAGE_NAME:="diabetes-backend"}"
: "${IMAGE_VERSION:="latest"}"
: "${UNIT_TEST_IMAGE_NAME:="diabetes-backend-unit-test"}"

echo -n "Building ${IMAGE_NAME}:${IMAGE_VERSION}..."
docker build \
    -t "${IMAGE_NAME}:${IMAGE_VERSION}" \
    -f docker/Dockerfile \
    --target backend \
    ./src
echo "Built ${IMAGE_NAME}:${IMAGE_VERSION}"

echo -n "Building ${UNIT_TEST_IMAGE_NAME}:${IMAGE_VERSION}..."
docker build \
    -t "${UNIT_TEST_IMAGE_NAME}:${IMAGE_VERSION}" \
    -f docker/Dockerfile \
    --target backend_unit \
    ./src

echo "Built ${UNIT_TEST_IMAGE_NAME}:${IMAGE_VERSION}"
