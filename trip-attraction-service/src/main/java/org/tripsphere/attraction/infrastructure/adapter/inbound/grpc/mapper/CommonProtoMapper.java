package org.tripsphere.attraction.infrastructure.adapter.inbound.grpc.mapper;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.protobuf.InvalidProtocolBufferException;
import com.google.protobuf.Struct;
import com.google.protobuf.util.JsonFormat;
import java.math.BigDecimal;
import java.time.LocalTime;
import java.util.Currency;
import java.util.Map;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.Named;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.attraction.domain.model.GeoLocation;
import org.tripsphere.attraction.domain.model.Money;
import org.tripsphere.attraction.infrastructure.util.CoordinateTransformUtil;
import org.tripsphere.common.v1.GeoPoint;
import org.tripsphere.common.v1.TimeOfDay;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface CommonProtoMapper {

    ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    // ===================================================================
    // GeoLocation (WGS84) <-> GeoPoint (GCJ-02) with coordinate transform
    // ===================================================================

    @Named("toGeoPointGCJ02")
    default GeoPoint toGeoPoint(GeoLocation wgs84) {
        if (wgs84 == null) return GeoPoint.getDefaultInstance();
        double[] gcj02 = CoordinateTransformUtil.wgs84ToGcj02(wgs84.longitude(), wgs84.latitude());
        return GeoPoint.newBuilder()
                .setLongitude(gcj02[0])
                .setLatitude(gcj02[1])
                .build();
    }

    @Named("toGeoLocationWGS84")
    default GeoLocation toGeoLocation(GeoPoint gcj02) {
        if (gcj02 == null || gcj02.equals(GeoPoint.getDefaultInstance())) return null;
        double[] wgs84 = CoordinateTransformUtil.gcj02ToWgs84(gcj02.getLongitude(), gcj02.getLatitude());
        return new GeoLocation(wgs84[0], wgs84[1]);
    }

    // ===================================================================
    // LocalTime <-> TimeOfDay
    // ===================================================================

    default LocalTime toLocalTime(TimeOfDay proto) {
        if (proto == null || proto.equals(TimeOfDay.getDefaultInstance())) return null;
        return LocalTime.of(proto.getHours(), proto.getMinutes(), proto.getSeconds(), proto.getNanos());
    }

    default TimeOfDay toTimeOfDay(LocalTime localTime) {
        if (localTime == null) return TimeOfDay.getDefaultInstance();
        return TimeOfDay.newBuilder()
                .setHours(localTime.getHour())
                .setMinutes(localTime.getMinute())
                .setSeconds(localTime.getSecond())
                .setNanos(localTime.getNano())
                .build();
    }

    // ===================================================================
    // DayOfWeek (Java) <-> DayOfWeek (proto)
    // ===================================================================

    default java.time.DayOfWeek toJavaDayOfWeek(org.tripsphere.common.v1.DayOfWeek proto) {
        if (proto == null) return null;
        return switch (proto) {
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

    default org.tripsphere.common.v1.DayOfWeek toProtoDayOfWeek(java.time.DayOfWeek java) {
        if (java == null) return org.tripsphere.common.v1.DayOfWeek.DAY_OF_WEEK_UNSPECIFIED;
        return switch (java) {
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
    // Money (domain) <-> Money (proto)
    // ===================================================================

    default Money toMoney(org.tripsphere.common.v1.Money proto) {
        if (proto == null || proto.equals(org.tripsphere.common.v1.Money.getDefaultInstance())) return null;
        Currency currency = Currency.getInstance(proto.getCurrency());
        BigDecimal amount = BigDecimal.valueOf(proto.getUnits()).add(BigDecimal.valueOf(proto.getNanos(), 9));
        return new Money(currency, amount);
    }

    default org.tripsphere.common.v1.Money toMoneyProto(Money money) {
        if (money == null) return org.tripsphere.common.v1.Money.getDefaultInstance();
        org.tripsphere.common.v1.Money.Builder builder = org.tripsphere.common.v1.Money.newBuilder();
        if (money.currency() != null) {
            builder.setCurrency(money.currency().getCurrencyCode());
        }
        if (money.amount() != null) {
            long units = money.amount().longValue();
            int nanos =
                    money.amount().remainder(BigDecimal.ONE).movePointRight(9).intValue();
            builder.setUnits(units);
            builder.setNanos(nanos);
        }
        return builder.build();
    }

    // ===================================================================
    // Map<String, Object> <-> Struct
    // ===================================================================

    default Map<String, Object> toMap(Struct struct) throws InvalidProtocolBufferException, JsonProcessingException {
        if (struct == null || struct.equals(Struct.getDefaultInstance())) return Map.of();
        String json = JsonFormat.printer().print(struct);
        return OBJECT_MAPPER.readValue(json, new TypeReference<Map<String, Object>>() {});
    }

    default Struct toStruct(Map<String, Object> map) throws JsonProcessingException, InvalidProtocolBufferException {
        if (map == null || map.isEmpty()) return Struct.getDefaultInstance();
        String json = OBJECT_MAPPER.writeValueAsString(map);
        Struct.Builder builder = Struct.newBuilder();
        JsonFormat.parser().merge(json, builder);
        return builder.build();
    }
}
