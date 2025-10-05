#!/bin/bash
set -eu

PREFIX="$1"
TAG="$2"
shift 2  # Optional service names

# If no services are specified, build all trip-*-service by default
if [[ $# -eq 0 ]]; then
    SERVICES=()
    for d in trip-*-service; do
        [[ -d "$d" ]] || continue
        SERVICES+=("$d")
    done
else
    SERVICES=("$@")
fi

echo "====== Start building images ======"

for dir in "${SERVICES[@]}"; do
    [[ -d "$dir" ]] || { echo "[WARN] Skip $dir (dir does not exist)"; continue; }

    dockerfile_found=false
    for df in "$dir"/Dockerfile*; do
        [[ -f "$df" ]] && dockerfile_found=true && break
    done

    if $dockerfile_found; then
        echo "Building ${dir} docker image"
        docker build -t "$PREFIX/$dir:$TAG" "$dir"
    else
        echo "[WARN] Skip $dir (Dockerfile not found)"
    fi
done
