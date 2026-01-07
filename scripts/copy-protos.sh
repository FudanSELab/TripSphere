#!/bin/bash

# This script is used to copy files from contracts/protobuf to service dirs.

set -eu

readonly PROTO_SRC_DIR="contracts/protobuf"

copy_protos() {
    local service_dir=$1
    local service_lang=""
    local dest_dir=""

    if [[ -f "$service_dir/pom.xml" ]]; then
        service_lang="Java"
        dest_dir="$service_dir/src/main/proto"

    elif [[ -f "$service_dir/pyproject.toml" ]]; then
        service_lang="Python"
        dest_dir="$service_dir/libs/proto"

    elif [[ -f "$service_dir/go.mod" ]]; then
        service_lang="Go"
        dest_dir="$service_dir/proto"

    elif [[ -f "$service_dir/package.json" ]]; then
        service_lang="JavaScript"
        dest_dir="$service_dir/lib/proto"

    else
        echo "[WARN] Skip $service_dir (language not recognized)"
        return
    fi

    echo "Detected $service_lang service, copying protos to $dest_dir"

    rm -rf "$dest_dir"
    mkdir -p "$dest_dir"
    cp -r "$PROTO_SRC_DIR/"* "$dest_dir/"

    echo "Protos are copied to $service_dir"
}

if [[ $# -eq 0 ]]; then
    echo "Usage: copy-protos.sh <service-dir> [service-dir...]"
    exit 1
else
    SERVICE_DIRS=("$@")
fi

for dir in "${SERVICE_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        copy_protos "$dir"
    else
        echo "[WARN] Directory not found: $dir"
    fi
done