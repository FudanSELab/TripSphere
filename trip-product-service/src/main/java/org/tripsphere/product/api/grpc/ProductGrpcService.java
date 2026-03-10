package org.tripsphere.product.api.grpc;

import io.grpc.stub.StreamObserver;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.product.exception.InvalidArgumentException;
import org.tripsphere.product.exception.NotFoundException;
import org.tripsphere.product.service.ProductService;
import org.tripsphere.product.service.ProductService.SpuPage;
import org.tripsphere.product.v1.*;

@GrpcService
@RequiredArgsConstructor
public class ProductGrpcService extends ProductServiceGrpc.ProductServiceImplBase {

    private final ProductService productService;

    @Override
    public void createSpu(
            CreateSpuRequest request, StreamObserver<CreateSpuResponse> responseObserver) {
        if (!request.hasSpu()) {
            throw InvalidArgumentException.required("spu");
        }

        Spu created = productService.createSpu(request.getSpu());

        responseObserver.onNext(CreateSpuResponse.newBuilder().setSpu(created).build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchCreateSpus(
            BatchCreateSpusRequest request,
            StreamObserver<BatchCreateSpusResponse> responseObserver) {
        List<CreateSpuRequest> requests = request.getRequestsList();
        if (requests.isEmpty()) {
            throw new InvalidArgumentException("Request list for batch creation is empty");
        }

        List<Spu> spusToCreate =
                requests.stream()
                        .filter(CreateSpuRequest::hasSpu)
                        .map(CreateSpuRequest::getSpu)
                        .toList();

        if (spusToCreate.isEmpty()) {
            throw new InvalidArgumentException("No valid SPU data in batch creation request");
        }

        List<Spu> created = productService.batchCreateSpus(spusToCreate);

        responseObserver.onNext(BatchCreateSpusResponse.newBuilder().addAllSpus(created).build());
        responseObserver.onCompleted();
    }

    @Override
    public void getSpuById(
            GetSpuByIdRequest request, StreamObserver<GetSpuByIdResponse> responseObserver) {
        String id = request.getId();
        if (id.isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        Spu spu = productService.getSpuById(id).orElseThrow(() -> new NotFoundException("SPU", id));

        responseObserver.onNext(GetSpuByIdResponse.newBuilder().setSpu(spu).build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchGetSpus(
            BatchGetSpusRequest request, StreamObserver<BatchGetSpusResponse> responseObserver) {
        List<String> ids = request.getIdsList();
        if (ids.isEmpty()) {
            responseObserver.onNext(BatchGetSpusResponse.newBuilder().build());
            responseObserver.onCompleted();
            return;
        }

        List<Spu> spus = productService.batchGetSpus(ids);

        Map<String, Spu> spusById =
                spus.stream().collect(Collectors.toMap(Spu::getId, Function.identity()));

        List<String> missingIds = ids.stream().filter(id -> !spusById.containsKey(id)).toList();
        if (!missingIds.isEmpty()) {
            throw new NotFoundException("SPUs with IDs " + missingIds + " not found");
        }

        List<Spu> orderedSpus = ids.stream().map(spusById::get).toList();

        responseObserver.onNext(BatchGetSpusResponse.newBuilder().addAllSpus(orderedSpus).build());
        responseObserver.onCompleted();
    }

    @Override
    public void listSpusByResource(
            ListSpusByResourceRequest request,
            StreamObserver<ListSpusByResourceResponse> responseObserver) {
        if (request.getResourceType() == ResourceType.RESOURCE_TYPE_UNSPECIFIED) {
            throw InvalidArgumentException.required("resource_type");
        }
        if (request.getResourceId().isEmpty()) {
            throw InvalidArgumentException.required("resource_id");
        }

        String resourceType =
                switch (request.getResourceType()) {
                    case RESOURCE_TYPE_HOTEL_ROOM -> "RESOURCE_TYPE_HOTEL_ROOM";
                    case RESOURCE_TYPE_ATTRACTION -> "RESOURCE_TYPE_ATTRACTION";
                    default -> "RESOURCE_TYPE_UNSPECIFIED";
                };

        SpuPage page =
                productService.listSpusByResource(
                        resourceType,
                        request.getResourceId(),
                        request.getPageSize(),
                        request.getPageToken());

        ListSpusByResourceResponse.Builder responseBuilder =
                ListSpusByResourceResponse.newBuilder().addAllSpus(page.spus());

        if (page.nextPageToken() != null && !page.nextPageToken().isEmpty()) {
            responseBuilder.setNextPageToken(page.nextPageToken());
        }

        responseObserver.onNext(responseBuilder.build());
        responseObserver.onCompleted();
    }

    @Override
    public void updateSpu(
            UpdateSpuRequest request, StreamObserver<UpdateSpuResponse> responseObserver) {
        if (!request.hasSpu()) {
            throw InvalidArgumentException.required("spu");
        }
        if (request.getSpu().getId().isEmpty()) {
            throw InvalidArgumentException.required("spu.id");
        }

        List<String> fieldPaths = List.of();
        if (request.hasFieldMask()) {
            fieldPaths = request.getFieldMask().getPathsList();
        }

        Spu updated = productService.updateSpu(request.getSpu(), fieldPaths);

        responseObserver.onNext(UpdateSpuResponse.newBuilder().setSpu(updated).build());
        responseObserver.onCompleted();
    }

    @Override
    public void getSkuById(
            GetSkuByIdRequest request, StreamObserver<GetSkuByIdResponse> responseObserver) {
        String id = request.getId();
        if (id.isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        Sku sku = productService.getSkuById(id).orElseThrow(() -> new NotFoundException("SKU", id));

        responseObserver.onNext(GetSkuByIdResponse.newBuilder().setSku(sku).build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchGetSkus(
            BatchGetSkusRequest request, StreamObserver<BatchGetSkusResponse> responseObserver) {
        List<String> ids = request.getIdsList();
        if (ids.isEmpty()) {
            responseObserver.onNext(BatchGetSkusResponse.newBuilder().build());
            responseObserver.onCompleted();
            return;
        }

        List<Sku> skus = productService.batchGetSkus(ids);

        Map<String, Sku> skusById =
                skus.stream().collect(Collectors.toMap(Sku::getId, Function.identity()));

        List<String> missingIds = ids.stream().filter(id -> !skusById.containsKey(id)).toList();
        if (!missingIds.isEmpty()) {
            throw new NotFoundException("SKUs with IDs " + missingIds + " not found");
        }

        List<Sku> orderedSkus = ids.stream().map(skusById::get).toList();

        responseObserver.onNext(BatchGetSkusResponse.newBuilder().addAllSkus(orderedSkus).build());
        responseObserver.onCompleted();
    }
}
