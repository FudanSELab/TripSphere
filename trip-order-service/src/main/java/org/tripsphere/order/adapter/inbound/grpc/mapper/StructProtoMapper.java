package org.tripsphere.order.adapter.inbound.grpc.mapper;

import com.google.protobuf.ListValue;
import com.google.protobuf.NullValue;
import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface StructProtoMapper {

    default Struct mapStruct(Map<String, Object> map) {
        if (map == null) {
            return null;
        }
        Struct.Builder builder = Struct.newBuilder();
        map.forEach((key, value) -> builder.putFields(key, toValue(value)));
        return builder.build();
    }

    default Map<String, Object> mapStruct(Struct struct) {
        if (struct == null) {
            return null;
        }
        Map<String, Object> result = new HashMap<>();
        struct.getFieldsMap().forEach((key, value) -> result.put(key, fromValue(value)));
        return result;
    }

    @SuppressWarnings("unchecked")
    private static Value toValue(Object obj) {
        if (obj == null) {
            return Value.newBuilder().setNullValue(NullValue.NULL_VALUE).build();
        } else if (obj instanceof String s) {
            return Value.newBuilder().setStringValue(s).build();
        } else if (obj instanceof Number n) {
            return Value.newBuilder().setNumberValue(n.doubleValue()).build();
        } else if (obj instanceof Boolean b) {
            return Value.newBuilder().setBoolValue(b).build();
        } else if (obj instanceof Map<?, ?> m) {
            Struct.Builder struct = Struct.newBuilder();
            ((Map<String, Object>) m).forEach((k, v) -> struct.putFields(k, toValue(v)));
            return Value.newBuilder().setStructValue(struct).build();
        } else if (obj instanceof List<?> list) {
            ListValue.Builder listBuilder = ListValue.newBuilder();
            list.forEach(item -> listBuilder.addValues(toValue(item)));
            return Value.newBuilder().setListValue(listBuilder).build();
        }
        return Value.newBuilder().setStringValue(obj.toString()).build();
    }

    private static Object fromValue(Value value) {
        return switch (value.getKindCase()) {
            case NULL_VALUE -> null;
            case NUMBER_VALUE -> value.getNumberValue();
            case STRING_VALUE -> value.getStringValue();
            case BOOL_VALUE -> value.getBoolValue();
            case STRUCT_VALUE -> {
                Map<String, Object> map = new HashMap<>();
                value.getStructValue().getFieldsMap().forEach((k, v) -> map.put(k, fromValue(v)));
                yield map;
            }
            case LIST_VALUE ->
                value.getListValue().getValuesList().stream()
                        .map(StructProtoMapper::fromValue)
                        .toList();
            case KIND_NOT_SET -> null;
        };
    }
}
