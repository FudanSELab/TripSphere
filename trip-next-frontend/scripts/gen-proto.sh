#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROTO_DIR="$SCRIPT_DIR/../../contracts/protobuf/tripsphere"
OUT_DIR="$SCRIPT_DIR/../lib/grpc/gen"

mkdir -p "$OUT_DIR"

# get ts-protoc-gen plugin path
TS_PLUGIN="$SCRIPT_DIR/../node_modules/.bin/protoc-gen-ts"

npx grpc_tools_node_protoc \
  --plugin=protoc-gen-ts="$TS_PLUGIN" \
  --js_out=import_style=commonjs,binary:"$OUT_DIR" \
  --ts_out=service=grpc-node,mode=grpc-js:"$OUT_DIR" \
  --grpc_out=grpc_js:"$OUT_DIR" \
  -I "$PROTO_DIR" \
  "$PROTO_DIR"/**/*.proto

echo "Proto files generated: $OUT_DIR"
