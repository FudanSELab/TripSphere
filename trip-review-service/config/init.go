package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
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

	// MySQL Configuration
	MySQLHost     string
	MySQLPort     string
	MySQLUser     string
	MySQLPassword string
	MySQLDatabase string

	// MySQL Connection Pool Configuration
	MySQLMaxOpenConn     int
	MySQLMaxIdleConn     int
	MySQLConnMaxLifeTime time.Duration

	// RocketMQ Configuration
	RocketMQGroupName string
	RocketMQEndpoint  string
	RocketMQAccessKey string
	RocketMQSecretKey string
)

func getEnv(key string, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

func getEnvAsInt(key string, defaultValue int) int {
	valueStr := getEnv(key, "")
	if valueStr == "" {
		return defaultValue
	}
	value, err := strconv.Atoi(valueStr)
	if err != nil {
		return defaultValue
	}
	return value
}

func getEnvAsDuration(key string, defaultValue time.Duration) time.Duration {
	valueStr := getEnv(key, "")
	if valueStr == "" {
		return defaultValue
	}
	value, err := time.ParseDuration(valueStr)
	if err != nil {
		return defaultValue
	}
	return value
}

func Init() {
	// App Configuration
	AppEnv = getEnv("APP_ENV", "dev")
	AppName = getEnv("APP_NAME", "trip-review-service")
	Port = getEnv("PORT", "50057")
	portInt, err := strconv.ParseUint(Port, 10, 64)
	if err != nil {
		panic(fmt.Errorf("failed to parse port: %w", err))
	}
	PortInt = portInt
	PodIP = getEnv("POD_IP", "")

	// Nacos Configuration
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

	// MySQL Configuration
	MySQLHost = getEnv("MYSQL_HOST", "localhost")
	MySQLPort = getEnv("MYSQL_PORT", "3306")
	MySQLUser = getEnv("MYSQL_USER", "root")
	MySQLPassword = getEnv("MYSQL_PASSWORD", "")
	MySQLDatabase = getEnv("MYSQL_DATABASE", "review_db")

	// MySQL Connection Pool Configuration
	MySQLMaxOpenConn = getEnvAsInt("MYSQL_MAX_OPEN_CONN", 100)
	MySQLMaxIdleConn = getEnvAsInt("MYSQL_MAX_IDLE_CONN", 10)
	MySQLConnMaxLifeTime = getEnvAsDuration("MYSQL_CONN_MAX_LIFETIME", 1*time.Hour)

	// RocketMQ Configuration
	RocketMQGroupName = getEnv("ROCKETMQ_GROUP_NAME", "")
	RocketMQEndpoint = getEnv("ROCKETMQ_ENDPOINT", "localhost:8081")
	RocketMQAccessKey = getEnv("ROCKETMQ_ACCESS_KEY", "")
	RocketMQSecretKey = getEnv("ROCKETMQ_SECRET_KEY", "")
}
