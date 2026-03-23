package org.tripsphere.attraction.api.grpc;

import io.grpc.stub.StreamObserver;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.attraction.exception.InvalidArgumentException;
import org.tripsphere.attraction.exception.NotFoundException;
import org.tripsphere.attraction.service.AttractionService;
import org.tripsphere.attraction.v1.Attraction;
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

    private final AttractionService attractionService;

    private static final double DEFAULT_RADIUS_METERS = 1000;

    @Override
    public void getAttractionById(
            GetAttractionByIdRequest request, StreamObserver<GetAttractionByIdResponse> responseObserver) {
        String id = request.getId();
        if (id.isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        Attraction attraction =
                attractionService.findById(id).orElseThrow(() -> new NotFoundException("Attraction", id));

        responseObserver.onNext(
                GetAttractionByIdResponse.newBuilder().setAttraction(attraction).build());
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

        List<Attraction> attractions = attractionService.findAllByIds(ids);

        Map<String, Attraction> attractionsById =
                attractions.stream().collect(Collectors.toMap(Attraction::getId, Function.identity()));

        List<String> missingIds =
                ids.stream().filter(id -> !attractionsById.containsKey(id)).toList();
        if (!missingIds.isEmpty()) {
            throw new NotFoundException("Attractions with IDs " + missingIds + " not found");
        }

        List<Attraction> orderedAttractions =
                ids.stream().map(attractionsById::get).toList();

        responseObserver.onNext(BatchGetAttractionsResponse.newBuilder()
                .addAllAttractions(orderedAttractions)
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

        List<Attraction> attractions =
                attractionService.searchNearby(request.getLocation(), radiusMeters, tags.isEmpty() ? null : tags);

        responseObserver.onNext(GetAttractionsNearbyResponse.newBuilder()
                .addAllAttractions(attractions)
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

        int pageSize = request.getPageSize() > 0 ? request.getPageSize() : 12;
        int skip = 0;
        String pageTokenStr = request.getPageToken();
        if (!pageTokenStr.isEmpty()) {
            try {
                skip = Integer.parseInt(pageTokenStr);
            } catch (NumberFormatException ignored) {
                skip = 0;
            }
        }

        List<String> tags = request.getTagsList();

        List<Attraction> attractions = attractionService.listByCity(city, tags.isEmpty() ? null : tags, pageSize, skip);

        int nextSkip = skip + attractions.size();
        String nextPageToken = attractions.size() < pageSize ? "" : String.valueOf(nextSkip);

        responseObserver.onNext(ListAttractionsByCityResponse.newBuilder()
                .addAllAttractions(attractions)
                .setNextPageToken(nextPageToken)
                .build());
        responseObserver.onCompleted();
    }
}
