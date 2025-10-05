#!/bin/bash

# This script is used to copy files from contracts/protobuf to service dirs.

set -eu

readonly SRC_DIR="contracts/protobuf"

refresh_local_proto() {
    local service_dir=$1
    local service_lang=""
    local dest_dir=""

    echo "====== Refresh $service_dir protos ======"

    if [[ -f "$service_dir/pom.xml" ]]; then
        service_lang="Java"
        dest_dir="$service_dir/src/main/proto"

    elif [[ -f "$service_dir/pyproject.toml" ]]; then
        service_lang="Python"
        dest_dir="$service_dir/libs/proto"

    elif [[ -f "$service_dir/go.mod" ]]; then
        service_lang="Go"
        dest_dir="$service_dir/proto"

    else
        echo "[WARN] Skip $service_dir (language not recognized)"
        return
    fi

    echo "Detected $service_lang service, refreshing protos in $dest_dir"

    rm -rf "$dest_dir"
    mkdir -p "$dest_dir"
    cp -r "$SRC_DIR/"* "$dest_dir/"

    echo "[OK] Protos refreshed for $service_dir"
}

if [[ $# -eq 0 ]]; then
    SERVICE_DIRS=(trip-*-service)
else
    SERVICE_DIRS=("$@")
fi

for dir in "${SERVICE_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        refresh_local_proto "$dir"
    else
        echo "[WARN] Directory $dir not found"
    fi
done
