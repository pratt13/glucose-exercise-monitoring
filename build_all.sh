#!/usr/bin/env bash
set -eou pipefail

echo "Building diabetes database"
pushd "diabetes-db"
./build.sh
popd

echo "Finished building docker images"