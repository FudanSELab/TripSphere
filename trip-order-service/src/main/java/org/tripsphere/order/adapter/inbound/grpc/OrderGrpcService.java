package org.tripsphere.order.adapter.inbound.grpc;

import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import io.grpc.stub.StreamObserver;
import java.util.List;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.order.adapter.inbound.grpc.mapper.DateProtoMapper;
import org.tripsphere.order.adapter.inbound.grpc.mapper.OrderProtoMapper;
import org.tripsphere.order.application.dto.*;
import org.tripsphere.order.application.service.command.*;
import org.tripsphere.order.application.service.query.*;
import org.tripsphere.order.domain.model.ContactInfo;
import org.tripsphere.order.domain.model.Order;
import org.tripsphere.order.domain.model.OrderSource;
import org.tripsphere.order.domain.model.OrderStatus;
import org.tripsphere.order.domain.model.OrderType;
import org.tripsphere.order.v1.*;

@GrpcService
@RequiredArgsConstructor
public class OrderGrpcService extends OrderServiceGrpc.OrderServiceImplBase {

    private final CreateOrderUseCase createOrderUseCase;
    private final CancelOrderUseCase cancelOrderUseCase;
    private final ConfirmPaymentUseCase confirmPaymentUseCase;
    private final GetOrderUseCase getOrderUseCase;
    private final ListUserOrdersUseCase listUserOrdersUseCase;
    private final OrderProtoMapper orderProtoMapper;
    private final DateProtoMapper dateProtoMapper;

    @Override
    public void createOrder(CreateOrderRequest request, StreamObserver<CreateOrderResponse> responseObserver) {
        if (request.getUserId().isEmpty()) {
            throw invalidArgument("user_id is required");
        }
        if (request.getItemsList().isEmpty()) {
            throw invalidArgument("Order items list is empty");
        }
        for (CreateOrderItem item : request.getItemsList()) {
            if (item.getSkuId().isEmpty()) throw invalidArgument("items[].sku_id is required");
            if (!item.hasDate()) throw invalidArgument("items[].date is required");
            if (item.getQuantity() <= 0) throw invalidArgument("items[].quantity must be > 0");
        }

        List<CreateOrderItemCommand> items = request.getItemsList().stream()
                .map(item -> new CreateOrderItemCommand(
                        item.getSkuId(),
                        dateProtoMapper.toDomain(item.getDate()),
                        item.hasEndDate() ? dateProtoMapper.toDomain(item.getEndDate()) : null,
                        item.getQuantity()))
                .toList();

        ContactInfo contact = null;
        if (request.hasContact()) {
            contact = new ContactInfo(
                    request.getContact().getName(),
                    request.getContact().getPhone(),
                    request.getContact().getEmail());
        }

        OrderSource source = null;
        if (request.hasSource()) {
            source = new OrderSource(
                    request.getSource().getChannel(),
                    request.getSource().getAgentId(),
                    request.getSource().getSessionId());
        }

        CreateOrderCommand command = new CreateOrderCommand(request.getUserId(), items, contact, source);

        Order order = createOrderUseCase.execute(command);

        responseObserver.onNext(CreateOrderResponse.newBuilder()
                .setOrder(orderProtoMapper.toProto(order))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void getOrder(GetOrderRequest request, StreamObserver<GetOrderResponse> responseObserver) {
        if (request.getId().isEmpty()) {
            throw invalidArgument("id is required");
        }

        Order order = getOrderUseCase.execute(request.getId());

        responseObserver.onNext(GetOrderResponse.newBuilder()
                .setOrder(orderProtoMapper.toProto(order))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void listUserOrders(ListUserOrdersRequest request, StreamObserver<ListUserOrdersResponse> responseObserver) {
        if (request.getUserId().isEmpty()) {
            throw invalidArgument("user_id is required");
        }

        OrderStatus statusFilter = request.getStatus() != org.tripsphere.order.v1.OrderStatus.ORDER_STATUS_UNSPECIFIED
                ? orderProtoMapper.mapStatusToDomain(request.getStatus())
                : null;
        OrderType typeFilter = request.getType() != org.tripsphere.order.v1.OrderType.ORDER_TYPE_UNSPECIFIED
                ? orderProtoMapper.mapTypeToDomain(request.getType())
                : null;

        int page = 0;
        if (!request.getPageToken().isEmpty()) {
            try {
                page = Integer.parseInt(request.getPageToken());
            } catch (NumberFormatException ignored) {
            }
        }

        ListOrdersQuery query =
                new ListOrdersQuery(request.getUserId(), statusFilter, typeFilter, request.getPageSize(), page);

        OrderPage result = listUserOrdersUseCase.execute(query);

        ListUserOrdersResponse.Builder responseBuilder =
                ListUserOrdersResponse.newBuilder().addAllOrders(orderProtoMapper.toProtos(result.orders()));

        if (result.hasNext()) {
            responseBuilder.setNextPageToken(String.valueOf(result.currentPage() + 1));
        }

        responseObserver.onNext(responseBuilder.build());
        responseObserver.onCompleted();
    }

    @Override
    public void cancelOrder(CancelOrderRequest request, StreamObserver<CancelOrderResponse> responseObserver) {
        if (request.getOrderId().isEmpty()) {
            throw invalidArgument("order_id is required");
        }

        Order order = cancelOrderUseCase.execute(request.getOrderId(), request.getReason());

        responseObserver.onNext(CancelOrderResponse.newBuilder()
                .setOrder(orderProtoMapper.toProto(order))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void confirmPayment(ConfirmPaymentRequest request, StreamObserver<ConfirmPaymentResponse> responseObserver) {
        if (request.getOrderId().isEmpty()) {
            throw invalidArgument("order_id is required");
        }

        Order order = confirmPaymentUseCase.execute(request.getOrderId(), request.getPaymentMethod());

        responseObserver.onNext(ConfirmPaymentResponse.newBuilder()
                .setOrder(orderProtoMapper.toProto(order))
                .build());
        responseObserver.onCompleted();
    }

    private static StatusRuntimeException invalidArgument(String message) {
        return Status.INVALID_ARGUMENT.withDescription(message).asRuntimeException();
    }
}
