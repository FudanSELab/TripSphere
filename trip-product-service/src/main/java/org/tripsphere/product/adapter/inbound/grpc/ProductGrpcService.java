package org.tripsphere.product.adapter.inbound.grpc;

import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import io.grpc.stub.StreamObserver;
import java.util.List;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.product.adapter.inbound.grpc.mapper.MoneyProtoMapper;
import org.tripsphere.product.adapter.inbound.grpc.mapper.SkuProtoMapper;
import org.tripsphere.product.adapter.inbound.grpc.mapper.SpuProtoMapper;
import org.tripsphere.product.adapter.inbound.grpc.mapper.StructProtoMapper;
import org.tripsphere.product.application.dto.CreateSpuCommand;
import org.tripsphere.product.application.dto.SpuPage;
import org.tripsphere.product.application.dto.UpdateSpuCommand;
import org.tripsphere.product.application.service.command.BatchCreateSpusUseCase;
import org.tripsphere.product.application.service.command.CreateSpuUseCase;
import org.tripsphere.product.application.service.command.UpdateSpuUseCase;
import org.tripsphere.product.application.service.query.BatchGetSkusUseCase;
import org.tripsphere.product.application.service.query.BatchGetSpusUseCase;
import org.tripsphere.product.application.service.query.GetSkuUseCase;
import org.tripsphere.product.application.service.query.GetSpuUseCase;
import org.tripsphere.product.application.service.query.ListSpusByResourceUseCase;
import org.tripsphere.product.domain.model.Sku;
import org.tripsphere.product.v1.*;

@GrpcService
@RequiredArgsConstructor
public class ProductGrpcService extends ProductServiceGrpc.ProductServiceImplBase {
    private final SpuProtoMapper spuProtoMapper;
    private final SkuProtoMapper skuProtoMapper;
    private final MoneyProtoMapper moneyProtoMapper;
    private final StructProtoMapper structProtoMapper;
    private final GetSpuUseCase getSpuUseCase;
    private final BatchGetSpusUseCase batchGetSpusUseCase;
    private final CreateSpuUseCase createSpuUseCase;
    private final BatchCreateSpusUseCase batchCreateSpusUseCase;
    private final UpdateSpuUseCase updateSpuUseCase;
    private final GetSkuUseCase getSkuUseCase;
    private final BatchGetSkusUseCase batchGetSkusUseCase;
    private final ListSpusByResourceUseCase listSpusByResourceUseCase;

