package org.tripsphere.hotel.repository;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;
import org.tripsphere.hotel.model.Hotel;
import org.springframework.data.geo.Distance;
import org.springframework.data.geo.Point;
import org.springframework.data.geo.Circle;

import java.util.List;
import java.util.Optional;

@Repository
public interface HotelRepository extends MongoRepository<Hotel, String> {
    public Optional<Hotel> findById(String id);

    public List<Hotel> findByLocationNear(Point point, Distance distance);

    public List<Hotel> findByLocationWithin(Circle circle);

    public Page<Hotel> findByLocationNear(Point point, Distance distance, Pageable pageable);

    public Page<Hotel> findByLocationWithin(Circle circle, Pageable pageable);

    @Query("""
            {
              'location': {
                $nearSphere: {
                  $geometry: { type: 'Point', coordinates: [?0, ?1] },
                  $maxDistance: ?2
                }
              },
              'name': { $regex: ?3, $options: 'i' },
              'tags': { $all: ?4 }
            }
            """)
    List<Hotel> findByLocationNearWithFilters(double lng, double lat, double maxDistanceMeters, String nameRegex, List<String> tags);

    @Query("""
            {
              'location': {
                $geoWithin: {
                  $centerSphere: [ [ ?0, ?1 ], ?2 ]
                }
              },
              'name': { $regex: ?3, $options: 'i' },
              'tags': { $all: ?4 }
            }
            """)
    List<Hotel> findByLocationWithinWithFilters(double lng, double lat, double radiusInRadians, String nameRegex, List<String> tags);

    @Query("""
            {
              'location': {
                $nearSphere: {
                  $geometry: { type: 'Point', coordinates: [?0, ?1] },
                  $maxDistance: ?2
                }
              },
              'name': { $regex: ?3, $options: 'i' },
              'tags': { $all: ?4 }
            }
            """)
    Page<Hotel> findByLocationNearWithFilters(double lng, double lat, double maxDistanceMeters, String nameRegex, List<String> tags, Pageable pageable);

    @Query("""
            {
              'location': {
                $geoWithin: {
                  $centerSphere: [ [ ?0, ?1 ], ?2 ]
                }
              },
              'name': { $regex: ?3, $options: 'i' },
              'tags': { $all: ?4 }
            }
            """)
    Page<Hotel> findByLocationWithinWithFilters(double lng, double lat, double radiusInRadians, String nameRegex, List<String> tags, Pageable pageable);

}
