#!/bin/bash

# Script to generate gRPC code
# Requires protoc and related Go plugins to be installed first

set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting to generate gRPC code...${NC}"

# Check if protoc is installed
if ! command -v protoc &> /dev/null; then
    echo -e "${YELLOW}Error: protoc is not installed${NC}"
    echo "Please install protoc first:"
    echo "  Ubuntu/Debian: sudo apt-get install protobuf-compiler"
    echo "  macOS: brew install protobuf"
    echo "  Or visit: https://grpc.io/docs/protoc-installation/"
    exit 1
fi

# Check if Go plugins are installed
if ! go list -m google.golang.org/protobuf/cmd/protoc-gen-go &> /dev/null; then
    echo -e "${YELLOW}Installing protoc-gen-go...${NC}"
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
fi

if ! go list -m google.golang.org/grpc/cmd/protoc-gen-go-grpc &> /dev/null; then
    echo -e "${YELLOW}Installing protoc-gen-go-grpc...${NC}"
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
fi

# Proto file paths
PROTO_DIR="../contracts/protobuf/tripsphere"
OUTPUT_DIR="./clients/grpc/gen"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo -e "${GREEN}Generating client code for other services...${NC}"
for proto_file in $(find "$PROTO_DIR" -name "*.proto"); do
    service_dir=$(dirname "$proto_file" | sed "s|$PROTO_DIR/||")
    service_name=$(basename "$service_dir")
    proto_rel_path=$(echo "$proto_file" | sed "s|$PROTO_DIR/||")
    mkdir -p "$OUTPUT_DIR/$service_dir"
    echo "  Generating client code for $service_name service..."
    protoc --go_out="$OUTPUT_DIR" \
        --go_opt=paths=source_relative \
        --go-grpc_out="$OUTPUT_DIR" \
        --go-grpc_opt=paths=source_relative \
        --proto_path="$PROTO_DIR" \
        "$proto_file"
done

echo -e "${GREEN}All proto code generation completed!${NC}"

