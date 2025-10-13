# Trip Note Service Makefile

# Variables
PROTO_DIR = contracts/protobuf/trip-note-service
PROTO_OUT_DIR = src/main/java
LIBS_DIR = libs/tripsphere

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  refresh-protos    - Refresh protobuf files from contracts"
	@echo "  compile-protos    - Compile protobuf files to Java"
	@echo "  clean            - Clean generated files"
	@echo "  build            - Build the project"
	@echo "  test             - Run tests"
	@echo "  run              - Run the application"
	@echo "  format           - Format code using Google Java Format"
	@echo "  docker-build     - Build Docker image"

# Refresh protobuf files (copy from contracts)
.PHONY: refresh-protos
refresh-protos:
	@echo "Refreshing protobuf files..."
	@if not exist "src\main\proto" mkdir src\main\proto
	@copy "$(PROTO_DIR)\*.proto" "src\main\proto\" 2>nul || echo "No proto files found in $(PROTO_DIR)"
	@echo "Protobuf files refreshed"

# Compile protobuf files
.PHONY: compile-protos
compile-protos: refresh-protos
	@echo "Compiling protobuf files..."
	@mvn protobuf:compile protobuf:compile-custom
	@echo "Protobuf compilation completed"

# Clean generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	@mvn clean
	@if exist "$(LIBS_DIR)" rmdir /s /q "$(LIBS_DIR)"
	@if exist "src\main\proto" rmdir /s /q "src\main\proto"
	@echo "Clean completed"

# Build the project
.PHONY: build
build: compile-protos
	@echo "Building project..."
	@mvn compile
	@echo "Build completed"

# Run tests
.PHONY: test
test:
	@echo "Running tests..."
	@mvn test
	@echo "Tests completed"

# Run the application
.PHONY: run
run:
	@echo "Running application..."
	@mvn spring-boot:run -Dspring-boot.run.profiles=dev

# Format code
.PHONY: format
format:
	@echo "Formatting code..."
	@mvn fmt:format
	@echo "Code formatting completed"

# Package the application
.PHONY: package
package: test
	@echo "Packaging application..."
	@mvn package -DskipTests
	@echo "Packaging completed"

# Docker build
.PHONY: docker-build
docker-build: package
	@echo "Building Docker image..."
	@docker build -t trip-note-service:latest .
	@echo "Docker image built successfully"

# Development setup
.PHONY: dev-setup
dev-setup: compile-protos
	@echo "Setting up development environment..."
	@mvn dependency:resolve
	@echo "Development setup completed"

# Install dependencies
.PHONY: install
install:
	@echo "Installing dependencies..."
	@mvn dependency:resolve
	@echo "Dependencies installed"