    @Override
    public void createSpu(CreateSpuRequest request, StreamObserver<CreateSpuResponse> responseObserver) {
        if (!request.hasSpu()) {
            throw invalidArgument("spu is required");
        }
        CreateSpuCommand command = toCreateCommand(request.getSpu());
        org.tripsphere.product.domain.model.Spu created = createSpuUseCase.execute(command);

        responseObserver.onNext(CreateSpuResponse.newBuilder()
                .setSpu(spuProtoMapper.map(created))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchCreateSpus(
            BatchCreateSpusRequest request, StreamObserver<BatchCreateSpusResponse> responseObserver) {
        List<CreateSpuRequest> requests = request.getRequestsList();
        if (requests.isEmpty()) {
            throw invalidArgument("Request list for batch creation is empty");
        }

        List<CreateSpuCommand> commands = requests.stream()
                .filter(CreateSpuRequest::hasSpu)
                .map(r -> toCreateCommand(r.getSpu()))
                .toList();

        if (commands.isEmpty()) {
            throw invalidArgument("No valid SPU data in batch creation request");
        }

        List<org.tripsphere.product.domain.model.Spu> created = batchCreateSpusUseCase.execute(commands);
        List<Spu> protos = spuProtoMapper.mapToProtos(created);

        responseObserver.onNext(
                BatchCreateSpusResponse.newBuilder().addAllSpus(protos).build());
        responseObserver.onCompleted();
    }

    @Override
    public void getSpuById(GetSpuByIdRequest request, StreamObserver<GetSpuByIdResponse> responseObserver) {
        String id = request.getId();
        Spu spu = spuProtoMapper.map(getSpuUseCase.execute(id));
        responseObserver.onNext(GetSpuByIdResponse.newBuilder().setSpu(spu).build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchGetSpus(BatchGetSpusRequest request, StreamObserver<BatchGetSpusResponse> responseObserver) {
        List<String> ids = request.getIdsList();
        List<Spu> orderedSpus = spuProtoMapper.mapToProtos(batchGetSpusUseCase.execute(ids));
        responseObserver.onNext(
                BatchGetSpusResponse.newBuilder().addAllSpus(orderedSpus).build());
        responseObserver.onCompleted();
    }

    @Override
    public void listSpusByResource(
            ListSpusByResourceRequest request, StreamObserver<ListSpusByResourceResponse> responseObserver) {
        if (request.getResourceType() == ResourceType.RESOURCE_TYPE_UNSPECIFIED) {
            throw invalidArgument("resource_type is required");
        }
        if (request.getResourceId().isEmpty()) {
            throw invalidArgument("resource_id is required");
        }

        org.tripsphere.product.domain.model.ResourceType domainResourceType =
                spuProtoMapper.mapResourceTypeToDomain(request.getResourceType());

        SpuPage page = listSpusByResourceUseCase.execute(
                domainResourceType, request.getResourceId(), request.getPageSize(), request.getPageToken());

        ListSpusByResourceResponse.Builder responseBuilder =
                ListSpusByResourceResponse.newBuilder().addAllSpus(spuProtoMapper.mapToProtos(page.spus()));

        if (page.nextPageToken() != null && !page.nextPageToken().isEmpty()) {
            responseBuilder.setNextPageToken(page.nextPageToken());
        }

        responseObserver.onNext(responseBuilder.build());
        responseObserver.onCompleted();
    }

    @Override
    public void updateSpu(UpdateSpuRequest request, StreamObserver<UpdateSpuResponse> responseObserver) {
        if (!request.hasSpu()) {
            throw invalidArgument("spu is required");
        }
        if (request.getSpu().getId().isEmpty()) {
            throw invalidArgument("spu.id is required");
        }

        Spu protoSpu = request.getSpu();
        List<String> fieldPaths =
                request.hasFieldMask() ? request.getFieldMask().getPathsList() : List.of();

        UpdateSpuCommand command = new UpdateSpuCommand(
                protoSpu.getId(),
                fieldPaths,
                protoSpu.getName(),
                protoSpu.getDescription(),
                spuProtoMapper.mapResourceTypeToDomain(protoSpu.getResourceType()),
                protoSpu.getResourceId(),
                protoSpu.getImagesList(),
                structProtoMapper.mapStruct(protoSpu.getAttributes()));

        org.tripsphere.product.domain.model.Spu updated = updateSpuUseCase.execute(command);

        responseObserver.onNext(UpdateSpuResponse.newBuilder()
                .setSpu(spuProtoMapper.map(updated))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void getSkuById(GetSkuByIdRequest request, StreamObserver<GetSkuByIdResponse> responseObserver) {
        String id = request.getId();
        Sku domainSku = getSkuUseCase.execute(id);
        org.tripsphere.product.v1.Sku proto = skuProtoMapper.map(domainSku);

        responseObserver.onNext(GetSkuByIdResponse.newBuilder().setSku(proto).build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchGetSkus(BatchGetSkusRequest request, StreamObserver<BatchGetSkusResponse> responseObserver) {
        List<String> ids = request.getIdsList();
        if (ids.isEmpty()) {
            responseObserver.onNext(BatchGetSkusResponse.newBuilder().build());
            responseObserver.onCompleted();
            return;
        }

        List<Sku> orderedSkus = batchGetSkusUseCase.execute(ids);
        List<org.tripsphere.product.v1.Sku> protos = skuProtoMapper.mapToProtos(orderedSkus);

        responseObserver.onNext(
                BatchGetSkusResponse.newBuilder().addAllSkus(protos).build());
        responseObserver.onCompleted();
    }

    private CreateSpuCommand toCreateCommand(Spu proto) {
        List<CreateSpuCommand.CreateSkuCommand> skuCommands = proto.getSkusList().stream()
                .map(sku -> new CreateSpuCommand.CreateSkuCommand(
                        sku.getName(),
                        sku.getDescription(),
                        skuProtoMapper.mapSkuStatusToDomain(sku.getStatus()),
                        structProtoMapper.mapStruct(sku.getAttributes()),
                        moneyProtoMapper.map(sku.getBasePrice())))
                .toList();

        return new CreateSpuCommand(
                proto.getName(),
                proto.getDescription(),
                spuProtoMapper.mapResourceTypeToDomain(proto.getResourceType()),
                proto.getResourceId(),
                proto.getImagesList(),
                structProtoMapper.mapStruct(proto.getAttributes()),
                skuCommands);
    }

    private static StatusRuntimeException invalidArgument(String message) {
        return Status.INVALID_ARGUMENT.withDescription(message).asRuntimeException();
    }
}
