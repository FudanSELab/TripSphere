package nacos

import (
	"context"

	"trip-file-service/config"
)

var Nacos *Client

func Init() {
	ctx := context.Background()

	client, err := NewClient(ctx, Config{
		Host:        config.NacosHost,
		Port:        int(config.NacosPortInt),
		NamespaceID: config.NacosNamespace,
		GroupName:   config.NacosGroup,
		Username:    config.NacosUsername,
		Password:    config.NacosPassword,
	})
	if err != nil {
		panic(err)
	}
	Nacos = client
}
