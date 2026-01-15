package org.tripsphere.hotel.service;

import java.util.List;

import org.springaicommunity.mcp.annotation.McpTool;
import org.springaicommunity.mcp.annotation.McpToolParam;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.tripsphere.hotel.model.Hotel;
import org.tripsphere.hotel.repository.HotelRepository;

@Component
public class HotelTools {
    @Autowired private HotelRepository hotelRepository;

    /**
     * Find hotels located at the specified location and within the specified distance range, and
     * list them in order from near to far.
     *
     * @param lng Longitude
     * @param lat Latitude
     * @param radiusKm distance to center(km)
     * @return The list of hotels
     */
    @McpTool(
            name = "findHotelsWithinRadius",
            description = "Find all hotels within a radius from a location")
    public List<Hotel> findHotelsWithinRadius(
            @McpToolParam(description = "Longitude", required = true) double lng,
            @McpToolParam(description = "Latitude", required = true) double lat,
            @McpToolParam(description = "Distance to central point, kilometer", required = true)
                    double radiusKm,
            @McpToolParam(
                            description =
                                    "Hotel name, If you want all hotels, just don't input anything",
                            required = true)
                    String name,
            @McpToolParam(
                            description = "Hotel tags, such like ”餐饮“,”茶室“ and ”洗衣服务“",
                            required = true)
                    List<String> tags) {
        double maxDistanceMeters = radiusKm * 1000; // Mongo expects meters for $nearSphere
        String nameRegex = (name == null || name.isBlank()) ? ".*" : ".*" + name + ".*";
        return hotelRepository.findByLocationNearWithFilters(
                lng, lat, maxDistanceMeters, nameRegex, tags);
    }
}
