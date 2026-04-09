package org.tripsphere.hotel.infrastructure.adapter.inbound.grpc;

import io.grpc.stub.StreamObserver;
import java.util.List;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.hotel.application.exception.InvalidArgumentException;
import org.tripsphere.hotel.application.service.query.BatchGetHotelsUseCase;
import org.tripsphere.hotel.application.service.query.GetHotelByIdUseCase;
import org.tripsphere.hotel.application.service.query.GetHotelsNearbyUseCase;
import org.tripsphere.hotel.application.service.query.GetRoomTypesByHotelIdUseCase;
import org.tripsphere.hotel.application.service.query.ListHotelsUseCase;
import org.tripsphere.hotel.domain.model.GeoLocation;
import org.tripsphere.hotel.domain.model.Hotel;
import org.tripsphere.hotel.domain.model.RoomType;
import org.tripsphere.hotel.infrastructure.adapter.inbound.grpc.mapper.HotelProtoMapper;
import org.tripsphere.hotel.infrastructure.adapter.inbound.grpc.mapper.RoomTypeProtoMapper;
import org.tripsphere.hotel.infrastructure.util.CoordinateTransformUtil;
import org.tripsphere.hotel.v1.BatchGetHotelsRequest;
import org.tripsphere.hotel.v1.BatchGetHotelsResponse;
import org.tripsphere.hotel.v1.GetHotelByIdRequest;
import org.tripsphere.hotel.v1.GetHotelByIdResponse;
import org.tripsphere.hotel.v1.GetHotelsNearbyRequest;
import org.tripsphere.hotel.v1.GetHotelsNearbyResponse;
import org.tripsphere.hotel.v1.GetRoomTypesByHotelIdRequest;
import org.tripsphere.hotel.v1.GetRoomTypesByHotelIdResponse;
import org.tripsphere.hotel.v1.HotelServiceGrpc;
import org.tripsphere.hotel.v1.ListHotelsRequest;
import org.tripsphere.hotel.v1.ListHotelsResponse;

@GrpcService
@RequiredArgsConstructor
public class HotelGrpcService extends HotelServiceGrpc.HotelServiceImplBase {

    private static final double DEFAULT_RADIUS_METERS = 1000;

    private final GetHotelByIdUseCase getHotelByIdUseCase;
    private final BatchGetHotelsUseCase batchGetHotelsUseCase;
    private final GetHotelsNearbyUseCase getHotelsNearbyUseCase;
    private final ListHotelsUseCase listHotelsUseCase;
    private final GetRoomTypesByHotelIdUseCase getRoomTypesByHotelIdUseCase;
    private final HotelProtoMapper hotelProtoMapper;
    private final RoomTypeProtoMapper roomTypeProtoMapper;

    @Override
    public void getHotelById(GetHotelByIdRequest request, StreamObserver<GetHotelByIdResponse> responseObserver) {
        String id = request.getId();
        if (id.isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        Hotel hotel = getHotelByIdUseCase.execute(id);

        responseObserver.onNext(GetHotelByIdResponse.newBuilder()
                .setHotel(hotelProtoMapper.toProto(hotel))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchGetHotels(BatchGetHotelsRequest request, StreamObserver<BatchGetHotelsResponse> responseObserver) {
        List<String> ids = request.getIdsList();
        if (ids.isEmpty()) {
            responseObserver.onNext(BatchGetHotelsResponse.newBuilder().build());
            responseObserver.onCompleted();
            return;
        }

        List<Hotel> hotels = batchGetHotelsUseCase.execute(ids);

        responseObserver.onNext(BatchGetHotelsResponse.newBuilder()
                .addAllHotels(hotelProtoMapper.toProtoList(hotels))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void getHotelsNearby(
            GetHotelsNearbyRequest request, StreamObserver<GetHotelsNearbyResponse> responseObserver) {
        if (!request.hasLocation()) {
            throw InvalidArgumentException.required("location");
        }

        double radiusMeters = request.getRadiusMeters() > 0 ? request.getRadiusMeters() : DEFAULT_RADIUS_METERS;

        double[] wgs84 = CoordinateTransformUtil.gcj02ToWgs84(
                request.getLocation().getLongitude(), request.getLocation().getLatitude());
        GeoLocation location = new GeoLocation(wgs84[0], wgs84[1]);

        List<Hotel> hotels = getHotelsNearbyUseCase.execute(location, radiusMeters);

        responseObserver.onNext(GetHotelsNearbyResponse.newBuilder()
                .addAllHotels(hotelProtoMapper.toProtoList(hotels))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void listHotels(ListHotelsRequest request, StreamObserver<ListHotelsResponse> responseObserver) {
        ListHotelsUseCase.HotelPage page = listHotelsUseCase.execute(
                request.getProvince(), request.getCity(), request.getPageSize(), request.getPageToken());

        ListHotelsResponse.Builder builder =
                ListHotelsResponse.newBuilder().addAllHotels(hotelProtoMapper.toProtoList(page.hotels()));

        if (page.nextPageToken() != null) {
            builder.setNextPageToken(page.nextPageToken());
        }

        responseObserver.onNext(builder.build());
        responseObserver.onCompleted();
    }

    @Override
    public void getRoomTypesByHotelId(
            GetRoomTypesByHotelIdRequest request, StreamObserver<GetRoomTypesByHotelIdResponse> responseObserver) {
        String hotelId = request.getHotelId();
        if (hotelId.isEmpty()) {
            throw InvalidArgumentException.required("hotel_id");
        }

        List<RoomType> roomTypes = getRoomTypesByHotelIdUseCase.execute(hotelId);

        responseObserver.onNext(GetRoomTypesByHotelIdResponse.newBuilder()
                .addAllRoomTypes(roomTypeProtoMapper.toProtoList(roomTypes))
                .build());
        responseObserver.onCompleted();
    }
}
