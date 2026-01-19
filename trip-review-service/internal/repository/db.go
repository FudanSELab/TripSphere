package repository

import (
	"fmt"
	"log"
	"strings"

	"gorm.io/driver/mysql"
	"gorm.io/gorm"

	"trip-review-service/config"
)

var db *gorm.DB

func GetDB() *gorm.DB {
	return db
}

func init() {
	// Initialize config first
	config.Init()

	// Build DSN (Data Source Name)
	// Format: username:password@tcp(host:port)/dbname?parseTime=true&charset=utf8mb4
	builder := strings.Builder{}
	builder.Grow(128)
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4",
		config.MySQLUser,
		config.MySQLPassword,
		config.MySQLHost,
		config.MySQLPort,
		config.MySQLDatabase)
	builder.WriteString(dsn)

	// Open database connection
	var err error
	db, err = gorm.Open(mysql.Open(builder.String()), &gorm.Config{})
	if err != nil {
		log.Println("database connect failed", err)
		return
	}

	// Configure connection pool
	sqlDB, err := db.DB()
	if err != nil {
		log.Println("failed to get database instance", err)
		return
	}

	sqlDB.SetMaxOpenConns(config.MySQLMaxOpenConn)
	sqlDB.SetMaxIdleConns(config.MySQLMaxIdleConn)
	sqlDB.SetConnMaxLifetime(config.MySQLConnMaxLifeTime)

	log.Println("connect to database successfully")

	reviewRepo = NewReviewRepo(db)
}
