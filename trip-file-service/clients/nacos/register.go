package nacos

import (
	"context"
	"net"
	"trip-file-service/config"

	"github.com/nacos-group/nacos-sdk-go/v2/vo"
)

var (
	registerIP string
)

// getLocalIP gets the local IP address
// It first tries to connect to an external address to get the actual IP,
// and falls back to getting the hostname IP if that fails.
func getLocalIP() string {
	// Try to connect to an external address to get the actual local IP
	conn, err := net.Dial("udp", "8.8.8.8:80")
	if err == nil {
		defer conn.Close()
		localAddr := conn.LocalAddr().(*net.UDPAddr)
		return localAddr.IP.String()
	}
	// Fallback: get IP from hostname
	hostname, err := net.LookupHost("localhost")
	if err == nil && len(hostname) > 0 {
		return hostname[0]
	}
	// Last resort: return localhost
	return "127.0.0.1"
}

// Register registers the service to Nacos
func Register(ctx context.Context) error {
	if Nacos == nil {
		return nil
	}
	registerIP := getLocalIP()
	return Nacos.RegisterInstance(ctx, vo.RegisterInstanceParam{
		Ip:          registerIP,
		Port:        config.PortInt,
		ServiceName: config.AppName,
		Ephemeral:   true,
	})
}
