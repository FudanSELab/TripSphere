package main

import (
	"bytes"
	"context"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "trip-file-service/clients/grpc/gen/file"
)

const (
	defaultAddress = "localhost:50051"
	testFileName   = "test.txt"
)

func main() {
	address := flag.String("addr", defaultAddress, "gRPC server address")
	flag.Parse()

	// Connect to gRPC server
	conn, err := grpc.NewClient(*address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("failed to connect to server: %v", err)
	}
	defer conn.Close()

	client := pb.NewFileServiceClient(conn)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	fmt.Println("=== FileService gRPC Test Client ===")

	// Get test file path
	_, currentFile, _, _ := runtime.Caller(0)
	testFilePath := filepath.Join(filepath.Dir(currentFile), testFileName)

	// Check if file exists
	if _, err := os.Stat(testFilePath); os.IsNotExist(err) {
		log.Fatalf("test file does not exist: %s", testFilePath)
	}
	fmt.Printf("✓ Using test file: %s\n\n", testFilePath)

	// Define test file info
	testFileInfo := &pb.File{
		Service:     "test-service",
		Path:        "test/test-file.txt",
		Name:        "test-file.txt",
		ContentType: "text/plain",
		Bucket:      "permanent",
	}

	tempFileInfo := &pb.File{
		Service:     "test-service",
		Path:        "temp/temp-test-file.txt",
		Name:        "temp-test-file.txt",
		ContentType: "text/plain",
		Bucket:      "temp",
	}

	// Test 1: GetUploadSignedUrl and upload file
	fmt.Println("1. Testing GetUploadSignedUrl and uploading file...")
	uploadedFile, err := testGetUploadSignedUrlAndUpload(ctx, client, testFileInfo, testFilePath)
	if err != nil {
		log.Printf("warning: failed to upload file: %v", err)
	} else {
		testFileInfo = uploadedFile
	}

	// Test 2: GetTempUploadSignedUrl and upload temporary file
	fmt.Println("\n2. Testing GetTempUploadSignedUrl and uploading temporary file...")
	uploadedTempFile, err := testGetTempUploadSignedUrlAndUpload(ctx, client, tempFileInfo, testFilePath)
	if err != nil {
		log.Printf("warning: failed to upload temporary file: %v", err)
	} else {
		tempFileInfo = uploadedTempFile
	}

	// Test 3: GetDownloadSignedUrls (using uploaded file)
	fmt.Println("\n3. Testing GetDownloadSignedUrls...")
	testGetDownloadSignedUrls(ctx, client, testFileInfo)

	// Test 4: CopyFiles (using uploaded file)
	fmt.Println("\n4. Testing CopyFiles...")
	copiedFile, err := testCopyFiles(ctx, client, testFileInfo)
	if err != nil {
		log.Printf("warning: failed to copy file: %v", err)
	}

	// Test 5: CopyToPermanent (using uploaded temporary file)
	fmt.Println("\n5. Testing CopyToPermanent...")
	var permanentFile *pb.File
	if tempFileInfo.Bucket == "temp" {
		req := &pb.CopyToPermanentRequest{
			Files: []*pb.File{tempFileInfo},
		}
		resp, err := client.CopyToPermanent(ctx, req)
		if err != nil {
			log.Printf("error: %v", err)
		} else {
			fmt.Printf("✓ Successfully copied files to permanent storage\n")
			fmt.Printf("  - Copied %d files from temporary storage to permanent storage\n", len(resp.Files))
			for i, file := range resp.Files {
				fmt.Printf("  [%d] %s/%s (bucket: %s)\n", i+1, file.Service, file.Path, file.Bucket)
				if i == 0 {
					permanentFile = file
				}
			}
		}
	} else {
		fmt.Printf("  Skipped: temporary file was not successfully uploaded\n")
	}

	// Test 6: DeleteFiles (cleanup test files)
	fmt.Println("\n6. Testing DeleteFiles...")
	filesToDelete := []*pb.File{}
	// Add permanent file
	if testFileInfo != nil {
		filesToDelete = append(filesToDelete, testFileInfo)
	}
	// Add copied file
	if copiedFile != nil {
		filesToDelete = append(filesToDelete, copiedFile)
	}
	// Add file copied from temporary storage to permanent storage
	if permanentFile != nil {
		filesToDelete = append(filesToDelete, permanentFile)
	}
	if len(filesToDelete) > 0 {
		testDeleteFiles(ctx, client, filesToDelete)
	} else {
		fmt.Printf("  Skipped: no test files to delete\n")
	}

	fmt.Println("\n=== All tests completed ===")
}

// uploadFile uploads a file using a signed URL
func uploadFile(signedURL, filePath string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	fileContent, err := io.ReadAll(file)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	req, err := http.NewRequest("PUT", signedURL, bytes.NewReader(fileContent))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "text/plain")

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to upload request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("upload failed, status code: %d, response: %s", resp.StatusCode, string(body))
	}

	return nil
}

