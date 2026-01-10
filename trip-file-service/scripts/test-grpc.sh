#!/bin/bash

# gRPC Server test script
# Used to quickly test FileService gRPC server

set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SERVER_ADDRESS="${1:-localhost:50051}"

echo -e "${GREEN}=== FileService gRPC Server Test ===${NC}"
echo -e "Server address: ${YELLOW}${SERVER_ADDRESS}${NC}\n"

# Check if server is running
echo -e "${YELLOW}Checking server connection...${NC}"
if ! timeout 2 bash -c "echo > /dev/tcp/${SERVER_ADDRESS%:*}/${SERVER_ADDRESS#*:}" 2>/dev/null; then
    echo -e "${RED}Error: Unable to connect to server ${SERVER_ADDRESS}${NC}"
    echo -e "${YELLOW}Please ensure:${NC}"
    echo "  1. gRPC server is running (go run cmd/main.go)"
    echo "  2. Server address is correct"
    exit 1
fi
echo -e "${GREEN}✓ Server connection OK${NC}\n"

# Run test client
echo -e "${GREEN}Running test client...${NC}\n"
go run cmd/test_client/main.go -addr "${SERVER_ADDRESS}"

echo -e "\n${GREEN}Test completed!${NC}"

