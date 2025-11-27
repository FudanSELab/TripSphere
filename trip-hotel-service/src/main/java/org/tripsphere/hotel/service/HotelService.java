package org.tripsphere.hotel.service;

import org.springaicommunity.mcp.annotation.McpTool;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Example;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.geo.Metrics;
import org.springframework.stereotype.Service;
import org.tripsphere.hotel.model.Hotel;
import org.tripsphere.hotel.repository.HotelRepository;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;
import java.util.logging.Logger;

import org.springframework.data.geo.Distance;
import org.springframework.data.geo.Point;
import org.springframework.data.geo.Circle;

@Service
public class HotelService {
    private static final Logger logger = Logger.getLogger(HotelService.class.getName());
    private static final DateTimeFormatter DATE_TIME_FORMATTER =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final DateTimeFormatter DATE_FORMATTER =
            DateTimeFormatter.ofPattern("yyyy-MM-dd");
    @Autowired
    private HotelRepository hotelRepository;

    public int isExist(String id) {
        Hotel checkHotel = new Hotel();
        checkHotel.setId(id);
        Example<Hotel> projectExample = Example.of(checkHotel);
        long count = hotelRepository.count(projectExample);

        int result = 0;
        if ((int) count != 0) {
            result = 1;
        }
        return result;
    }

    public String addHotel(Hotel hotel) {
        hotelRepository.save(hotel);
        return hotel.getId();
    }

    public boolean deleteHotel(String id) {
        Optional<Hotel> hotelOptional = hotelRepository.findById(id);
        if (hotelOptional.isPresent()) {
            Hotel hotel = hotelOptional.get();
            hotelRepository.delete(hotel);
        } else
            return false;
        return true;
    }

    public boolean changHotel(Hotel hotel) {
        Optional<Hotel> hotelOptionalOld = hotelRepository.findById(hotel.getId());
        if (!hotelOptionalOld.isPresent()) return false;
        Hotel hotelOld = hotelOptionalOld.get();
        hotelOld.setName(hotel.getName());
        hotelOld.setAddress(hotel.getAddress());
        hotelOld.setIntroduction(hotel.getIntroduction());
        hotelOld.setTags(hotel.getTags());
        hotelOld.setRooms(hotel.getRooms());
        hotelOld.setLocation(hotel.getLocation());
        hotelRepository.save(hotelOld);
        return true;
    }

    public Hotel findHotelById(String id) {
        Optional<Hotel> hotelOptional = hotelRepository.findById(id);
        if (hotelOptional.isPresent()) {
            Hotel hotel = hotelOptional.get();
            return hotel;
        } else
            return null;
    }

    /**
     * Find hotels located at the specified location and within the specified distance range,
     * and list them in order from near to far.
     *
     * @param lng      Longitude
     * @param lat      Latitude
     * @param radiusKm distance to center(km)
     * @return The list of hotels
     */
    public List<Hotel> findHotelsWithinRadius(double lng, double lat, double radiusKm, String name, List<String> tags) {
        double maxDistanceMeters = radiusKm * 1000; // Mongo expects meters for $nearSphere
        String nameRegex = (name == null || name.isBlank()) ? ".*" : ".*" + name + ".*";
        return hotelRepository.findByLocationNearWithFilters(lng, lat, maxDistanceMeters, nameRegex, tags);
    }

    /**
     * Find hotels located at the specified location and within the specified distance range
     *
     * @param lng      Longitude
     * @param lat      Latitude
     * @param radiusKm distance to center(km)
     * @return The list of hotels
     */
    @McpTool(name = "add", description = "Add two numbers together")
    public List<Hotel> findHotelsWithinCircle(double lng, double lat, double radiusKm, String name, List<String> tags) {
        double radiusInRadians = radiusKm / 6378.1; // convert km -> radians for $centerSphere
        String nameRegex = (name == null || name.isBlank()) ? ".*" : ".*" + name + ".*";
        return hotelRepository.findByLocationWithinWithFilters(lng, lat, radiusInRadians, nameRegex, tags);
    }


    /**
     * Find hotels located at the specified location and within the specified distance range,
     * and list them in order from near to far, and result has been paginated
     *
     * @param lng      Longitude
     * @param lat      Latitude
     * @param radiusKm distance to center(km)
     * @param page     which page you want to find, start from 0
     * @param size     page size
     * @return The page of hotels
     */
    public Page<Hotel> findHotelsWithinRadius(double lng, double lat, double radiusKm, String name, List<String> tags, int page, int size) {
        double maxDistanceMeters = radiusKm * 1000;
        String nameRegex = (name == null || name.isBlank()) ? ".*" : ".*" + name + ".*";
        Pageable pageable = PageRequest.of(page, size);
        return hotelRepository.findByLocationNearWithFilters(lng, lat, maxDistanceMeters, nameRegex, tags, pageable);
    }

    /**
     * Find hotels located at the specified location and within the specified distance range,
     * and result has been paginated
     *
     * @param lng      Longitude
     * @param lat      Latitude
     * @param radiusKm distance to center(km)
     * @param page     which page you want to find, start from 0
     * @param size     page size
     * @return The page of hotels
     */
    public Page<Hotel> findHotelsWithinCircle(double lng, double lat, double radiusKm, String name, List<String> tags, int page, int size) {
        double radiusInRadians = radiusKm / 6378.1;
        String nameRegex = (name == null || name.isBlank()) ? ".*" : ".*" + name + ".*";
        Pageable pageable = PageRequest.of(page, size);
        return hotelRepository.findByLocationWithinWithFilters(lng, lat, radiusInRadians, nameRegex, tags, pageable);
    }
}
