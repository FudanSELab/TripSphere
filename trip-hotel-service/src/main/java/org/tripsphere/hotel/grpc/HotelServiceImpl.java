package org.tripsphere.hotel.grpc;

import io.grpc.stub.StreamObserver;

import net.devh.boot.grpc.server.service.GrpcService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.info.BuildProperties;
import org.springframework.data.domain.Page;
import org.springframework.data.mongodb.core.geo.GeoJsonPoint;
import org.tripsphere.hotel.*;
import org.tripsphere.hotel.service.HotelService;
import org.tripsphere.hotel.model.Hotel;
import org.tripsphere.hotel.model.Room;

import java.util.ArrayList;
import java.util.List;

@GrpcService
public class HotelServiceImpl extends HotelServiceGrpc.HotelServiceImplBase {

    @Autowired
    private HotelService hotelService;

    @Override
    public void addHotel(org.tripsphere.hotel.AddHotelRequest request,
                         io.grpc.stub.StreamObserver<org.tripsphere.hotel.AddHotelResponse> responseObserver) {
        Hotel hotel = new Hotel();
        hotel.setName(request.getHotel().getName());
        hotel.setCountry(request.getHotel().getCountry());
        hotel.setProvince(request.getHotel().getProvince());
        hotel.setCity(request.getHotel().getCity());
        hotel.setZone(request.getHotel().getZone());
        hotel.setAddress(request.getHotel().getAddress());
        hotel.setIntroduction(request.getHotel().getIntroduction());
        hotel.setTags(request.getHotel().getTagsList());

        GeoJsonPoint location = new GeoJsonPoint(request.getHotel().getLocation().getLng(), request.getHotel().getLocation().getLat());
        hotel.setLocation(location);

        //get rooms from request
        List<Room> rooms = new ArrayList<>();
        for (int i = 0; i < request.getHotel().getRoomsCount(); i++) {
            Room room = new Room();
            room.setName(request.getHotel().getRooms(i).getName());
            room.setTotal_number(request.getHotel().getRooms(i).getTotalNumber());
            room.setRemaining_number(request.getHotel().getRooms(i).getRemainingNumber());
            room.setBed_width(request.getHotel().getRooms(i).getBedWidth());
            room.setBed_number(request.getHotel().getRooms(i).getBedNumber());
            room.setMin_area(request.getHotel().getRooms(i).getMinArea());
            room.setMax_area(request.getHotel().getRooms(i).getMaxArea());
            room.setPeople_number(request.getHotel().getRooms(i).getPeopleNumber());
            room.setTags(request.getHotel().getRooms(i).getTagsList());
            rooms.add(room);
        }
        hotel.setRooms(rooms);

        String id = hotelService.addHotel(hotel);

        AddHotelResponse response = AddHotelResponse.newBuilder().setId(id).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void deleteHotel(org.tripsphere.hotel.DeleteHotelRequest request,
                            io.grpc.stub.StreamObserver<org.tripsphere.hotel.DeleteHotelResponse> responseObserver) {
        String id = request.getId();
        boolean success = hotelService.deleteHotel(id);
        DeleteHotelResponse response = DeleteHotelResponse.newBuilder().setSuccess(success).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void changeHotel(org.tripsphere.hotel.ChangeHotelRequest request,
                            io.grpc.stub.StreamObserver<org.tripsphere.hotel.ChangeHotelResponse> responseObserver) {

        Hotel hotel = new Hotel();
        hotel.setId(request.getHotel().getId());
        hotel.setName(request.getHotel().getName());
        hotel.setCountry(request.getHotel().getCountry());
        hotel.setProvince(request.getHotel().getProvince());
        hotel.setCity(request.getHotel().getCity());
        hotel.setZone(request.getHotel().getZone());
        hotel.setAddress(request.getHotel().getAddress());
        hotel.setIntroduction(request.getHotel().getIntroduction());
        hotel.setTags(request.getHotel().getTagsList());

        GeoJsonPoint location = new GeoJsonPoint(request.getHotel().getLocation().getLng(), request.getHotel().getLocation().getLat());
        hotel.setLocation(location);
        //get rooms from request
        List<Room> rooms = new ArrayList<>();
        for (int i = 0; i < request.getHotel().getRoomsCount(); i++) {
            Room room = new Room();
            room.setName(request.getHotel().getRooms(i).getName());
            room.setTotal_number(request.getHotel().getRooms(i).getTotalNumber());
            room.setRemaining_number(request.getHotel().getRooms(i).getRemainingNumber());
            room.setBed_width(request.getHotel().getRooms(i).getBedWidth());
            room.setBed_number(request.getHotel().getRooms(i).getBedNumber());
            room.setMin_area(request.getHotel().getRooms(i).getMinArea());
            room.setMax_area(request.getHotel().getRooms(i).getMaxArea());
            room.setPeople_number(request.getHotel().getRooms(i).getPeopleNumber());
            room.setTags(request.getHotel().getRooms(i).getTagsList());
            rooms.add(room);
        }
        hotel.setRooms(rooms);

        boolean success = hotelService.changHotel(hotel);

        ChangeHotelResponse response = ChangeHotelResponse.newBuilder().setSuccess(success).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void findHotelWithinRadiusPage(FindHotelWithinRadiusPageRequest request,
                                          StreamObserver<FindHotelWithinRadiusPageResponse> responseObserver) {
        double lng = request.getLocation().getLng();
        double lat = request.getLocation().getLat();
        double radiusKm = request.getRadiusKm();
        int number = request.getNumber();
        int size = request.getSize();
        String name = request.getName();
        List<String> tags = request.getTagsList();

        Page<Hotel> result = hotelService.findHotelsWithinRadius(lng, lat, radiusKm, name, tags, number, size);

        HotelPage hotelPage = buildHotelPage(result);
        FindHotelWithinRadiusPageResponse response = FindHotelWithinRadiusPageResponse.newBuilder()
                .setHotelPage(hotelPage)
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void findHotelsWithinCirclePage(FindHotelsWithinCirclePageRequest request,
                                           StreamObserver<FindHotelsWithinCirclePageResponse> responseObserver) {
        double lng = request.getLocation().getLng();
        double lat = request.getLocation().getLat();
        double radiusKm = request.getRadiusKm();
        int number = request.getNumber();
        int size = request.getSize();
        String name = request.getName();
        List<String> tags = request.getTagsList();

        Page<Hotel> result = hotelService.findHotelsWithinCircle(lng, lat, radiusKm, name, tags, number, size);

        HotelPage hotelPage = buildHotelPage(result);
        FindHotelsWithinCirclePageResponse response = FindHotelsWithinCirclePageResponse.newBuilder()
                .setHotelPage(hotelPage)
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void findHotelWithinRadius(FindHotelWithinRadiusRequest request,
                                      StreamObserver<FindHotelWithinRadiusResponse> responseObserver) {
        double lng = request.getLocation().getLng();
        double lat = request.getLocation().getLat();
        double radiusKm = request.getRadiusKm();
        String name = request.getName();
        List<String> tags = request.getTagsList();

        List<Hotel> hotels = hotelService.findHotelsWithinRadius(lng, lat, radiusKm, name, tags);

        List<org.tripsphere.hotel.Hotel> hotelProtos = buildHotelList(hotels);
        FindHotelWithinRadiusResponse response = FindHotelWithinRadiusResponse.newBuilder()
                .addAllContent(hotelProtos)
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void findHotelsWithinCircle(FindHotelsWithinCircleRequest request,
                                       StreamObserver<FindHotelsWithinCircleResponse> responseObserver) {
        double lng = request.getLocation().getLng();
        double lat = request.getLocation().getLat();
        double radiusKm = request.getRadiusKm();
        String name = request.getName();
        List<String> tags = request.getTagsList();

        List<Hotel> hotels = hotelService.findHotelsWithinCircle(lng, lat, radiusKm, name, tags);

        List<org.tripsphere.hotel.Hotel> hotelProtos = buildHotelList(hotels);
        FindHotelsWithinCircleResponse response = FindHotelsWithinCircleResponse.newBuilder()
                .addAllContent(hotelProtos)
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void findHotelById(org.tripsphere.hotel.FindHotelByIdRequest request,
                              io.grpc.stub.StreamObserver<org.tripsphere.hotel.FindHotelByIdResponse> responseObserver) {
        Hotel hotel = hotelService.findHotelById(request.getId());
        org.tripsphere.hotel.Hotel.Builder hotelBuilder = org.tripsphere.hotel.Hotel.newBuilder()
                .setId(hotel.getId() == null ? "" : hotel.getId())
                .setName(hotel.getName() == null ? "" : hotel.getName())
                .setCountry(hotel.getCountry() == null ? "" : hotel.getCountry())
                .setProvince(hotel.getProvince() == null ? "" : hotel.getProvince())
                .setCity(hotel.getCity() == null ? "" : hotel.getCity())
                .setZone(hotel.getZone() == null ? "" : hotel.getZone())
                .setAddress(hotel.getAddress() == null ? "" : hotel.getAddress())
                .setIntroduction(hotel.getIntroduction() == null ? "" : hotel.getIntroduction());

        if (hotel.getTags() != null)
            hotelBuilder.addAllTags(hotel.getTags());

        if (hotel.getLocation() != null) {
            org.tripsphere.hotel.Location locationProto = org.tripsphere.hotel.Location.newBuilder()
                    .setLng(hotel.getLocation().getX())
                    .setLat(hotel.getLocation().getY())
                    .build();
            hotelBuilder.setLocation(locationProto);
        }

        if (hotel.getRooms() != null) {
            for (Room room : hotel.getRooms()) {
                org.tripsphere.hotel.Room.Builder roomBuilder = org.tripsphere.hotel.Room.newBuilder()
                        .setName(room.getName() == null ? "" : room.getName())
                        .setTotalNumber(room.getTotal_number())
                        .setRemainingNumber(room.getRemaining_number())
                        .setBedWidth(room.getBed_width())
                        .setBedNumber(room.getBed_number())
                        .setMinArea(room.getMin_area())
                        .setMaxArea(room.getMax_area())
                        .setPeopleNumber(room.getPeople_number());

                if (room.getTags() != null)
                    roomBuilder.addAllTags(room.getTags());
            }
        }
        FindHotelByIdResponse response = FindHotelByIdResponse.newBuilder().setHotel(hotelBuilder.build()).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();

    }
    /***********************************************************************************************/
    /**
     * 将分页结果 Page<Hotel> 转换为 proto 的 HotelPage
     */
    private HotelPage buildHotelPage(Page<Hotel> result) {
        List<org.tripsphere.hotel.Hotel> hotelProtos = buildHotelList(result.getContent());

        return HotelPage.newBuilder()
                .addAllContent(hotelProtos)
                .setTotalPages(result.getTotalPages())
                .setTotalElements(result.getTotalElements())
                .setSize(result.getSize())
                .setNumber(result.getNumber())
                .setFirst(result.isFirst())
                .setLast(result.isLast())
                .setNumberOfElements(result.getNumberOfElements())
                .build();
    }

    /**
     * 将 List<Hotel> 转换为 List<proto Hotel>
     */
    private List<org.tripsphere.hotel.Hotel> buildHotelList(List<Hotel> hotels) {
        List<org.tripsphere.hotel.Hotel> hotelProtos = new ArrayList<>();

        for (Hotel hotel : hotels) {
            org.tripsphere.hotel.Hotel.Builder hotelBuilder = org.tripsphere.hotel.Hotel.newBuilder()
                    .setId(hotel.getId() == null ? "" : hotel.getId())
                    .setName(hotel.getName() == null ? "" : hotel.getName())
                    .setCountry(hotel.getCountry() == null ? "" : hotel.getCountry())
                    .setProvince(hotel.getProvince() == null ? "" : hotel.getProvince())
                    .setCity(hotel.getCity() == null ? "" : hotel.getCity())
                    .setZone(hotel.getZone() == null ? "" : hotel.getZone())
                    .setAddress(hotel.getAddress() == null ? "" : hotel.getAddress())
                    .setIntroduction(hotel.getIntroduction() == null ? "" : hotel.getIntroduction());

            if (hotel.getTags() != null)
                hotelBuilder.addAllTags(hotel.getTags());

            if (hotel.getLocation() != null) {
                org.tripsphere.hotel.Location locationProto = org.tripsphere.hotel.Location.newBuilder()
                        .setLng(hotel.getLocation().getX())
                        .setLat(hotel.getLocation().getY())
                        .build();
                hotelBuilder.setLocation(locationProto);
            }

            if (hotel.getRooms() != null) {
                for (Room room : hotel.getRooms()) {
                    org.tripsphere.hotel.Room.Builder roomBuilder = org.tripsphere.hotel.Room.newBuilder()
                            .setName(room.getName() == null ? "" : room.getName())
                            .setTotalNumber(room.getTotal_number())
                            .setRemainingNumber(room.getRemaining_number())
                            .setBedWidth(room.getBed_width())
                            .setBedNumber(room.getBed_number())
                            .setMinArea(room.getMin_area())
                            .setMaxArea(room.getMax_area())
                            .setPeopleNumber(room.getPeople_number());

                    if (room.getTags() != null)
                        roomBuilder.addAllTags(room.getTags());

                    hotelBuilder.addRooms(roomBuilder.build());
                }
            }

            hotelProtos.add(hotelBuilder.build());
        }
        return hotelProtos;
    }

}
