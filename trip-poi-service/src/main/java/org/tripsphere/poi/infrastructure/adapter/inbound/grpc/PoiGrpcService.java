package org.tripsphere.poi.infrastructure.adapter.inbound.grpc;

import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import io.grpc.stub.StreamObserver;
import java.util.List;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.poi.application.dto.CreatePoiCommand;
import org.tripsphere.poi.application.dto.SearchPoisInBoundsQuery;
import org.tripsphere.poi.application.dto.SearchPoisNearbyQuery;
import org.tripsphere.poi.application.service.command.BatchCreatePoisUseCase;
import org.tripsphere.poi.application.service.command.CreatePoiUseCase;
import org.tripsphere.poi.application.service.query.BatchFindPoisUseCase;
import org.tripsphere.poi.application.service.query.FindPoiByIdUseCase;
import org.tripsphere.poi.application.service.query.SearchPoisInBoundsUseCase;
import org.tripsphere.poi.application.service.query.SearchPoisNearbyUseCase;
import org.tripsphere.poi.domain.model.GeoCoordinate;
import org.tripsphere.poi.domain.model.Poi;
import org.tripsphere.poi.domain.model.PoiAddress;
import org.tripsphere.poi.infrastructure.adapter.inbound.grpc.mapper.PoiProtoMapper;
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
import org.tripsphere.poi.v1.PoiFilter;
import org.tripsphere.poi.v1.PoiServiceGrpc;

@GrpcService
@RequiredArgsConstructor
public class PoiGrpcService extends PoiServiceGrpc.PoiServiceImplBase {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 200;

    private final PoiProtoMapper poiProtoMapper;
    private final FindPoiByIdUseCase findPoiByIdUseCase;
    private final BatchFindPoisUseCase batchFindPoisUseCase;
    private final SearchPoisNearbyUseCase searchPoisNearbyUseCase;
    private final SearchPoisInBoundsUseCase searchPoisInBoundsUseCase;
    private final CreatePoiUseCase createPoiUseCase;
    private final BatchCreatePoisUseCase batchCreatePoisUseCase;

    @Override
    public void getPoiById(GetPoiByIdRequest request, StreamObserver<GetPoiByIdResponse> responseObserver) {
        String id = request.getId();
        if (id.isEmpty()) {
            throw invalidArgument("id is required");
        }
        Poi poi = findPoiByIdUseCase.execute(id);
        responseObserver.onNext(GetPoiByIdResponse.newBuilder()
                .setPoi(poiProtoMapper.toProto(poi))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchGetPois(BatchGetPoisRequest request, StreamObserver<BatchGetPoisResponse> responseObserver) {
        List<String> ids = request.getIdsList();
        if (ids.isEmpty()) {
            responseObserver.onNext(BatchGetPoisResponse.newBuilder().build());
            responseObserver.onCompleted();
            return;
        }
        List<Poi> pois = batchFindPoisUseCase.execute(ids);
        responseObserver.onNext(BatchGetPoisResponse.newBuilder()
                .addAllPois(poiProtoMapper.toProtos(pois))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void getPoisNearby(GetPoisNearbyRequest request, StreamObserver<GetPoisNearbyResponse> responseObserver) {
        if (!request.hasLocation()) {
            throw invalidArgument("location is required");
        }
        GeoCoordinate center = poiProtoMapper.fromGeoPoint(request.getLocation());
        double radiusMeters = request.getRadiusMeters() > 0 ? request.getRadiusMeters() : 1000;
        int limit = normalizeLimit(request.getLimit());
        List<String> categories = null;
        String adcode = null;
        if (request.hasFilter()) {
            PoiFilter filter = request.getFilter();
            if (!filter.getCategoriesList().isEmpty()) {
                categories = filter.getCategoriesList();
            }
            if (!filter.getAdcode().isEmpty()) {
                adcode = filter.getAdcode();
            }
        }
        SearchPoisNearbyQuery query = new SearchPoisNearbyQuery(center, radiusMeters, limit, categories, adcode);
        List<Poi> pois = searchPoisNearbyUseCase.execute(query);
        responseObserver.onNext(GetPoisNearbyResponse.newBuilder()
                .addAllPois(poiProtoMapper.toProtos(pois))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void getPoisInBounds(
            GetPoisInBoundsRequest request, StreamObserver<GetPoisInBoundsResponse> responseObserver) {
        if (!request.hasSouthWest() || !request.hasNorthEast()) {
            throw invalidArgument("Both southWest and northEast bounds are required");
        }
        GeoCoordinate southWest = poiProtoMapper.fromGeoPoint(request.getSouthWest());
        GeoCoordinate northEast = poiProtoMapper.fromGeoPoint(request.getNorthEast());
        int limit = normalizeLimit(request.getLimit());
        List<String> categories = null;
        String adcode = null;
        if (request.hasFilter()) {
            PoiFilter filter = request.getFilter();
            if (!filter.getCategoriesList().isEmpty()) {
                categories = filter.getCategoriesList();
            }
            if (!filter.getAdcode().isEmpty()) {
                adcode = filter.getAdcode();
            }
        }
        SearchPoisInBoundsQuery query = new SearchPoisInBoundsQuery(southWest, northEast, limit, categories, adcode);
        List<Poi> pois = searchPoisInBoundsUseCase.execute(query);
        responseObserver.onNext(GetPoisInBoundsResponse.newBuilder()
                .addAllPois(poiProtoMapper.toProtos(pois))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void createPoi(CreatePoiRequest request, StreamObserver<CreatePoiResponse> responseObserver) {
        if (!request.hasPoi()) {
            throw invalidArgument("poi is required");
        }
        CreatePoiCommand command = toCreatePoiCommand(request.getPoi());
        Poi created = createPoiUseCase.execute(command);
        responseObserver.onNext(CreatePoiResponse.newBuilder()
                .setPoi(poiProtoMapper.toProto(created))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchCreatePois(
            BatchCreatePoisRequest request, StreamObserver<BatchCreatePoisResponse> responseObserver) {
        List<CreatePoiRequest> requests = request.getRequestsList();
        if (requests.isEmpty()) {
            throw invalidArgument("Request list for batch creation is empty");
        }
        List<CreatePoiCommand> commands = requests.stream()
                .filter(CreatePoiRequest::hasPoi)
                .map(r -> toCreatePoiCommand(r.getPoi()))
                .toList();
        if (commands.isEmpty()) {
            throw invalidArgument("No valid POI data in batch creation request");
        }
        List<Poi> created = batchCreatePoisUseCase.execute(commands);
        responseObserver.onNext(BatchCreatePoisResponse.newBuilder()
                .addAllPois(poiProtoMapper.toProtos(created))
                .build());
        responseObserver.onCompleted();
    }

    private CreatePoiCommand toCreatePoiCommand(org.tripsphere.poi.v1.Poi proto) {
        GeoCoordinate location = poiProtoMapper.fromGeoPoint(proto.getLocation());
        PoiAddress address = poiProtoMapper.fromProtoAddress(proto.getAddress());
        return new CreatePoiCommand(
                proto.getName(),
                location,
                address,
                proto.getAdcode(),
                proto.getAmapId(),
                proto.getCategoriesList(),
                proto.getImagesList());
    }

    private int normalizeLimit(int limit) {
        if (limit <= 0) return DEFAULT_LIMIT;
        return Math.min(limit, MAX_LIMIT);
    }

    private static StatusRuntimeException invalidArgument(String message) {
        return Status.INVALID_ARGUMENT.withDescription(message).asRuntimeException();
    }
}
