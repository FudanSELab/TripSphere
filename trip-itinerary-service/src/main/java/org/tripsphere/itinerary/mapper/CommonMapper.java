package org.tripsphere.itinerary.mapper;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.f4b6a3.uuid.UuidCreator;
import com.google.protobuf.InvalidProtocolBufferException;
import com.google.protobuf.Struct;
import com.google.protobuf.Timestamp;
import com.google.protobuf.util.JsonFormat;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Map;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.mapstruct.factory.Mappers;
import org.tripsphere.common.v1.Date;
import org.tripsphere.common.v1.TimeOfDay;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface CommonMapper {
    CommonMapper INSTANCE = Mappers.getMapper(CommonMapper.class);

    ObjectMapper objectMapper = new ObjectMapper();

    // ===================================================================
    // Date Mappings (LocalDate <-> proto Date)
    // ===================================================================

    default LocalDate toLocalDate(Date date) {
        if (date == null || date.equals(Date.getDefaultInstance())) {
            return null;
        }
        return LocalDate.of(date.getYear(), date.getMonth(), date.getDay());
    }

    default Date toDateProto(LocalDate localDate) {
        if (localDate == null) return Date.getDefaultInstance();
        return Date.newBuilder()
                .setYear(localDate.getYear())
                .setMonth(localDate.getMonthValue())
                .setDay(localDate.getDayOfMonth())
                .build();
    }

    // ===================================================================
    // TimeOfDay Mappings (LocalTime <-> proto TimeOfDay)
    // ===================================================================

    default LocalTime toLocalTime(TimeOfDay timeOfDay) {
        if (timeOfDay == null || timeOfDay.equals(TimeOfDay.getDefaultInstance())) {
            return null;
        }
        return LocalTime.of(timeOfDay.getHours(), timeOfDay.getMinutes(), timeOfDay.getSeconds(), timeOfDay.getNanos());
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
    // Timestamp Mappings (Instant <-> proto Timestamp)
    // ===================================================================

    default Timestamp toTimestamp(Instant instant) {
        if (instant == null) return Timestamp.getDefaultInstance();
        return Timestamp.newBuilder()
                .setSeconds(instant.getEpochSecond())
                .setNanos(instant.getNano())
                .build();
    }

    default Instant toInstant(Timestamp timestamp) {
        if (timestamp == null || timestamp.equals(Timestamp.getDefaultInstance())) return null;
        return Instant.ofEpochSecond(timestamp.getSeconds(), timestamp.getNanos());
    }

    // ===================================================================
    // ID Generation
    // ===================================================================

    default String ensureId(String id) {
        return (id == null || id.isEmpty()) ? UuidCreator.getTimeOrderedEpoch().toString() : id;
    }
}
