package org.tripsphere.note.grpc;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.info.BuildProperties;
import org.tripsphere.note.GetVersionRequest;
import org.tripsphere.note.GetVersionResponse;
import org.tripsphere.note.MetadataServiceGrpc;

import io.grpc.stub.StreamObserver;

import net.devh.boot.grpc.server.service.GrpcService;

@GrpcService
public class MetadataServiceImpl extends MetadataServiceGrpc.MetadataServiceImplBase {
    private final BuildProperties buildProperties;

    public MetadataServiceImpl(@Autowired(required = false) BuildProperties buildProperties) {
        this.buildProperties = buildProperties;
    }

    @Override
    public void getVersion(
            GetVersionRequest request, StreamObserver<GetVersionResponse> responseObserver) {
        String version =
                buildProperties != null
                        ? buildProperties.getVersion()
                        : "develop"; // Default version in development environment
        GetVersionResponse response = GetVersionResponse.newBuilder().setVersion(version).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }
}
