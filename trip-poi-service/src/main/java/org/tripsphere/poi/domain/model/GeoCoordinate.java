package org.tripsphere.poi.domain.model;

import org.tripsphere.poi.domain.util.CoordinateTransformUtil;

/** Represents a geographic coordinate in WGS84 coordinate system. */
public record GeoCoordinate(double longitude, double latitude) {

    public static GeoCoordinate of(double longitude, double latitude) {
        return new GeoCoordinate(longitude, latitude);
    }

    public static GeoCoordinate fromGcj02(double longitude, double latitude) {
        double[] wgs84 = CoordinateTransformUtil.gcj02ToWgs84(longitude, latitude);
        return new GeoCoordinate(wgs84[0], wgs84[1]);
    }

    public double[] toGcj02() {
        return CoordinateTransformUtil.wgs84ToGcj02(longitude, latitude);
    }
}
