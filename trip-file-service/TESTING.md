# FileService gRPC Server Testing Guide

This document describes how to test the FileService gRPC server functionality.

## Prerequisites

1. **Start dependency services**
   ```bash
   # Start MinIO and Nacos
   docker-compose -f docker-compose.dev.yaml up -d
   ```

2. **Start gRPC Server**
   ```bash
   # In the project root directory
   go run cmd/main.go
   ```

   The server will listen on `localhost:50051`.

## Testing Methods

We provide a complete Go test client that can test all gRPC methods. The test client will:
1. **Automatically create test files** - Creates a test text file in the system temporary directory
2. **Actually upload files** - After getting the signed URL, automatically uploads the test file to MinIO
3. **Use real files for testing** - All subsequent tests use the uploaded real files

#### Run Test Client

```bash
# In the project root directory
go run cmd/test_client/main.go
```

#### Specify Server Address

```bash
go run cmd/test_client/main.go -addr localhost:50051
```

#### Test Flow

The test client will execute the complete test flow in the following order:

1. **Create test file** - Creates a test text file in the temporary directory
2. **GetUploadSignedUrl + Upload** - Gets permanent file upload signed URL and actually uploads the test file
3. **GetTempUploadSignedUrl + Upload** - Gets temporary file upload signed URL and actually uploads the test file
4. **GetDownloadSignedUrls** - Gets download signed URLs using uploaded files
5. **CopyFiles** - Copies uploaded files to new locations
6. **CopyToPermanent** - Copies temporary files to permanent storage
7. **DeleteFiles** - Cleans up all test files (including original and copied files)
