package org.tripsphere.hotel.api.grpc;

import io.grpc.stub.StreamObserver;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.hotel.exception.InvalidArgumentException;
import org.tripsphere.hotel.exception.NotFoundException;
import org.tripsphere.hotel.service.HotelService;
import org.tripsphere.hotel.v1.*;

@GrpcService
@RequiredArgsConstructor
public class HotelGrpcService extends HotelServiceGrpc.HotelServiceImplBase {

    private final HotelService hotelService;

    private static final double DEFAULT_RADIUS_METERS = 1000;

    @Override
    public void getHotelById(GetHotelByIdRequest request, StreamObserver<GetHotelByIdResponse> responseObserver) {
        String id = request.getId();
        if (id.isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        Hotel hotel = hotelService.findById(id).orElseThrow(() -> new NotFoundException("Hotel", id));

        responseObserver.onNext(
                GetHotelByIdResponse.newBuilder().setHotel(hotel).build());
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

        List<Hotel> hotels = hotelService.findAllByIds(ids);

        Map<String, Hotel> hotelsById = hotels.stream().collect(Collectors.toMap(Hotel::getId, Function.identity()));

        List<String> missingIds =
                ids.stream().filter(id -> !hotelsById.containsKey(id)).toList();
        if (!missingIds.isEmpty()) {
            throw new NotFoundException("Hotels with IDs " + missingIds + " not found");
        }

        List<Hotel> orderedHotels = ids.stream().map(hotelsById::get).toList();

        responseObserver.onNext(
                BatchGetHotelsResponse.newBuilder().addAllHotels(orderedHotels).build());
        responseObserver.onCompleted();
    }

    @Override
    public void getHotelsNearby(
            GetHotelsNearbyRequest request, StreamObserver<GetHotelsNearbyResponse> responseObserver) {
        if (!request.hasLocation()) {
            throw InvalidArgumentException.required("location");
        }

        double radiusMeters = request.getRadiusMeters() > 0 ? request.getRadiusMeters() : DEFAULT_RADIUS_METERS;

        List<Hotel> hotels = hotelService.searchNearby(request.getLocation(), radiusMeters);

        responseObserver.onNext(
                GetHotelsNearbyResponse.newBuilder().addAllHotels(hotels).build());
        responseObserver.onCompleted();
    }

    @Override
    public void listHotels(ListHotelsRequest request, StreamObserver<ListHotelsResponse> responseObserver) {
        HotelService.HotelPage page = hotelService.listHotels(
                request.getProvince(), request.getCity(), request.getPageSize(), request.getPageToken());

        ListHotelsResponse.Builder responseBuilder =
                ListHotelsResponse.newBuilder().addAllHotels(page.hotels());

        if (page.nextPageToken() != null) {
            responseBuilder.setNextPageToken(page.nextPageToken());
        }

        responseObserver.onNext(responseBuilder.build());
        responseObserver.onCompleted();
    }

    @Override
    public void getRoomTypesByHotelId(
            GetRoomTypesByHotelIdRequest request, StreamObserver<GetRoomTypesByHotelIdResponse> responseObserver) {
        String hotelId = request.getHotelId();
        if (hotelId.isEmpty()) {
            throw InvalidArgumentException.required("hotel_id");
        }

        // Verify hotel exists
        hotelService.findById(hotelId).orElseThrow(() -> new NotFoundException("Hotel", hotelId));

        List<RoomType> roomTypes = hotelService.findRoomTypesByHotelId(hotelId);

        responseObserver.onNext(GetRoomTypesByHotelIdResponse.newBuilder()
                .addAllRoomTypes(roomTypes)
                .build());
        responseObserver.onCompleted();
    }
}
