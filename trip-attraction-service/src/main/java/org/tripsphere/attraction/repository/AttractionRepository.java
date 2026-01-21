package org.tripsphere.attraction.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;
import org.tripsphere.attraction.model.Attraction;

@Repository
public interface AttractionRepository extends MongoRepository<Attraction, String> {
    public Optional<Attraction> findById(String id);

    @Query(
            """
            {
              'location': {
                $nearSphere: {
                  $geometry: { type: 'Point', coordinates: [?0, ?1] },
                  $maxDistance: ?2
                }
              }
            }
            """)
    List<Attraction> findByLocationNearWithFilters(
            double lng, double lat, double maxDistanceMeters);

    @Query(
            """
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
    List<Attraction> findByLocationWithinWithFilters(
            double lng, double lat, double radiusInRadians, String nameRegex, List<String> tags);

    @Query(
            """
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
    Page<Attraction> findByLocationNearWithFilters(
            double lng,
            double lat,
            double maxDistanceMeters,
            String nameRegex,
            List<String> tags,
            Pageable pageable);

    @Query(
            """
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
    Page<Attraction> findByLocationWithinWithFilters(
            double lng,
            double lat,
            double radiusInRadians,
            String nameRegex,
            List<String> tags,
            Pageable pageable);
}
