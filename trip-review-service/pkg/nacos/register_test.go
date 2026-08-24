package nacos

import (
	"testing"

	"github.com/stretchr/testify/require"
)

func TestRegisterInstanceParamIncludesDiscoveryMetadata(t *testing.T) {
	param := newRegisterInstanceParam("trip-review-service", "127.0.0.1", 50057)

	require.Equal(t, "trip-review-service", param.ServiceName)
	require.Equal(t, uint64(50057), param.Port)
	require.Equal(t, map[string]string{
		"gRPC_port": "50057",
		"protocol":  "grpc",
	}, param.Metadata)
}
