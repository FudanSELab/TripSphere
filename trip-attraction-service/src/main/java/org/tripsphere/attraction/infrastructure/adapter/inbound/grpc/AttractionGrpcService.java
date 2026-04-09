package org.tripsphere.attraction.infrastructure.adapter.inbound.grpc;

import io.grpc.stub.StreamObserver;
import java.util.List;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.attraction.application.exception.InvalidArgumentException;
import org.tripsphere.attraction.application.service.query.BatchGetAttractionsUseCase;
import org.tripsphere.attraction.application.service.query.GetAttractionByIdUseCase;
import org.tripsphere.attraction.application.service.query.GetAttractionsNearbyUseCase;
import org.tripsphere.attraction.application.service.query.ListAttractionsByCityUseCase;
import org.tripsphere.attraction.domain.model.Attraction;
import org.tripsphere.attraction.domain.model.GeoLocation;
import org.tripsphere.attraction.infrastructure.adapter.inbound.grpc.mapper.AttractionProtoMapper;
import org.tripsphere.attraction.infrastructure.util.CoordinateTransformUtil;
import org.tripsphere.attraction.v1.AttractionServiceGrpc;
import org.tripsphere.attraction.v1.BatchGetAttractionsRequest;
import org.tripsphere.attraction.v1.BatchGetAttractionsResponse;
import org.tripsphere.attraction.v1.GetAttractionByIdRequest;
import org.tripsphere.attraction.v1.GetAttractionByIdResponse;
import org.tripsphere.attraction.v1.GetAttractionsNearbyRequest;
import org.tripsphere.attraction.v1.GetAttractionsNearbyResponse;
import org.tripsphere.attraction.v1.ListAttractionsByCityRequest;
import org.tripsphere.attraction.v1.ListAttractionsByCityResponse;

@GrpcService
@RequiredArgsConstructor
public class AttractionGrpcService extends AttractionServiceGrpc.AttractionServiceImplBase {

    private static final double DEFAULT_RADIUS_METERS = 1000;

    private final GetAttractionByIdUseCase getAttractionByIdUseCase;
    private final BatchGetAttractionsUseCase batchGetAttractionsUseCase;
    private final GetAttractionsNearbyUseCase getAttractionsNearbyUseCase;
    private final ListAttractionsByCityUseCase listAttractionsByCityUseCase;
    private final AttractionProtoMapper protoMapper;

    @Override
    public void getAttractionById(
            GetAttractionByIdRequest request, StreamObserver<GetAttractionByIdResponse> responseObserver) {
        String id = request.getId();
        if (id.isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        Attraction attraction = getAttractionByIdUseCase.execute(id);

        responseObserver.onNext(GetAttractionByIdResponse.newBuilder()
                .setAttraction(protoMapper.toProto(attraction))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchGetAttractions(
            BatchGetAttractionsRequest request, StreamObserver<BatchGetAttractionsResponse> responseObserver) {
        List<String> ids = request.getIdsList();
        if (ids.isEmpty()) {
            responseObserver.onNext(BatchGetAttractionsResponse.newBuilder().build());
            responseObserver.onCompleted();
            return;
        }

        List<Attraction> attractions = batchGetAttractionsUseCase.execute(ids);

        responseObserver.onNext(BatchGetAttractionsResponse.newBuilder()
                .addAllAttractions(protoMapper.toProtoList(attractions))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void getAttractionsNearby(
            GetAttractionsNearbyRequest request, StreamObserver<GetAttractionsNearbyResponse> responseObserver) {
        if (!request.hasLocation()) {
            throw InvalidArgumentException.required("location");
        }

        double radiusMeters = request.getRadiusMeters() > 0 ? request.getRadiusMeters() : DEFAULT_RADIUS_METERS;
        List<String> tags = request.getTagsList();

        double[] wgs84 = CoordinateTransformUtil.gcj02ToWgs84(
                request.getLocation().getLongitude(), request.getLocation().getLatitude());
        GeoLocation location = new GeoLocation(wgs84[0], wgs84[1]);

        List<Attraction> attractions =
                getAttractionsNearbyUseCase.execute(location, radiusMeters, tags.isEmpty() ? null : tags);

        responseObserver.onNext(GetAttractionsNearbyResponse.newBuilder()
                .addAllAttractions(protoMapper.toProtoList(attractions))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void listAttractionsByCity(
            ListAttractionsByCityRequest request, StreamObserver<ListAttractionsByCityResponse> responseObserver) {
        String city = request.getCity();
        if (city.isEmpty()) {
            throw InvalidArgumentException.required("city");
        }

        List<Attraction> attractions = listAttractionsByCityUseCase.execute(
                city, request.getTagsList(), request.getPageSize(), request.getPageToken());

        int skip = 0;
        if (!request.getPageToken().isEmpty()) {
            try {
                skip = Integer.parseInt(request.getPageToken());
            } catch (NumberFormatException ignored) {
                skip = 0;
            }
        }
        int effectivePageSize = request.getPageSize() > 0 ? request.getPageSize() : 12;
        int nextSkip = skip + attractions.size();
        String nextPageToken = attractions.size() < effectivePageSize ? "" : String.valueOf(nextSkip);

        responseObserver.onNext(ListAttractionsByCityResponse.newBuilder()
                .addAllAttractions(protoMapper.toProtoList(attractions))
                .setNextPageToken(nextPageToken)
                .build());
        responseObserver.onCompleted();
    }
}
