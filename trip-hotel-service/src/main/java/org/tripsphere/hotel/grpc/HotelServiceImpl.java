package org.tripsphere.hotel.grpc;

import io.grpc.stub.StreamObserver;

import net.devh.boot.grpc.server.service.GrpcService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.info.BuildProperties;
import org.tripsphere.hotel.AddHotelRequest;
import org.tripsphere.hotel.AddHotelResponse;
import org.tripsphere.hotel.DeleteHotelRequest;
import org.tripsphere.hotel.DeleteHotelResponse;
import org.tripsphere.hotel.ChangeHotelRequest;
import org.tripsphere.hotel.ChangeHotelResponse;
import org.tripsphere.hotel.HotelServiceGrpc;
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

        ChangeHotelResponse response=ChangeHotelResponse.newBuilder().setSuccess(success).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }
}
