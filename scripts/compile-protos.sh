#!/bin/bash

# This script is used to generate protobuf files for all services.
# Useful to ensure code can compile, and provide hints for IDEs in development.
# Several dev tools like protoc, uv, mvnw may be required to run this script.

set -eu

compile_service_proto() {
    local service_dir=$1
    local src_dir=""

    echo "====== Compile $service_dir protos ======"

    if [[ -f "$service_dir/pom.xml" ]]; then
        src_dir="$service_dir/src/main/proto"
        echo "Detected Java service, compiling protos in $src_dir"
        compile_proto_java "$service_dir"

    elif [[ -f "$service_dir/pyproject.toml" ]]; then
        src_dir="$service_dir/libs/proto"
        echo "Detected Python service, compiling protos in $src_dir"
        compile_proto_python "$service_dir"

    elif [[ -f "$service_dir/go.mod" ]]; then
        src_dir="$service_dir/proto"
        echo "Detected Go service, compiling protos in $src_dir"
        compile_proto_go "$service_dir"

    else
        echo "[WARN] Skip $service_dir (language not recognized)"
        return
    fi

    echo "[OK] Protos compiled for $service_dir"
}

compile_proto_java() {
    local service_dir=$1

    "$service_dir/mvnw" -f "$service_dir/pom.xml" \
        clean \
        protobuf:compile \
        protobuf:compile-custom
}

compile_proto_python() {
    local service_dir=$1
    local src_dir="$service_dir/libs/proto"
    local dest_dir="$service_dir/libs/tripsphere/src"

    # Clean up old generated gRPC files
    find "$dest_dir" -type f ! -name "py.typed" ! -name "__init__.py" -delete

    local protos
    protos=$(find "$src_dir" -name "*.proto")

    uv run --project "$service_dir" -m grpc_tools.protoc \
        -I"$src_dir" \
        --python_out="$dest_dir" \
        --grpc_python_out="$dest_dir" \
        --mypy_out="$dest_dir" \
        --mypy_grpc_out="$dest_dir" \
        $protos
}

compile_proto_go() {
    local service_dir=$1

    echo "TODO: Not Implemented Yet"
}

if [[ $# -eq 0 ]]; then
    SERVICE_DIRS=(trip-*-service)
else
    SERVICE_DIRS=("$@")
fi

for dir in "${SERVICE_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        compile_service_proto "$dir"
    else
        echo "[WARN] Directory $dir not found"
    fi
done