package org.tripsphere.poi.infrastructure.adapter.inbound.grpc;

import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.info.BuildProperties;
import org.tripsphere.poi.v1.GetVersionRequest;
import org.tripsphere.poi.v1.GetVersionResponse;
import org.tripsphere.poi.v1.MetadataServiceGrpc;

@GrpcService
public class MetadataGrpcService extends MetadataServiceGrpc.MetadataServiceImplBase {

    private final BuildProperties buildProperties;

    public MetadataGrpcService(@Autowired(required = false) BuildProperties buildProperties) {
        this.buildProperties = buildProperties;
    }

    @Override
    public void getVersion(GetVersionRequest request, StreamObserver<GetVersionResponse> responseObserver) {
        String version = buildProperties != null ? buildProperties.getVersion() : "develop";
        responseObserver.onNext(
                GetVersionResponse.newBuilder().setVersion(version).build());
        responseObserver.onCompleted();
    }
}
