package org.tripsphere.poi.infrastructure.adapter.outbound.persistence;

import java.util.List;
import org.springframework.data.geo.Point;
import org.tripsphere.poi.infrastructure.adapter.outbound.persistence.document.PoiDoc;

public interface CustomPoiDocRepository {

    List<PoiDoc> findAllByLocationNear(
            Point location, double radiusMeters, int limit, List<String> categories, String adcode);

    List<PoiDoc> findAllByLocationInBox(
            Point southWest, Point northEast, int limit, List<String> categories, String adcode);
}
