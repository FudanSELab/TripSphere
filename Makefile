SERVICE ?=

.PHONY: refresh-protos
refresh-protos:
	@bash scripts/refresh-protos.sh $(SERVICE)

.PHONY: compile-protos
compile-protos:
	@bash scripts/compile-protos.sh $(SERVICE)
