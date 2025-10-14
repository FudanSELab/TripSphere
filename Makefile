PREFIX = tripsphere
TAG = latest
SERVICE ?=

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  help              - Show this help message"
	@echo "  refresh-protos    - Refresh protobuf files"
	@echo "  compile-protos    - Compile protobuf files"
	@echo "  build-image       - Build Docker image"

.PHONY: refresh-protos
refresh-protos:
	@bash scripts/refresh-protos.sh $(SERVICE)

.PHONY: compile-protos
compile-protos:
	@bash scripts/compile-protos.sh $(SERVICE)

.PHONY: build-image
build-image:
	@bash scripts/build-image.sh $(PREFIX) $(TAG) $(SERVICE)
