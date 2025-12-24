package server

import (
	"context"
	"fmt"
	"path/filepath"
	"time"

	minioGo "github.com/minio/minio-go/v7"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	pb "trip-file-service/clients/grpc/gen/file"
	"trip-file-service/clients/minio"
)

const (
	// Default presigned URL expiry duration
	defaultPresignedURLExpiry = 1 * time.Hour
	// Bucket names
	bucketTemp      = "temp"
	bucketPermanent = "permanent"
)

// FileServer implements the gRPC server for FileService
type FileServer struct {
	pb.UnimplementedFileServiceServer
	minioClient *minio.Client
}

// NewFileServer creates a new FileServer instance
func NewFileServer() *FileServer {
	return &FileServer{
		minioClient: minio.MinIO,
	}
}

// getObjectName constructs the object name from service and path
func (s *FileServer) getObjectName(service, path string) string {
	return filepath.Join(service, path)
}

// GetUploadSignedUrl gets a signed URL for permanent file upload
func (s *FileServer) GetUploadSignedUrl(ctx context.Context, req *pb.GetUploadSignedUrlRequest) (*pb.GetUploadSignedUrlResponse, error) {
	if req.File == nil {
		return nil, status.Error(codes.InvalidArgument, "file is required")
	}

	if req.File.Service == "" || req.File.Path == "" {
		return nil, status.Error(codes.InvalidArgument, "service and path fields are required")
	}

	// Ensure bucket exists
	objectName := s.getObjectName(req.File.Service, req.File.Path)
	if err := s.minioClient.EnsureBucket(ctx, bucketPermanent, ""); err != nil {
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to ensure permanent bucket: %v", err))
	}

	// Generate presigned URL for upload
	url, err := s.minioClient.PresignedPutObject(ctx, bucketPermanent, objectName, defaultPresignedURLExpiry)
	if err != nil {
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to generate presigned upload URL: %v", err))
	}

	file := &pb.File{
		Name:        req.File.Name,
		ContentType: req.File.ContentType,
		Url:         url,
		Bucket:      bucketPermanent,
		Service:     req.File.Service,
		Path:        req.File.Path,
	}

	return &pb.GetUploadSignedUrlResponse{
		File: file,
	}, nil
}

// GetTempUploadSignedUrl gets a signed URL for temporary file upload
func (s *FileServer) GetTempUploadSignedUrl(ctx context.Context, req *pb.GetTempUploadSignedUrlRequest) (*pb.GetTempUploadSignedUrlResponse, error) {
	if req.File == nil {
		return nil, status.Error(codes.InvalidArgument, "file is required")
	}

	if req.File.Service == "" || req.File.Path == "" {
		return nil, status.Error(codes.InvalidArgument, "service and path fields are required")
	}

	// Ensure bucket exists
	objectName := s.getObjectName(req.File.Service, req.File.Path)
	if err := s.minioClient.EnsureBucket(ctx, bucketTemp, ""); err != nil {
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to ensure temp bucket: %v", err))
	}

	// Generate presigned URL for upload
	url, err := s.minioClient.PresignedPutObject(ctx, bucketTemp, objectName, defaultPresignedURLExpiry)
	if err != nil {
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to generate presigned temp upload URL: %v", err))
	}

	file := &pb.File{
		Name:        req.File.Name,
		ContentType: req.File.ContentType,
		Url:         url,
		Bucket:      bucketTemp,
		Service:     req.File.Service,
		Path:        req.File.Path,
	}

	return &pb.GetTempUploadSignedUrlResponse{
		File: file,
	}, nil
}

// GetDownloadSignedUrls gets signed URLs for batch file downloads
func (s *FileServer) GetDownloadSignedUrls(ctx context.Context, req *pb.GetDownloadSignedUrlsRequest) (*pb.GetDownloadSignedUrlsResponse, error) {
	if len(req.Files) == 0 {
		return nil, status.Error(codes.InvalidArgument, "files list cannot be empty")
	}

	files := make([]*pb.File, 0, len(req.Files))
	for _, f := range req.Files {
		if f == nil {
			continue
		}
		if f.Service == "" || f.Path == "" {
			continue
		}
		if f.Bucket == "" {
			f.Bucket = bucketPermanent // Default to permanent bucket
		}

		objectName := s.getObjectName(f.Service, f.Path)
		url, err := s.minioClient.PresignedGetObject(ctx, f.Bucket, objectName, defaultPresignedURLExpiry, nil)
		if err != nil {
			// Skip files that fail to generate URL, but continue processing others
			continue
		}

		file := &pb.File{
			Name:        f.Name,
			ContentType: f.ContentType,
			Url:         url,
			Bucket:      f.Bucket,
			Service:     f.Service,
			Path:        f.Path,
		}
		files = append(files, file)
	}

	if len(files) == 0 {
		return nil, status.Error(codes.Internal, "failed to generate any download URLs")
	}

	return &pb.GetDownloadSignedUrlsResponse{
		Files: files,
	}, nil
}

