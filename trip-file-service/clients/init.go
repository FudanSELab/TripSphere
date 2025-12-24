package clients

import (
	"trip-file-service/clients/minio"
	"trip-file-service/clients/nacos"
)

func Init() {
	minio.Init()
	nacos.Init()
}
