package org.tripsphere.attraction.mapper;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.protobuf.InvalidProtocolBufferException;
import com.google.protobuf.Struct;
import com.google.protobuf.util.JsonFormat;
import java.time.LocalTime;
import java.util.Map;
import org.mapstruct.*;
import org.mapstruct.factory.Mappers;
import org.springframework.data.mongodb.core.geo.GeoJsonPoint;
import org.tripsphere.attraction.util.CoordinateTransformUtil;
import org.tripsphere.common.v1.GeoPoint;
import org.tripsphere.common.v1.TimeOfDay;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface CommonMapper {
    CommonMapper INSTANCE = Mappers.getMapper(CommonMapper.class);

    static final ObjectMapper objectMapper = new ObjectMapper();

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
    // Struct <-> Map Conversions
    // ===================================================================

    default Map<String, Object> toMap(Struct struct) throws InvalidProtocolBufferException, JsonProcessingException {
        if (struct == null || struct.equals(Struct.getDefaultInstance())) {
            return Map.of();
        }
        String json = JsonFormat.printer().print(struct);
        return objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {});
    }

    default Struct toStruct(Map<String, Object> map) throws JsonProcessingException, InvalidProtocolBufferException {
        if (map == null || map.isEmpty()) {
            return Struct.getDefaultInstance();
        }
        String json = objectMapper.writeValueAsString(map);
        Struct.Builder structBuilder = Struct.newBuilder();
        JsonFormat.parser().merge(json, structBuilder);
        return structBuilder.build();
    }

    // ===================================================================
    // DayOfWeek Mappings
    // ===================================================================

    default java.time.DayOfWeek toJavaDayOfWeek(org.tripsphere.common.v1.DayOfWeek protoDayOfWeek) {
        if (protoDayOfWeek == null) return null;
        return switch (protoDayOfWeek) {
            case DAY_OF_WEEK_MONDAY -> java.time.DayOfWeek.MONDAY;
            case DAY_OF_WEEK_TUESDAY -> java.time.DayOfWeek.TUESDAY;
            case DAY_OF_WEEK_WEDNESDAY -> java.time.DayOfWeek.WEDNESDAY;
            case DAY_OF_WEEK_THURSDAY -> java.time.DayOfWeek.THURSDAY;
            case DAY_OF_WEEK_FRIDAY -> java.time.DayOfWeek.FRIDAY;
            case DAY_OF_WEEK_SATURDAY -> java.time.DayOfWeek.SATURDAY;
            case DAY_OF_WEEK_SUNDAY -> java.time.DayOfWeek.SUNDAY;
            default -> null;
        };
    }

    default org.tripsphere.common.v1.DayOfWeek toProtoDayOfWeek(java.time.DayOfWeek javaDayOfWeek) {
        if (javaDayOfWeek == null) return org.tripsphere.common.v1.DayOfWeek.DAY_OF_WEEK_UNSPECIFIED;
        return switch (javaDayOfWeek) {
            case MONDAY -> org.tripsphere.common.v1.DayOfWeek.DAY_OF_WEEK_MONDAY;
            case TUESDAY -> org.tripsphere.common.v1.DayOfWeek.DAY_OF_WEEK_TUESDAY;
            case WEDNESDAY -> org.tripsphere.common.v1.DayOfWeek.DAY_OF_WEEK_WEDNESDAY;
            case THURSDAY -> org.tripsphere.common.v1.DayOfWeek.DAY_OF_WEEK_THURSDAY;
            case FRIDAY -> org.tripsphere.common.v1.DayOfWeek.DAY_OF_WEEK_FRIDAY;
            case SATURDAY -> org.tripsphere.common.v1.DayOfWeek.DAY_OF_WEEK_SATURDAY;
            case SUNDAY -> org.tripsphere.common.v1.DayOfWeek.DAY_OF_WEEK_SUNDAY;
        };
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
}
