package nacos

import (
	"context"
	"trip-file-service/config"

	"github.com/nacos-group/nacos-sdk-go/v2/vo"
)

// Deregister deregisters the service from Nacos
func Deregister(ctx context.Context) error {
	if Nacos == nil {
		return nil
	}
	param := vo.DeregisterInstanceParam{
		Ip:          registerIP,
		Port:        config.PortInt,
		ServiceName: config.AppName,
		Ephemeral:   true,
	}
	return Nacos.DeregisterInstance(ctx, param)
}
