package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

// Config holds all configuration for the application
type Config struct {
	App     AppConfig
	Nacos   NacosConfig
	MongoDB MongoDBConfig
}

// AppConfig holds application configuration
type AppConfig struct {
	Env   string
	Name  string
	Port  int
	PodIP string
}

// NacosConfig holds Nacos configuration
type NacosConfig struct {
	Host      string
	Port      int
	Namespace string
	Group     string
	Username  string
	Password  string
}

// MongoDBConfig holds MongoDB configuration
type MongoDBConfig struct {
	URI            string
	Database       string
	ConnectTimeout time.Duration
	MaxPoolSize    uint64
	MinPoolSize    uint64
}

// Load loads configuration from environment variables
func Load() (*Config, error) {
	port, err := strconv.Atoi(getEnv("PORT", "50057"))
	if err != nil {
		return nil, fmt.Errorf("invalid PORT: %w", err)
	}

	nacosPort, err := strconv.Atoi(getEnv("NACOS_PORT", "8848"))
	if err != nil {
		return nil, fmt.Errorf("invalid NACOS_PORT: %w", err)
	}

	return &Config{
		App: AppConfig{
			Env:   getEnv("APP_ENV", "dev"),
			Name:  getEnv("APP_NAME", "trip-review-service"),
			Port:  port,
			PodIP: getEnv("POD_IP", ""),
		},
		Nacos: NacosConfig{
			Host:      getEnv("NACOS_HOST", ""),
			Port:      nacosPort,
			Namespace: getEnv("NACOS_NAMESPACE", "public"),
			Group:     getEnv("NACOS_GROUP", "DEFAULT_GROUP"),
			Username:  getEnv("NACOS_USERNAME", "nacos"),
			Password:  getEnv("NACOS_PASSWORD", "nacos"),
		},
		MongoDB: MongoDBConfig{
			URI:            getEnv("MONGODB_URI", "mongodb://localhost:27017"),
			Database:       getEnv("MONGODB_DATABASE", "review_db"),
			ConnectTimeout: getEnvAsDuration("MONGODB_CONNECT_TIMEOUT", 10*time.Second),
			MaxPoolSize:    getEnvAsUint64("MONGODB_MAX_POOL_SIZE", 100),
			MinPoolSize:    getEnvAsUint64("MONGODB_MIN_POOL_SIZE", 10),
		},
	}, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvAsUint64(key string, defaultValue uint64) uint64 {
	if value := os.Getenv(key); value != "" {
		if i, err := strconv.ParseUint(value, 10, 64); err == nil {
			return i
		}
	}
	return defaultValue
}

func getEnvAsDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if d, err := time.ParseDuration(value); err == nil {
			return d
		}
	}
	return defaultValue
}
