PREFIX = tripsphere
TAG = latest
SERVICE ?=

.PHONY: refresh-protos
refresh-protos:
	@bash scripts/refresh-protos.sh $(SERVICE)

.PHONY: compile-protos
compile-protos:
	@bash scripts/compile-protos.sh $(SERVICE)

.PHONY: build-image
build-image:
	@bash hack/build-image.sh $(PREFIX) $(TAG)