// testGetUploadSignedUrlAndUpload gets upload URL and actually uploads the file
func testGetUploadSignedUrlAndUpload(ctx context.Context, client pb.FileServiceClient, fileInfo *pb.File, filePath string) (*pb.File, error) {
	req := &pb.GetUploadSignedUrlRequest{
		File: fileInfo,
	}

	resp, err := client.GetUploadSignedUrl(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get upload URL: %w", err)
	}

	fmt.Printf("✓ Successfully got upload signed URL\n")
	fmt.Printf("  - Service: %s\n", resp.File.Service)
	fmt.Printf("  - Path: %s\n", resp.File.Path)
	fmt.Printf("  - Bucket: %s\n", resp.File.Bucket)
	fmt.Printf("  - URL: %s\n", resp.File.Url)

	// Actually upload the file
	fmt.Printf("  Uploading file...\n")
	if err := uploadFile(resp.File.Url, filePath); err != nil {
		return nil, fmt.Errorf("failed to upload file: %w", err)
	}

	fmt.Printf("✓ File uploaded successfully\n")
	return resp.File, nil
}

// testGetTempUploadSignedUrlAndUpload gets temporary upload URL and actually uploads the file
func testGetTempUploadSignedUrlAndUpload(ctx context.Context, client pb.FileServiceClient, fileInfo *pb.File, filePath string) (*pb.File, error) {
	req := &pb.GetTempUploadSignedUrlRequest{
		File: fileInfo,
	}

	resp, err := client.GetTempUploadSignedUrl(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get temporary upload URL: %w", err)
	}

	fmt.Printf("✓ Successfully got temporary upload signed URL\n")
	fmt.Printf("  - Service: %s\n", resp.File.Service)
	fmt.Printf("  - Path: %s\n", resp.File.Path)
	fmt.Printf("  - Bucket: %s\n", resp.File.Bucket)
	fmt.Printf("  - URL: %s\n", resp.File.Url)

	// Actually upload the file
	fmt.Printf("  Uploading temporary file...\n")
	if err := uploadFile(resp.File.Url, filePath); err != nil {
		return nil, fmt.Errorf("failed to upload temporary file: %w", err)
	}

	fmt.Printf("✓ Temporary file uploaded successfully\n")
	return resp.File, nil
}

// testGetDownloadSignedUrls gets download signed URLs (using uploaded file)
func testGetDownloadSignedUrls(ctx context.Context, client pb.FileServiceClient, uploadedFile *pb.File) {
	req := &pb.GetDownloadSignedUrlsRequest{
		Files: []*pb.File{
			uploadedFile,
		},
	}

	resp, err := client.GetDownloadSignedUrls(ctx, req)
	if err != nil {
		log.Printf("error: %v", err)
		return
	}

	fmt.Printf("✓ Successfully got download signed URLs\n")
	fmt.Printf("  - Got download URLs for %d files\n", len(resp.Files))
	for i, file := range resp.Files {
		fmt.Printf("  [%d] %s/%s -> %s\n", i+1, file.Bucket, file.Path, file.Url)
		// Verify if download URL is available
		if file.Url != "" {
			fmt.Printf("      (you can access this URL to download the file)\n")
		}
	}
}

// testCopyFiles copies files (using uploaded file)
func testCopyFiles(ctx context.Context, client pb.FileServiceClient, sourceFile *pb.File) (*pb.File, error) {
	destinationFile := &pb.File{
		Service:     sourceFile.Service,
		Path:        "test/copied-file.txt",
		Name:        "copied-file.txt",
		ContentType: sourceFile.ContentType,
		Bucket:      sourceFile.Bucket,
	}

	req := &pb.CopyFilesRequest{
		CopyFiles: []*pb.CopyFilePair{
			{
				From: sourceFile,
				To:   destinationFile,
			},
		},
	}

	resp, err := client.CopyFiles(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to copy file: %w", err)
	}

	fmt.Printf("✓ Successfully copied file\n")
	fmt.Printf("  - From: %s/%s\n", sourceFile.Bucket, sourceFile.Path)
	fmt.Printf("  - To: %s/%s\n", destinationFile.Bucket, destinationFile.Path)
	fmt.Printf("  - Response: %+v\n", resp)

	return destinationFile, nil
}

// testDeleteFiles deletes files (cleanup test files)
func testDeleteFiles(ctx context.Context, client pb.FileServiceClient, files []*pb.File) {
	req := &pb.DeleteFilesRequest{
		Files: files,
	}

	resp, err := client.DeleteFiles(ctx, req)
	if err != nil {
		log.Printf("error: %v", err)
		return
	}

	fmt.Printf("✓ Successfully deleted files\n")
	fmt.Printf("  - Deleted %d files\n", len(files))
	for i, file := range files {
		fmt.Printf("  [%d] %s/%s\n", i+1, file.Bucket, file.Path)
	}
	fmt.Printf("  - Response: %+v\n", resp)
}
