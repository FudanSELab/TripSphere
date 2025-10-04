#!/bin/bash
set -eu

SRC_DIR="contracts/protobuf"

refresh_service() {
  SERVICE_DIR=$1
  echo "====== Processing $SERVICE_DIR ======"

  if [[ -f "$SERVICE_DIR/pom.xml" ]]; then
    DEST_DIR="$SERVICE_DIR/src/main/proto"
    echo "Detected Java service, copying protos to $DEST_DIR"

  elif [[ -f "$SERVICE_DIR/pyproject.toml" ]]; then
    DEST_DIR="$SERVICE_DIR/libs/proto"
    echo "Detected Python service, copying protos to $DEST_DIR"

  elif [[ -f "$SERVICE_DIR/go.mod" ]]; then
    DEST_DIR="$SERVICE_DIR/proto"
    echo "Detected Go service, copying protos to $DEST_DIR"

  else
    echo "[WARN] Skipping $SERVICE_DIR (language not recognized)"
    return
  fi

  rm -rf "$DEST_DIR"
  mkdir -p "$DEST_DIR"
  cp -r "$SRC_DIR/"* "$DEST_DIR/"

  echo "[OK] Protos refreshed for $SERVICE_DIR"
}

if [[ $# -eq 0 ]]; then
  SERVICE_DIRS=(trip-*-service)
else
  SERVICE_DIRS=("$@")
fi

for dir in "${SERVICE_DIRS[@]}"; do
  if [[ -d "$dir" ]]; then
    refresh_service "$dir"
  else
    echo "[WARN] Directory $dir not found"
  fi
done

echo "[DONE] All protos refreshed!"
