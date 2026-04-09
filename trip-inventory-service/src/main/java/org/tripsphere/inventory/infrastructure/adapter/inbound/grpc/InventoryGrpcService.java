package org.tripsphere.inventory.infrastructure.adapter.inbound.grpc;

import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import io.grpc.stub.StreamObserver;
import java.time.LocalDate;
import java.util.List;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.inventory.application.dto.CheckAvailabilityResult;
import org.tripsphere.inventory.application.dto.LockInventoryCommand;
import org.tripsphere.inventory.application.dto.SetDailyInventoryCommand;
import org.tripsphere.inventory.application.service.command.*;
import org.tripsphere.inventory.application.service.query.*;
import org.tripsphere.inventory.domain.model.DailyInventory;
import org.tripsphere.inventory.domain.model.InventoryLock;
import org.tripsphere.inventory.domain.model.Money;
import org.tripsphere.inventory.infrastructure.adapter.inbound.grpc.mapper.DailyInventoryProtoMapper;
import org.tripsphere.inventory.infrastructure.adapter.inbound.grpc.mapper.DateProtoMapper;
import org.tripsphere.inventory.infrastructure.adapter.inbound.grpc.mapper.InventoryLockProtoMapper;
import org.tripsphere.inventory.infrastructure.adapter.inbound.grpc.mapper.MoneyProtoMapper;
import org.tripsphere.inventory.v1.*;

@GrpcService
@RequiredArgsConstructor
public class InventoryGrpcService extends InventoryServiceGrpc.InventoryServiceImplBase {

    private final SetDailyInventoryUseCase setDailyInventoryUseCase;
    private final BatchSetDailyInventoryUseCase batchSetDailyInventoryUseCase;
    private final LockInventoryUseCase lockInventoryUseCase;
    private final ConfirmLockUseCase confirmLockUseCase;
    private final ReleaseLockUseCase releaseLockUseCase;
    private final GetDailyInventoryUseCase getDailyInventoryUseCase;
    private final QueryInventoryCalendarUseCase queryInventoryCalendarUseCase;
    private final CheckAvailabilityUseCase checkAvailabilityUseCase;

    private final DailyInventoryProtoMapper dailyInventoryProtoMapper;
    private final InventoryLockProtoMapper inventoryLockProtoMapper;
    private final DateProtoMapper dateProtoMapper;
    private final MoneyProtoMapper moneyProtoMapper;

