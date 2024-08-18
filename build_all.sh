#!/usr/bin/env bash
set -eou pipefail

echo "Building diabetes database"
pushd "diabetes-db"
./build.sh
popd

echo "Building diabetes backend"
pushd "diabetes_backend"
./build.sh
popd

echo "Finished building docker images"
