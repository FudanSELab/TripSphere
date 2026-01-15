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

    @Override
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
        attraction.setName(request.getAttraction().getName());

        GeoJsonPoint location = new GeoJsonPoint(request.getAttraction().getLocation().getLng(), request.getAttraction().getLocation().getLat());
        attraction.setLocation(location);

        List<File> images = new ArrayList<>();
        for (int i=0;i<request.getAttraction().getImagesCount();i++){
            File file = new File();
            file.setName(request.getAttraction().getImages(i).getName());
            file.setContentType(request.getAttraction().getImages(i).getContentType());
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

    @Override
    public void deleteAttraction(org.tripsphere.attraction.DeleteAttractionRequest request,
                                  io.grpc.stub.StreamObserver<org.tripsphere.attraction.DeleteAttractionResponse> responseObserver) {
        String attractionId = request.getId();
        boolean success = attractionService.deleteAttraction(attractionId);
        DeleteAttractionResponse response = DeleteAttractionResponse.newBuilder().setSuccess(success).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
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
            image.setContentType(request.getAttraction().getImages(i).getContentType());
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

    @Override
    public void findIdByName(org.tripsphere.attraction.FindIdByNameRequest request,
                             io.grpc.stub.StreamObserver<org.tripsphere.attraction.FindIdByNameResponse> responseObserver) {
        String name = request.getName();
        String attraction_id = attractionService.findAttractionIdByName(name);
        FindIdByNameResponse response = FindIdByNameResponse.newBuilder().setAttractionId(attraction_id).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void findAttractionById(org.tripsphere.attraction.FindAttractionByIdRequest request,
                                   io.grpc.stub.StreamObserver<org.tripsphere.attraction.FindAttractionByIdResponse> responseObserver) {
        Attraction attraction = attractionService.findAttractionById(request.getId());
        org.tripsphere.attraction.Attraction.Builder attractionBuilder= org.tripsphere.attraction.Attraction.newBuilder()
                .setId(attraction.getId() == null ? "": attraction.getId())
                .setName(attraction.getName() == null ? "": attraction.getName())
                .setIntroduction(attraction.getIntroduction() == null ? "": attraction.getIntroduction());

        if (attraction.getTags()!=null)
            attractionBuilder.addAllTags(attraction.getTags());

        if(attraction.getLocation() !=null){
            org.tripsphere.attraction.Location locationProto = org.tripsphere.attraction.Location.newBuilder()
                    .setLng(attraction.getLocation().getX())
                    .setLat(attraction.getLocation().getY())
                    .build();
            attractionBuilder.setLocation(locationProto);
        }

        if (attraction.getAddress() != null){
            org.tripsphere.attraction.Address.Builder addressBuilder = org.tripsphere.attraction.Address.newBuilder()
                    .setCountry(attraction.getAddress().getCountry() == null ? "" : attraction.getAddress().getCountry())
                    .setProvince(attraction.getAddress().getProvince() == null ? "" : attraction.getAddress().getProvince())
                    .setCity(attraction.getAddress().getCity() == null ? "" : attraction.getAddress().getCity())
                    .setCounty(attraction.getAddress().getCounty() == null ? "" : attraction.getAddress().getCounty())
                    .setDistrict(attraction.getAddress().getDistrict() == null ? "" : attraction.getAddress().getDistrict())
                    .setStreet(attraction.getAddress().getStreet() == null ? "" : attraction.getAddress().getStreet());
            attractionBuilder.setAddress(addressBuilder.build());
        }

        FindAttractionByIdResponse response = FindAttractionByIdResponse.newBuilder().setAttraction(attractionBuilder.build()).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void findAttractionsWithinRadiusPage(org.tripsphere.attraction.FindAttractionsWithinRadiusPageRequest request,
                                               io.grpc.stub.StreamObserver<org.tripsphere.attraction.FindAttractionsWithinRadiusPageResponse> responseObserver) {
        double lng = request.getLocation().getLng();
        double lat = request.getLocation().getLat();
        double radiusKm = request.getRadiusKm();
        int number = request.getNumber();
        int size = request.getSize();
        String name = request.getName();
        List<String> tags = request.getTagsList();

        Page<Attraction> result = attractionService.findAttractionsWithinRadius(lng, lat, radiusKm, name, tags, number, size);

        AttractionPage attractionPage = buildAttractionPage(result);
        FindAttractionsWithinRadiusPageResponse response = FindAttractionsWithinRadiusPageResponse.newBuilder()
                .setAttractionPage(attractionPage)
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void findAttractionsWithinCirclePage(FindAttractionsWithinCirclePageRequest request,
                                           StreamObserver<FindAttractionsWithinCirclePageResponse> responseObserver) {
        double lng = request.getLocation().getLng();
        double lat = request.getLocation().getLat();
        double radiusKm = request.getRadiusKm();
        int number = request.getNumber();
        int size = request.getSize();
        String name = request.getName();
        List<String> tags = request.getTagsList();

        Page<Attraction> result = attractionService.findAttractionsWithinCircle(lng, lat, radiusKm, name, tags, number, size);

        AttractionPage attractionPage = buildAttractionPage(result);
        FindAttractionsWithinCirclePageResponse response = FindAttractionsWithinCirclePageResponse.newBuilder()
                .setAttractionPage(attractionPage)
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void findAttractionsWithinRadius(FindAttractionsWithinRadiusRequest request,
                                      StreamObserver<FindAttractionsWithinRadiusResponse> responseObserver) {
        double lng = request.getLocation().getLng();
        double lat = request.getLocation().getLat();
        double radiusKm = request.getRadiusKm();
        String name = request.getName();
        List<String> tags = request.getTagsList();

        List<Attraction> attractions = attractionService.findAttractionsWithinRadius(lng, lat, radiusKm, name, tags);

        List<org.tripsphere.attraction.Attraction> attractionProtos = buildAttractionList(attractions);
        FindAttractionsWithinRadiusResponse response = FindAttractionsWithinRadiusResponse.newBuilder()
                .addAllContent(attractionProtos)
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    @Override
    public void findAttractionsWithinCircle(FindAttractionsWithinCircleRequest request,
                                       StreamObserver<FindAttractionsWithinCircleResponse> responseObserver) {
        double lng = request.getLocation().getLng();
        double lat = request.getLocation().getLat();
        double radiusKm = request.getRadiusKm();
        String name = request.getName();
        List<String> tags = request.getTagsList();

        List<Attraction> attractions = attractionService.findAttractionsWithinCircle(lng, lat, radiusKm, name, tags);

        List<org.tripsphere.attraction.Attraction> attractionProtos = buildAttractionList(attractions);
        FindAttractionsWithinCircleResponse response = FindAttractionsWithinCircleResponse.newBuilder()
                .addAllContent(attractionProtos)
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    /***********************************************************************************************/
    /**
     * Page<Attraction> ->proto AttractionPage
     */
    private AttractionPage buildAttractionPage(Page<Attraction> result) {
        List<org.tripsphere.attraction.Attraction> attractionProtos = buildAttractionList(result.getContent());

        return AttractionPage.newBuilder()
                .addAllContent(attractionProtos)
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
     * List<Hotel> -> List<proto Hotel>
     */
    private List<org.tripsphere.attraction.Attraction> buildAttractionList(List<Attraction> attractions) {
        List<org.tripsphere.attraction.Attraction> attractionProtos = new ArrayList<>();

        for (Attraction attraction : attractions) {
            org.tripsphere.attraction.Attraction.Builder attractionBuilder = org.tripsphere.attraction.Attraction.newBuilder()
                    .setId(attraction.getId() == null ? "" : attraction.getId())
                    .setName(attraction.getName() == null ? "" : attraction.getName())
                    .setIntroduction(attraction.getIntroduction() == null ? "" : attraction.getIntroduction());

            if (attraction.getTags() != null)
                attractionBuilder.addAllTags(attraction.getTags());

            if (attraction.getLocation() != null) {
                org.tripsphere.attraction.Location locationProto = org.tripsphere.attraction.Location.newBuilder()
                        .setLng(attraction.getLocation().getX())
                        .setLat(attraction.getLocation().getY())
                        .build();
                attractionBuilder.setLocation(locationProto);
            }

            if (attraction.getAddress() != null){
                org.tripsphere.attraction.Address.Builder addressBuilder = org.tripsphere.attraction.Address.newBuilder()
                        .setCountry(attraction.getAddress().getCountry() == null ? "" : attraction.getAddress().getCountry())
                        .setProvince(attraction.getAddress().getProvince() == null ? "" : attraction.getAddress().getProvince())
                        .setCity(attraction.getAddress().getCity() == null ? "" : attraction.getAddress().getCity())
                        .setCounty(attraction.getAddress().getCounty() == null ? "" : attraction.getAddress().getCounty())
                        .setDistrict(attraction.getAddress().getDistrict() == null ? "" : attraction.getAddress().getDistrict())
                        .setStreet(attraction.getAddress().getStreet() == null ? "" : attraction.getAddress().getStreet());
                attractionBuilder.setAddress(addressBuilder.build());
            }
            attractionProtos.add(attractionBuilder.build());
        }
        return attractionProtos;
    }
}