// CopyFiles copies files to new locations in batch
func (s *FileServer) CopyFiles(ctx context.Context, req *pb.CopyFilesRequest) (*pb.CopyFilesResponse, error) {
	if len(req.CopyFiles) == 0 {
		return nil, status.Error(codes.InvalidArgument, "copy_files list cannot be empty")
	}

	// Validate all copy pairs
	for _, pair := range req.CopyFiles {
		if pair.From == nil || pair.To == nil {
			return nil, status.Error(codes.InvalidArgument, "from and to files are required")
		}
		if pair.From.Service == "" || pair.From.Path == "" {
			return nil, status.Error(codes.InvalidArgument, "from file service and path are required")
		}
		if pair.To.Service == "" || pair.To.Path == "" {
			return nil, status.Error(codes.InvalidArgument, "to file service and path are required")
		}
		if pair.From.Bucket == "" {
			pair.From.Bucket = bucketPermanent // Default to permanent bucket
		}
		if pair.To.Bucket == "" {
			pair.To.Bucket = bucketPermanent // Default to permanent bucket
		}
	}

	// Execute copy operations
	for _, pair := range req.CopyFiles {
		fromBucket := pair.From.Bucket
		fromObjectName := s.getObjectName(pair.From.Service, pair.From.Path)
		toBucket := pair.To.Bucket
		toObjectName := s.getObjectName(pair.To.Service, pair.To.Path)

		// Ensure destination bucket exists
		if err := s.minioClient.EnsureBucket(ctx, toBucket, ""); err != nil {
			return nil, status.Error(codes.Internal, fmt.Sprintf("failed to ensure destination bucket %s: %v", toBucket, err))
		}

		// Copy object
		src := minioGo.CopySrcOptions{
			Bucket: fromBucket,
			Object: fromObjectName,
		}
		dst := minioGo.CopyDestOptions{
			Bucket: toBucket,
			Object: toObjectName,
		}

		_, err := s.minioClient.CopyObject(ctx, dst, src)
		if err != nil {
			return nil, status.Error(codes.Internal, fmt.Sprintf("failed to copy file from %s/%s to %s/%s: %v", fromBucket, fromObjectName, toBucket, toObjectName, err))
		}
	}

	return &pb.CopyFilesResponse{}, nil
}

// DeleteFiles deletes files in batch
func (s *FileServer) DeleteFiles(ctx context.Context, req *pb.DeleteFilesRequest) (*pb.DeleteFilesResponse, error) {
	if len(req.Files) == 0 {
		return nil, status.Error(codes.InvalidArgument, "files list cannot be empty")
	}

	// Validate all files and group by bucket
	bucketFiles := make(map[string][]string)
	for _, f := range req.Files {
		if f == nil {
			continue
		}
		if f.Service == "" || f.Path == "" {
			return nil, status.Error(codes.InvalidArgument, "file service and path are required")
		}
		bucket := f.Bucket
		if bucket == "" {
			bucket = bucketPermanent // Default to permanent bucket
		}
		objectName := s.getObjectName(f.Service, f.Path)
		bucketFiles[bucket] = append(bucketFiles[bucket], objectName)
	}

	// Execute delete operations
	for bucket, objectNames := range bucketFiles {
		for _, objectName := range objectNames {
			err := s.minioClient.RemoveObject(ctx, bucket, objectName, minioGo.RemoveObjectOptions{})
			if err != nil {
				return nil, status.Error(codes.Internal, fmt.Sprintf("failed to delete file %s/%s: %v", bucket, objectName, err))
			}
		}
	}

	return &pb.DeleteFilesResponse{}, nil
}

// CopyToPermanent copies temporary files to permanent storage bucket
func (s *FileServer) CopyToPermanent(ctx context.Context, req *pb.CopyToPermanentRequest) (*pb.CopyToPermanentResponse, error) {
	if len(req.Files) == 0 {
		return nil, status.Error(codes.InvalidArgument, "files list cannot be empty")
	}

	// Ensure permanent bucket exists
	if err := s.minioClient.EnsureBucket(ctx, bucketPermanent, ""); err != nil {
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to ensure permanent bucket: %v", err))
	}

	// Skip files already in permanent bucket and copy others
	files := make([]*pb.File, 0)
	for _, f := range req.Files {
		if f == nil {
			continue
		}
		if f.Bucket == bucketPermanent {
			// Already in permanent bucket, skip
			continue
		}
		if f.Service == "" || f.Path == "" {
			return nil, status.Error(codes.InvalidArgument, "file service and path are required")
		}

		fromBucket := f.Bucket
		if fromBucket == "" {
			fromBucket = bucketTemp // Default to temp bucket if not specified
		}
		objectName := s.getObjectName(f.Service, f.Path)

		// Copy object from temp to permanent bucket
		src := minioGo.CopySrcOptions{
			Bucket: fromBucket,
			Object: objectName,
		}
		dst := minioGo.CopyDestOptions{
			Bucket: bucketPermanent,
			Object: objectName,
		}

		_, err := s.minioClient.CopyObject(ctx, dst, src)
		if err != nil {
			return nil, status.Error(codes.Internal, fmt.Sprintf("failed to copy file %s/%s to permanent bucket: %v", fromBucket, objectName, err))
		}

		// Create new file object with permanent bucket
		newFile := &pb.File{
			Name:        f.Name,
			ContentType: f.ContentType,
			Bucket:      bucketPermanent,
			Service:     f.Service,
			Path:        f.Path,
		}
		files = append(files, newFile)
	}

	return &pb.CopyToPermanentResponse{
		Files: files,
	}, nil
}
