package org.tripsphere.order.adapter.outbound.grpc;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.protobuf.Struct;
import com.google.protobuf.util.JsonFormat;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.client.inject.GrpcClient;
import org.springframework.stereotype.Component;
import org.tripsphere.order.application.dto.SkuInfo;
import org.tripsphere.order.application.dto.SpuInfo;
import org.tripsphere.order.application.port.ProductPort;
import org.tripsphere.order.domain.model.Money;
import org.tripsphere.product.v1.*;

@Slf4j
@Component
public class ProductGrpcAdapter implements ProductPort {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
    private static final TypeReference<Map<String, Object>> MAP_TYPE_REF = new TypeReference<>() {};

    @GrpcClient("trip-product-service")
    private ProductServiceGrpc.ProductServiceBlockingStub productStub;

    @Override
    public List<SkuInfo> batchGetSkus(List<String> skuIds) {
        log.debug("Batch fetching {} SKUs", skuIds.size());
        BatchGetSkusResponse response = productStub.batchGetSkus(
                BatchGetSkusRequest.newBuilder().addAllIds(skuIds).build());
        return response.getSkusList().stream().map(this::toSkuInfo).toList();
    }

    @Override
    public List<SpuInfo> batchGetSpus(List<String> spuIds) {
        log.debug("Batch fetching {} SPUs", spuIds.size());
        BatchGetSpusResponse response = productStub.batchGetSpus(
                BatchGetSpusRequest.newBuilder().addAllIds(spuIds).build());
        return response.getSpusList().stream().map(this::toSpuInfo).toList();
    }

    private SkuInfo toSkuInfo(Sku proto) {
        Money basePrice = Money.zero();
        if (proto.hasBasePrice()) {
            basePrice = new Money(
                    proto.getBasePrice().getCurrency().isEmpty()
                            ? "CNY"
                            : proto.getBasePrice().getCurrency(),
                    proto.getBasePrice().getUnits(),
                    proto.getBasePrice().getNanos());
        }
        return new SkuInfo(
                proto.getId(),
                proto.getSpuId(),
                proto.getName(),
                proto.getStatus() == SkuStatus.SKU_STATUS_ACTIVE,
                basePrice,
                structToMap(proto.getAttributes()));
    }

    private SpuInfo toSpuInfo(Spu proto) {
        String resourceType =
                switch (proto.getResourceType()) {
                    case RESOURCE_TYPE_HOTEL_ROOM -> "HOTEL_ROOM";
                    case RESOURCE_TYPE_ATTRACTION -> "ATTRACTION";
                    default -> "UNSPECIFIED";
                };
        return new SpuInfo(
                proto.getId(),
                proto.getName(),
                proto.getDescription(),
                resourceType,
                proto.getResourceId(),
                proto.getImagesList(),
                structToMap(proto.getAttributes()));
    }

    private Map<String, Object> structToMap(Struct struct) {
        if (struct == null || struct.getFieldsCount() == 0) return null;
        try {
            String json = JsonFormat.printer().print(struct);
            return OBJECT_MAPPER.readValue(json, MAP_TYPE_REF);
        } catch (Exception e) {
            log.warn("Failed to convert struct to map: {}", e.getMessage());
            return null;
        }
    }
}
