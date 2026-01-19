package nacos

import (
	"context"
	"net"

	"github.com/nacos-group/nacos-sdk-go/v2/vo"
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
func (c *Client) Register(ctx context.Context, serviceName string, port uint64) error {
	if c == nil {
		return nil
	}
	registerIP := getLocalIP()
	return c.RegisterInstance(ctx, vo.RegisterInstanceParam{
		Ip:          registerIP,
		Port:        port,
		ServiceName: serviceName,
		Weight:      1,
		Enable:      true,
		Healthy:     true,
		Ephemeral:   true,
	})
}

// Deregister deregisters the service from Nacos
func (c *Client) Deregister(ctx context.Context, serviceName string, port uint64) error {
	if c == nil {
		return nil
	}
	registerIP := getLocalIP()
	return c.DeregisterInstance(ctx, vo.DeregisterInstanceParam{
		Ip:          registerIP,
		Port:        port,
		ServiceName: serviceName,
	})
}
