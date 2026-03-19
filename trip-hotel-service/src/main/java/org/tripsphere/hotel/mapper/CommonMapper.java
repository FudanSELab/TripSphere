package org.tripsphere.hotel.mapper;

import java.time.LocalDate;
import java.time.LocalTime;
import org.mapstruct.*;
import org.mapstruct.factory.Mappers;
import org.springframework.data.mongodb.core.geo.GeoJsonPoint;
import org.tripsphere.common.v1.Date;
import org.tripsphere.common.v1.GeoPoint;
import org.tripsphere.common.v1.TimeOfDay;
import org.tripsphere.hotel.util.CoordinateTransformUtil;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface CommonMapper {
    CommonMapper INSTANCE = Mappers.getMapper(CommonMapper.class);

    // ===================================================================
    // GeoPoint <-> GeoJsonPoint (with coordinate transformation)
    // ===================================================================

    default GeoJsonPoint toGeoJsonPoint(GeoPoint point) {
        if (point == null || (point.getLongitude() == 0.0 && point.getLatitude() == 0.0 && !point.isInitialized())) {
            return null;
        }
        double[] coordinate = CoordinateTransformUtil.gcj02ToWgs84(point.getLongitude(), point.getLatitude());
        return new GeoJsonPoint(coordinate[0], coordinate[1]);
    }

    default GeoPoint toGeoPoint(GeoJsonPoint geoJsonPoint) {
        if (geoJsonPoint == null) return GeoPoint.getDefaultInstance();
        double[] coordinate = CoordinateTransformUtil.wgs84ToGcj02(geoJsonPoint.getX(), geoJsonPoint.getY());
        return GeoPoint.newBuilder()
                .setLongitude(coordinate[0])
                .setLatitude(coordinate[1])
                .build();
    }

    // ===================================================================
    // LocalTime <-> TimeOfDay Mappings
    // ===================================================================

    default LocalTime toLocalTime(TimeOfDay proto) {
        if (proto == null || proto.equals(TimeOfDay.getDefaultInstance())) {
            return null;
        }
        return LocalTime.of(proto.getHours(), proto.getMinutes(), proto.getSeconds(), proto.getNanos());
    }

    default TimeOfDay toTimeOfDayProto(LocalTime localTime) {
        if (localTime == null) return TimeOfDay.getDefaultInstance();
        return TimeOfDay.newBuilder()
                .setHours(localTime.getHour())
                .setMinutes(localTime.getMinute())
                .setSeconds(localTime.getSecond())
                .setNanos(localTime.getNano())
                .build();
    }

    // ===================================================================
    // LocalDate <-> Date Mappings
    // ===================================================================

    default LocalDate toLocalDate(Date proto) {
        if (proto == null || proto.equals(Date.getDefaultInstance())) {
            return null;
        }
        if (proto.getYear() == 0 || proto.getMonth() == 0 || proto.getDay() == 0) {
            return null;
        }
        return LocalDate.of(proto.getYear(), proto.getMonth(), proto.getDay());
    }

    default Date toDateProto(LocalDate localDate) {
        if (localDate == null) return Date.getDefaultInstance();
        return Date.newBuilder()
                .setYear(localDate.getYear())
                .setMonth(localDate.getMonthValue())
                .setDay(localDate.getDayOfMonth())
                .build();
    }
}
