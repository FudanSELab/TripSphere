package org.tripsphere.product.mapper;

import com.google.protobuf.ListValue;
import com.google.protobuf.NullValue;
import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.mapstruct.factory.Mappers;
import org.tripsphere.product.v1.ResourceType;
import org.tripsphere.product.v1.SkuStatus;
import org.tripsphere.product.v1.SpuStatus;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface CommonMapper {
    CommonMapper INSTANCE = Mappers.getMapper(CommonMapper.class);

    default Map<String, Object> toMap(Struct struct) {
        if (struct == null || struct.equals(Struct.getDefaultInstance())) {
            return null;
        }
        Map<String, Object> map = new HashMap<>();
        for (Map.Entry<String, Value> entry : struct.getFieldsMap().entrySet()) {
            map.put(entry.getKey(), valueToObject(entry.getValue()));
        }
        return map;
    }

    default Object valueToObject(Value value) {
        if (value == null) return null;
        return switch (value.getKindCase()) {
            case NULL_VALUE -> null;
            case NUMBER_VALUE -> value.getNumberValue();
            case STRING_VALUE -> value.getStringValue();
            case BOOL_VALUE -> value.getBoolValue();
            case STRUCT_VALUE -> toMap(value.getStructValue());
            case LIST_VALUE -> value.getListValue().getValuesList().stream()
                    .map(this::valueToObject)
                    .toList();
            default -> null;
        };
    }

    default Struct toStruct(Map<String, Object> map) {
        if (map == null || map.isEmpty()) {
            return Struct.getDefaultInstance();
        }
        Struct.Builder builder = Struct.newBuilder();
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            builder.putFields(entry.getKey(), objectToValue(entry.getValue()));
        }
        return builder.build();
    }

    @SuppressWarnings("unchecked")
    default Value objectToValue(Object obj) {
        if (obj == null) {
            return Value.newBuilder().setNullValue(NullValue.NULL_VALUE).build();
        }
        if (obj instanceof Number number) {
            return Value.newBuilder().setNumberValue(number.doubleValue()).build();
        }
        if (obj instanceof String str) {
            return Value.newBuilder().setStringValue(str).build();
        }
        if (obj instanceof Boolean bool) {
            return Value.newBuilder().setBoolValue(bool).build();
        }
        if (obj instanceof Map<?, ?> nestedMap) {
            return Value.newBuilder()
                    .setStructValue(toStruct((Map<String, Object>) nestedMap))
                    .build();
        }
        if (obj instanceof List<?> list) {
            ListValue.Builder listBuilder = ListValue.newBuilder();
            for (Object item : list) {
                listBuilder.addValues(objectToValue(item));
            }
            return Value.newBuilder().setListValue(listBuilder.build()).build();
        }
        return Value.newBuilder().setStringValue(obj.toString()).build();
    }

    default String resourceTypeToString(ResourceType type) {
        return switch (type) {
            case RESOURCE_TYPE_HOTEL_ROOM -> "RESOURCE_TYPE_HOTEL_ROOM";
            case RESOURCE_TYPE_ATTRACTION -> "RESOURCE_TYPE_ATTRACTION";
            default -> "RESOURCE_TYPE_UNSPECIFIED";
        };
    }

    default ResourceType stringToResourceType(String type) {
        if (type == null) return ResourceType.RESOURCE_TYPE_UNSPECIFIED;
        return switch (type) {
            case "RESOURCE_TYPE_HOTEL_ROOM" -> ResourceType.RESOURCE_TYPE_HOTEL_ROOM;
            case "RESOURCE_TYPE_ATTRACTION" -> ResourceType.RESOURCE_TYPE_ATTRACTION;
            default -> ResourceType.RESOURCE_TYPE_UNSPECIFIED;
        };
    }

    default String spuStatusToString(SpuStatus status) {
        return switch (status) {
            case SPU_STATUS_DRAFT -> "SPU_STATUS_DRAFT";
            case SPU_STATUS_ON_SHELF -> "SPU_STATUS_ON_SHELF";
            case SPU_STATUS_OFF_SHELF -> "SPU_STATUS_OFF_SHELF";
            case SPU_STATUS_DELETED -> "SPU_STATUS_DELETED";
            default -> "SPU_STATUS_DRAFT";
        };
    }

    default SpuStatus stringToSpuStatus(String status) {
        if (status == null) return SpuStatus.SPU_STATUS_UNSPECIFIED;
        return switch (status) {
            case "SPU_STATUS_DRAFT" -> SpuStatus.SPU_STATUS_DRAFT;
            case "SPU_STATUS_ON_SHELF" -> SpuStatus.SPU_STATUS_ON_SHELF;
            case "SPU_STATUS_OFF_SHELF" -> SpuStatus.SPU_STATUS_OFF_SHELF;
            case "SPU_STATUS_DELETED" -> SpuStatus.SPU_STATUS_DELETED;
            default -> SpuStatus.SPU_STATUS_UNSPECIFIED;
        };
    }

    default String skuStatusToString(SkuStatus status) {
        return switch (status) {
            case SKU_STATUS_ACTIVE -> "SKU_STATUS_ACTIVE";
            case SKU_STATUS_INACTIVE -> "SKU_STATUS_INACTIVE";
            case SKU_STATUS_DELETED -> "SKU_STATUS_DELETED";
            default -> "SKU_STATUS_ACTIVE";
        };
    }

    default SkuStatus stringToSkuStatus(String status) {
        if (status == null) return SkuStatus.SKU_STATUS_UNSPECIFIED;
        return switch (status) {
            case "SKU_STATUS_ACTIVE" -> SkuStatus.SKU_STATUS_ACTIVE;
            case "SKU_STATUS_INACTIVE" -> SkuStatus.SKU_STATUS_INACTIVE;
            case "SKU_STATUS_DELETED" -> SkuStatus.SKU_STATUS_DELETED;
            default -> SkuStatus.SKU_STATUS_UNSPECIFIED;
        };
    }
}
