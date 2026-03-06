package org.tripsphere.poi.api.grpc;

import io.grpc.stub.StreamObserver;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.poi.exception.InvalidArgumentException;
import org.tripsphere.poi.exception.NotFoundException;
import org.tripsphere.poi.exception.PermissionDeniedException;
import org.tripsphere.poi.exception.UnauthenticatedException;
import org.tripsphere.poi.security.GrpcAuthContext;
import org.tripsphere.poi.service.PoiService;
import org.tripsphere.poi.v1.BatchCreatePoisRequest;
import org.tripsphere.poi.v1.BatchCreatePoisResponse;
import org.tripsphere.poi.v1.BatchGetPoisRequest;
import org.tripsphere.poi.v1.BatchGetPoisResponse;
import org.tripsphere.poi.v1.CreatePoiRequest;
import org.tripsphere.poi.v1.CreatePoiResponse;
import org.tripsphere.poi.v1.GetPoiByIdRequest;
import org.tripsphere.poi.v1.GetPoiByIdResponse;
import org.tripsphere.poi.v1.GetPoisInBoundsRequest;
import org.tripsphere.poi.v1.GetPoisInBoundsResponse;
import org.tripsphere.poi.v1.GetPoisNearbyRequest;
import org.tripsphere.poi.v1.GetPoisNearbyResponse;
import org.tripsphere.poi.v1.Poi;
import org.tripsphere.poi.v1.PoiServiceGrpc;

@GrpcService
@RequiredArgsConstructor
public class PoiGrpcService extends PoiServiceGrpc.PoiServiceImplBase {

    private final PoiService poiService;

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 200;

    @Override
    public void getPoiById(
            GetPoiByIdRequest request, StreamObserver<GetPoiByIdResponse> responseObserver) {
        String id = request.getId();
        if (id.isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        Poi poi = poiService.findById(id).orElseThrow(() -> new NotFoundException("POI", id));

        responseObserver.onNext(GetPoiByIdResponse.newBuilder().setPoi(poi).build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchGetPois(
            BatchGetPoisRequest request, StreamObserver<BatchGetPoisResponse> responseObserver) {
        List<String> ids = request.getIdsList();
        if (ids.isEmpty()) {
            responseObserver.onNext(BatchGetPoisResponse.newBuilder().build());
            responseObserver.onCompleted();
            return;
        }

        List<Poi> pois = poiService.findAllByIds(ids);

        Map<String, Poi> poisById =
                pois.stream().collect(Collectors.toMap(Poi::getId, Function.identity()));

        List<String> missingIds = ids.stream().filter(id -> !poisById.containsKey(id)).toList();
        if (!missingIds.isEmpty()) {
            throw new NotFoundException("POIs with IDs " + missingIds + " not found");
        }

        List<Poi> orderedPois = ids.stream().map(poisById::get).toList();

        responseObserver.onNext(BatchGetPoisResponse.newBuilder().addAllPois(orderedPois).build());
        responseObserver.onCompleted();
    }

    @Override
    public void getPoisNearby(
            GetPoisNearbyRequest request, StreamObserver<GetPoisNearbyResponse> responseObserver) {
        if (!request.hasLocation()) {
            throw InvalidArgumentException.required("location");
        }

        double radiusMeters = request.getRadiusMeters() > 0 ? request.getRadiusMeters() : 1000;
        int limit = normalizeLimit(request.getLimit());

        List<Poi> pois =
                poiService.searchNearby(
                        request.getLocation(), radiusMeters, limit, request.getFilter());

        responseObserver.onNext(GetPoisNearbyResponse.newBuilder().addAllPois(pois).build());
        responseObserver.onCompleted();
    }

    @Override
    public void getPoisInBounds(
            GetPoisInBoundsRequest request,
            StreamObserver<GetPoisInBoundsResponse> responseObserver) {
        if (!request.hasSouthWest() || !request.hasNorthEast()) {
            throw new InvalidArgumentException("Both southWest and northEast bounds are required");
        }

        int limit = normalizeLimit(request.getLimit());

        List<Poi> pois =
                poiService.searchInBounds(
                        request.getSouthWest(), request.getNorthEast(), limit, request.getFilter());

        responseObserver.onNext(GetPoisInBoundsResponse.newBuilder().addAllPois(pois).build());
        responseObserver.onCompleted();
    }

    @Override
    public void createPoi(
            CreatePoiRequest request, StreamObserver<CreatePoiResponse> responseObserver) {
        // Admin only
        requireAdmin();

        if (!request.hasPoi()) {
            throw InvalidArgumentException.required("poi");
        }

        Poi created = poiService.createPoi(request.getPoi());

        responseObserver.onNext(CreatePoiResponse.newBuilder().setPoi(created).build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchCreatePois(
            BatchCreatePoisRequest request,
            StreamObserver<BatchCreatePoisResponse> responseObserver) {
        // Admin only
        requireAdmin();

        List<CreatePoiRequest> requests = request.getRequestsList();
        if (requests.isEmpty()) {
            throw new InvalidArgumentException("Request list for batch creation is empty");
        }

        // Extract POIs from requests
        List<Poi> poisToCreate =
                requests.stream()
                        .filter(CreatePoiRequest::hasPoi)
                        .map(CreatePoiRequest::getPoi)
                        .toList();

        if (poisToCreate.isEmpty()) {
            throw new InvalidArgumentException("No valid POI data in batch creation request");
        }

        List<Poi> created = poiService.batchCreatePois(poisToCreate);

        responseObserver.onNext(BatchCreatePoisResponse.newBuilder().addAllPois(created).build());
        responseObserver.onCompleted();
    }

    private int normalizeLimit(int limit) {
        if (limit <= 0) {
            return DEFAULT_LIMIT;
        }
        return Math.min(limit, MAX_LIMIT);
    }

    /** Require admin privileges for the current request. */
    private void requireAdmin() {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (!authContext.isAuthenticated()) {
            throw UnauthenticatedException.authenticationRequired();
        }

        if (!authContext.isAdmin()) {
            throw PermissionDeniedException.adminRequired();
        }
    }
}
