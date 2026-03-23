package org.tripsphere.attraction.repository;

import java.util.List;
import org.springframework.data.geo.Point;
import org.tripsphere.attraction.model.AttractionDoc;

public interface CustomAttractionDocRepository {

    List<AttractionDoc> findAllByLocationNear(Point point, double radiusMeters, int limit, List<String> tags);
}
