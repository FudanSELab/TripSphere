# PowerShell script to generate gRPC proto files

$SCRIPT_DIR = $PSScriptRoot
$PROTO_DIR = Join-Path $SCRIPT_DIR "..\..\contracts\protobuf\tripsphere"
$OUT_DIR = Join-Path $SCRIPT_DIR "..\lib\grpc\gen"

# Create output directory if it doesn't exist
New-Item -ItemType Directory -Force -Path $OUT_DIR | Out-Null

# Get ts-protoc-gen plugin path (use .cmd on Windows)
$TS_PLUGIN = Join-Path $SCRIPT_DIR "..\node_modules\.bin\protoc-gen-ts.cmd"

# Resolve paths to absolute paths
$PROTO_DIR = Resolve-Path $PROTO_DIR -ErrorAction SilentlyContinue
if (-not $PROTO_DIR) {
    Write-Error "Proto directory not found: $PROTO_DIR"
    exit 1
}
$PROTO_DIR = $PROTO_DIR.Path

$OUT_DIR = (Resolve-Path $OUT_DIR -ErrorAction SilentlyContinue).Path
if (-not $OUT_DIR) {
    $OUT_DIR = (New-Item -ItemType Directory -Force -Path $OUT_DIR).FullName
}

$TS_PLUGIN = Resolve-Path $TS_PLUGIN -ErrorAction SilentlyContinue
if (-not $TS_PLUGIN) {
    Write-Error "TS plugin not found: $TS_PLUGIN"
    exit 1
}
$TS_PLUGIN = $TS_PLUGIN.Path

# Find all proto files
$PROTO_FILES = Get-ChildItem -Path $PROTO_DIR -Filter "*.proto" -Recurse

if ($PROTO_FILES.Count -eq 0) {
    Write-Error "No proto files found in: $PROTO_DIR"
    exit 1
}

# Run protoc command
npx grpc_tools_node_protoc `
  --plugin="protoc-gen-ts=$TS_PLUGIN" `
  --js_out="import_style=commonjs,binary:$OUT_DIR" `
  --ts_out="service=grpc-node,mode=grpc-js:$OUT_DIR" `
  --grpc_out="grpc_js:$OUT_DIR" `
  -I "$PROTO_DIR" `
  $PROTO_FILES.FullName

Write-Host "Proto files generated: $OUT_DIR"


