SERVICE ?=

.PHONY: refresh-protos
refresh-protos:
	@bash scripts/refresh-protos.sh $(SERVICE)

.PHONY: compile-protos
compile-protos:
	@bash hack/compile-protos.sh $(SERVICE)
