package config

import (
	"fmt"
	"os"
	"strconv"
)

var (
	AppEnv  string
	AppName string
	Port    string
	PortInt uint64
	PodIP   string

	NacosHost      string
	NacosPort      string
	NacosPortInt   uint64
	NacosNamespace string
	NacosGroup     string
	NacosUsername  string
	NacosPassword  string

	MinIOEndpoint        string
	MinIOAccessKeyID     string
	MinIOSecretAccessKey string
	MinIOUseSSL          bool
)

func getEnv(key string, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

func Init() {
	AppEnv = getEnv("APP_ENV", "dev")
	AppName = getEnv("APP_NAME", "trip-file-service")
	Port = getEnv("PORT", "50051")
	portInt, err := strconv.ParseUint(Port, 10, 64)
	if err != nil {
		panic(fmt.Errorf("failed to parse port: %w", err))
	}
	PortInt = portInt
	PodIP = getEnv("POD_IP", "")

	NacosHost = getEnv("NACOS_HOST", "localhost")
	NacosPort = getEnv("NACOS_PORT", "8848")
	NacosNamespace = getEnv("NACOS_NAMESPACE", "public")
	NacosGroup = getEnv("NACOS_GROUP", "DEFAULT_GROUP")
	NacosUsername = getEnv("NACOS_USERNAME", "nacos")
	NacosPassword = getEnv("NACOS_PASSWORD", "nacos")
	NacosPortInt, err = strconv.ParseUint(NacosPort, 10, 64)
	if err != nil {
		panic(fmt.Errorf("failed to parse nacos port: %w", err))
	}

	MinIOEndpoint = getEnv("MINIO_ENDPOINT", "minio:9000")
	MinIOAccessKeyID = getEnv("MINIO_ACCESS_KEY_ID", "minioadmin")
	MinIOSecretAccessKey = getEnv("MINIO_SECRET_ACCESS_KEY", "minioadmin")
	MinIOUseSSL = getEnv("MINIO_USE_SSL", "false") == "true"
}
