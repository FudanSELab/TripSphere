package org.tripsphere.inventory;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.env.Environment;

@SpringBootTest(properties = {
    "spring.cloud.nacos.discovery.enabled=false",
    "spring.cloud.nacos.discovery.register-enabled=false"
})
class DiscoveryMetadataTests {

    @Autowired
    private Environment environment;

    @Test
    void exposesGrpcDiscoveryMetadata() {
        assertThat(environment.getProperty("spring.cloud.nacos.discovery.metadata.gRPC_port"))
            .isEqualTo(environment.getProperty("grpc.server.port"));
        assertThat(environment.getProperty("spring.cloud.nacos.discovery.metadata.protocol"))
            .isEqualTo("grpc");
    }
}
