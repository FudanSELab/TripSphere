package org.tripsphere.attraction.grpc;

import io.grpc.stub.StreamObserver;

import net.devh.boot.grpc.server.service.GrpcService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.mongodb.core.geo.GeoJsonPoint;
import org.tripsphere.attraction.service.AttractionService;
import org.tripsphere.attraction.*;
import org.tripsphere.attraction.model.Attraction;
import org.tripsphere.attraction.model.Address;
import org.tripsphere.attraction.model.File;

import java.util.ArrayList;
import java.util.List;

@GrpcService
public class AttractionServiceImpl extends AttractionServiceGrpc.AttractionServiceImplBase {

    @Autowired
    private AttractionService attractionService;

    public void addAttraction(org.tripsphere.attraction.AddAttractionRequest request,
                               io.grpc.stub.StreamObserver<org.tripsphere.attraction.AddAttractionResponse> responseObserver) {
        Attraction attraction = new Attraction();

        Address address = new Address();
        address.setCountry(request.getAttraction().getAddress().getCountry());
        address.setProvince(request.getAttraction().getAddress().getProvince());
        address.setCity(request.getAttraction().getAddress().getCity());
        address.setCounty(request.getAttraction().getAddress().getCounty());
        address.setDistrict(request.getAttraction().getAddress().getDistrict());
        address.setStreet(request.getAttraction().getAddress().getStreet());
        attraction.setAddress(address);

        attraction.setIntroduction(request.getAttraction().getIntroduction());
        attraction.setTags(request.getAttraction().getTagsList());

        GeoJsonPoint location = new GeoJsonPoint(request.getAttraction().getLocation().getLng(), request.getAttraction().getLocation().getLat());
        attraction.setLocation(location);

        List<File> images = new ArrayList<>();
        for (int i=0;i<request.getAttraction().getImagesCount();i++){
            File file = new File();
            file.setName(request.getAttraction().getImages(i).getName());
            file.setContextType(request.getAttraction().getImages(i).getContextType());
            file.setUrl(request.getAttraction().getImages(i).getUrl());
            file.setBucket(request.getAttraction().getImages(i).getBucket());
            file.setService(request.getAttraction().getImages(i).getService());
            file.setPath(request.getAttraction().getImages(i).getPath());
            images.add(file);
        }
        attraction.setImages(images);

        String id =attractionService.addAttraction(attraction);

        AddAttractionResponse response = AddAttractionResponse.newBuilder().setId(id).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    public void deleteAttraction(org.tripsphere.attraction.DeleteAttractionRequest request,
                                  io.grpc.stub.StreamObserver<org.tripsphere.attraction.DeleteAttractionResponse> responseObserver) {
        String attractionId = request.getId();
        boolean success = attractionService.deleteAttraction(attractionId);
        DeleteAttractionResponse response = DeleteAttractionResponse.newBuilder().setSuccess(success).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    public void changeAttraction(org.tripsphere.attraction.ChangeAttractionRequest request,
                                  io.grpc.stub.StreamObserver<org.tripsphere.attraction.ChangeAttractionResponse> responseObserver) {
        String name = request.getAttraction().getName();

        String country = request.getAttraction().getAddress().getCountry();
        String province = request.getAttraction().getAddress().getProvince();
        String city = request.getAttraction().getAddress().getCity();
        String county = request.getAttraction().getAddress().getCounty();
        String district = request.getAttraction().getAddress().getDistrict();
        String street = request.getAttraction().getAddress().getStreet();
        Address address = new Address();
        address.setCountry(country);
        address.setProvince(province);
        address.setCity(city);
        address.setCounty(county);
        address.setDistrict(district);
        address.setStreet(street);

        String introduction = request.getAttraction().getIntroduction();
        List<String> tags = request.getAttraction().getTagsList();

        List<File> images = new ArrayList<>();
        for(int i=0;i<request.getAttraction().getImagesCount();i++){
            File image = new File();
            image.setName(request.getAttraction().getImages(i).getName());
            image.setContextType(request.getAttraction().getImages(i).getContextType());
            image.setUrl(request.getAttraction().getImages(i).getUrl());
            image.setBucket(request.getAttraction().getImages(i).getBucket());
            image.setService(request.getAttraction().getImages(i).getService());
            image.setPath(request.getAttraction().getImages(i).getPath());

            images.add(image);
        }

        GeoJsonPoint location = new GeoJsonPoint(request.getAttraction().getLocation().getLng(), request.getAttraction().getLocation().getLat());

        Attraction attraction = new Attraction();
        attraction.setId(request.getAttraction().getId());
        attraction.setName(name);
        attraction.setAddress(address);
        attraction.setIntroduction(introduction);
        attraction.setTags(tags);
        attraction.setImages(images);
        attraction.setLocation(location);

        boolean success = attractionService.changAttraction(attraction);
        ChangeAttractionResponse response = ChangeAttractionResponse.newBuilder().setSuccess(success).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    public void findIdByName(org.tripsphere.attraction.FindIdByNameRequest request,
                             io.grpc.stub.StreamObserver<org.tripsphere.attraction.FindIdByNameResponse> responseObserver) {
        String name = request.getName();
        String attraction_id = attractionService.findAttractionIdByName(name);
        FindIdByNameResponse response = FindIdByNameResponse.newBuilder().setAttractionId(attraction_id).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }
}

