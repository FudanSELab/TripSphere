package org.tripsphere.attraction.service;

import java.util.List;
import java.util.Optional;
import java.util.logging.Logger;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Example;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.tripsphere.attraction.model.Attraction;
import org.tripsphere.attraction.repository.AttractionRepository;

@Service
public class AttractionService {
    private static final Logger logger = Logger.getLogger(Attraction.class.getName());
    @Autowired private AttractionRepository attractionRepository;

    /**
     * Add attraction
     *
     * @param attraction attraction
     * @return the attraction id
     */
    public String addAttraction(Attraction attraction) {
        attractionRepository.save(attraction);
        return attraction.getId();
    }

    /**
     * Delete attraction
     *
     * @param id attraction id
     * @return if delete success, return true, else return false
     */
    public boolean deleteAttraction(String id) {
        Optional<Attraction> attractionOptional = attractionRepository.findById(id);
        if (attractionOptional.isPresent()) {
            Attraction attraction = attractionOptional.get();
            attractionRepository.delete(attraction);
        } else return false;
        return true;
    }

    /**
     * Change attraction information
     *
     * @param attraction attraction
     * @return if change success, return true, else return false
     */
    public boolean changAttraction(Attraction attraction) {
        Optional<Attraction> attractionOptional = attractionRepository.findById(attraction.getId());
        if (!attractionOptional.isPresent()) return false;
        Attraction attractionOld = attractionOptional.get();
        attractionOld.setName(attraction.getName());
        attractionOld.setAddress(attraction.getAddress());
        attractionOld.setIntroduction(attraction.getIntroduction());
        attractionOld.setLocation(attraction.getLocation());
        attractionOld.setTags(attraction.getTags());
        attractionOld.setImages(attraction.getImages());
        attractionRepository.save(attractionOld);
        return true;
    }

    /**
     * find attraction by id
     *
     * @param id attraction id
     * @return if found, return attraction, else return null
     */
    public Attraction findAttractionById(String id) {
        Optional<Attraction> attractionOptional = attractionRepository.findById(id);
        if (attractionOptional.isPresent()) {
            Attraction attraction = attractionOptional.get();
            return attraction;
        } else return null;
    }

    /**
     * find attraction id by name
     *
     * @param name attraction name
     * @return if found, return attraction id, else return null
     */
    public String findAttractionIdByName(String name) {
        Attraction probe = new Attraction();
        probe.setName(name);
        Example<Attraction> example = Example.of(probe);
        Optional<Attraction> attractionOptional = attractionRepository.findOne(example);
        if (attractionOptional.isPresent()) {
            Attraction attraction = attractionOptional.get();
            return attraction.getId();
        } else return null;
    }

    /**
     * Find attractions located at the specified location and within the specified distance range,
     * and list them in order from near to far.
     *
     * @param lng Longitude
     * @param lat Latitude
     * @param radiusKm distance to center(km)
     * @return The list of attractions
     */
    public List<Attraction> findAttractionsWithinRadius(
            double lng, double lat, double radiusKm, String name, List<String> tags) {
        double maxDistanceMeters = radiusKm * 1000; // Mongo expects meters for $nearSphere
        String nameRegex = (name == null || name.isBlank()) ? ".*" : ".*" + name + ".*";
        return attractionRepository.findByLocationNear(lng, lat, maxDistanceMeters);
    }

    /**
     * Find attractions located at the specified location and within the specified distance range
     *
     * @param lng Longitude
     * @param lat Latitude
     * @param radiusKm distance to center(km)
     * @return The list of attractions
     */
    public List<Attraction> findAttractionsWithinCircle(
            double lng, double lat, double radiusKm, String name, List<String> tags) {
        double radiusInRadians = radiusKm / 6378.1; // convert km -> radians for $centerSphere
        String nameRegex = (name == null || name.isBlank()) ? ".*" : ".*" + name + ".*";
        return attractionRepository.findByLocationWithinWithFilters(
                lng, lat, radiusInRadians, nameRegex, tags);
    }

    /**
     * Find attractions located at the specified location and within the specified distance range,
     * and list them in order from near to far, and result has been paginated
     *
     * @param lng Longitude
     * @param lat Latitude
     * @param radiusKm distance to center(km)
     * @param page which page you want to find, start from 0
     * @param size page size
     * @return The page of attractions
     */
    public Page<Attraction> findAttractionsWithinRadius(
            double lng,
            double lat,
            double radiusKm,
            String name,
            List<String> tags,
            int page,
            int size) {
        double maxDistanceMeters = radiusKm * 1000;
        String nameRegex = (name == null || name.isBlank()) ? ".*" : ".*" + name + ".*";
        Pageable pageable = PageRequest.of(page, size);
        return attractionRepository.findByLocationNearWithFilters(
                lng, lat, maxDistanceMeters, nameRegex, tags, pageable);
    }

    /**
     * Find attractions located at the specified location and within the specified distance range,
     * and result has been paginated
     *
     * @param lng Longitude
     * @param lat Latitude
     * @param radiusKm distance to center(km)
     * @param page which page you want to find, start from 0
     * @param size page size
     * @return The page of attractions
     */
    public Page<Attraction> findAttractionsWithinCircle(
            double lng,
            double lat,
            double radiusKm,
            String name,
            List<String> tags,
            int page,
            int size) {
        double radiusInRadians = radiusKm / 6378.1;
        String nameRegex = (name == null || name.isBlank()) ? ".*" : ".*" + name + ".*";
        Pageable pageable = PageRequest.of(page, size);
        return attractionRepository.findByLocationWithinWithFilters(
                lng, lat, radiusInRadians, nameRegex, tags, pageable);
    }
}
