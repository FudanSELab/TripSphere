package repository

import (
	"fmt"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	"log"
	"strings"
	"trip-review-service/configs"
)

var db *gorm.DB

func GetDB() *gorm.DB {
	return db
}

func init() {
	config := configs.GetConfig()
	builder := strings.Builder{}
	builder.Grow(128)
	connectionConfig := fmt.Sprintf("%s:%s@tcp(%s)/%s", config.MySQL.Write.User,
		config.MySQL.Write.Pass,
		config.MySQL.Write.Addr,
		config.MySQL.Write.Name)
	builder.WriteString(connectionConfig)

	var err error
	db, err = gorm.Open(mysql.Open(builder.String()), &gorm.Config{})
	if err != nil {
		log.Println("database connect failed", err)
	}
	log.Println("connect to database successfully")

	reviewRepo = NewReviewRepo(db)
}