    @Override
    public void setDailyInventory(
            SetDailyInventoryRequest request, StreamObserver<SetDailyInventoryResponse> responseObserver) {
        if (request.getSkuId().isEmpty()) {
            throw invalidArgument("sku_id is required");
        }
        if (!request.hasDate()) {
            throw invalidArgument("date is required");
        }

        LocalDate date = dateProtoMapper.toDomain(request.getDate());
        Money price = request.hasPrice() ? moneyProtoMapper.toDomain(request.getPrice()) : Money.cny(0, 0);

        SetDailyInventoryCommand command =
                new SetDailyInventoryCommand(request.getSkuId(), date, request.getTotalQuantity(), price);

        DailyInventory result = setDailyInventoryUseCase.execute(command);

        responseObserver.onNext(SetDailyInventoryResponse.newBuilder()
                .setInventory(dailyInventoryProtoMapper.toProto(result))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void batchSetDailyInventory(
            BatchSetDailyInventoryRequest request, StreamObserver<BatchSetDailyInventoryResponse> responseObserver) {
        if (request.getItemsList().isEmpty()) {
            throw invalidArgument("Items list is empty");
        }

        List<SetDailyInventoryCommand> commands = request.getItemsList().stream()
                .map(item -> {
                    LocalDate date = dateProtoMapper.toDomain(item.getDate());
                    Money price = item.hasPrice() ? moneyProtoMapper.toDomain(item.getPrice()) : Money.cny(0, 0);
                    return new SetDailyInventoryCommand(item.getSkuId(), date, item.getTotalQuantity(), price);
                })
                .toList();

        List<DailyInventory> results = batchSetDailyInventoryUseCase.execute(commands);

        responseObserver.onNext(BatchSetDailyInventoryResponse.newBuilder()
                .addAllInventories(dailyInventoryProtoMapper.toProtos(results))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void getDailyInventory(
            GetDailyInventoryRequest request, StreamObserver<GetDailyInventoryResponse> responseObserver) {
        if (request.getSkuId().isEmpty()) {
            throw invalidArgument("sku_id is required");
        }
        if (!request.hasDate()) {
            throw invalidArgument("date is required");
        }

        LocalDate date = dateProtoMapper.toDomain(request.getDate());
        DailyInventory result = getDailyInventoryUseCase.execute(request.getSkuId(), date);

        responseObserver.onNext(GetDailyInventoryResponse.newBuilder()
                .setInventory(dailyInventoryProtoMapper.toProto(result))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void queryInventoryCalendar(
            QueryInventoryCalendarRequest request, StreamObserver<QueryInventoryCalendarResponse> responseObserver) {
        if (request.getSkuId().isEmpty()) {
            throw invalidArgument("sku_id is required");
        }
        if (!request.hasStartDate() || !request.hasEndDate()) {
            throw invalidArgument("Both start_date and end_date are required");
        }

        LocalDate start = dateProtoMapper.toDomain(request.getStartDate());
        LocalDate end = dateProtoMapper.toDomain(request.getEndDate());

        List<DailyInventory> entries = queryInventoryCalendarUseCase.execute(request.getSkuId(), start, end);

        responseObserver.onNext(QueryInventoryCalendarResponse.newBuilder()
                .addAllEntries(dailyInventoryProtoMapper.toProtos(entries))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void checkAvailability(
            CheckAvailabilityRequest request, StreamObserver<CheckAvailabilityResponse> responseObserver) {
        if (request.getSkuId().isEmpty()) {
            throw invalidArgument("sku_id is required");
        }
        if (!request.hasDate()) {
            throw invalidArgument("date is required");
        }

        LocalDate date = dateProtoMapper.toDomain(request.getDate());
        CheckAvailabilityResult result =
                checkAvailabilityUseCase.execute(request.getSkuId(), date, request.getQuantity());

        responseObserver.onNext(CheckAvailabilityResponse.newBuilder()
                .setAvailable(result.available())
                .setAvailableQuantity(result.availableQuantity())
                .setPrice(moneyProtoMapper.toProto(result.price()))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void lockInventory(LockInventoryRequest request, StreamObserver<LockInventoryResponse> responseObserver) {
        if (request.getItemsList().isEmpty()) {
            throw invalidArgument("Lock items list is empty");
        }
        if (request.getOrderId().isEmpty()) {
            throw invalidArgument("order_id is required");
        }

        List<LockInventoryCommand.LockItemCommand> items = request.getItemsList().stream()
                .map(item -> new LockInventoryCommand.LockItemCommand(
                        item.getSkuId(), dateProtoMapper.toDomain(item.getDate()), item.getQuantity()))
                .toList();

        LockInventoryCommand command =
                new LockInventoryCommand(items, request.getOrderId(), request.getLockTimeoutSeconds());

        InventoryLock lock = lockInventoryUseCase.execute(command);

        responseObserver.onNext(LockInventoryResponse.newBuilder()
                .setLock(inventoryLockProtoMapper.toProto(lock))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void confirmLock(ConfirmLockRequest request, StreamObserver<ConfirmLockResponse> responseObserver) {
        if (request.getLockId().isEmpty()) {
            throw invalidArgument("lock_id is required");
        }

        InventoryLock lock = confirmLockUseCase.execute(request.getLockId());

        responseObserver.onNext(ConfirmLockResponse.newBuilder()
                .setLock(inventoryLockProtoMapper.toProto(lock))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void releaseLock(ReleaseLockRequest request, StreamObserver<ReleaseLockResponse> responseObserver) {
        if (request.getLockId().isEmpty()) {
            throw invalidArgument("lock_id is required");
        }

        InventoryLock lock = releaseLockUseCase.execute(request.getLockId(), request.getReason());

        responseObserver.onNext(ReleaseLockResponse.newBuilder()
                .setLock(inventoryLockProtoMapper.toProto(lock))
                .build());
        responseObserver.onCompleted();
    }

    private static StatusRuntimeException invalidArgument(String message) {
        return Status.INVALID_ARGUMENT.withDescription(message).asRuntimeException();
    }
}
