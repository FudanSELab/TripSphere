package org.tripsphere.order.grpc.client;

import java.util.List;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.client.inject.GrpcClient;
import org.springframework.stereotype.Component;
import org.tripsphere.product.v1.*;

@Slf4j
@Component
public class ProductServiceClient {

    @GrpcClient("trip-product-service")
    private ProductServiceGrpc.ProductServiceBlockingStub productStub;

    public Sku getSkuById(String skuId) {
        log.debug("Fetching SKU: {}", skuId);
        GetSkuByIdResponse response =
                productStub.getSkuById(GetSkuByIdRequest.newBuilder().setId(skuId).build());
        return response.getSku();
    }

    public List<Sku> batchGetSkus(List<String> skuIds) {
        log.debug("Batch fetching {} SKUs", skuIds.size());
        BatchGetSkusResponse response =
                productStub.batchGetSkus(
                        BatchGetSkusRequest.newBuilder().addAllIds(skuIds).build());
        return response.getSkusList();
    }

    public Spu getSpuById(String spuId) {
        log.debug("Fetching SPU: {}", spuId);
        GetSpuByIdResponse response =
                productStub.getSpuById(GetSpuByIdRequest.newBuilder().setId(spuId).build());
        return response.getSpu();
    }

    public List<Spu> batchGetSpus(List<String> spuIds) {
        log.debug("Batch fetching {} SPUs", spuIds.size());
        BatchGetSpusResponse response =
                productStub.batchGetSpus(
                        BatchGetSpusRequest.newBuilder().addAllIds(spuIds).build());
        return response.getSpusList();
    }
}
