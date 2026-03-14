package org.tripsphere.order.api.grpc;

import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.springframework.data.domain.Page;
import org.tripsphere.order.exception.InvalidArgumentException;
import org.tripsphere.order.exception.NotFoundException;
import org.tripsphere.order.service.OrderService;
import org.tripsphere.order.v1.*;

@GrpcService
@RequiredArgsConstructor
public class OrderGrpcService extends OrderServiceGrpc.OrderServiceImplBase {

    private final OrderService orderService;

    @Override
    public void createOrder(
            CreateOrderRequest request, StreamObserver<CreateOrderResponse> responseObserver) {
        if (request.getUserId().isEmpty()) {
            throw InvalidArgumentException.required("user_id");
        }
        if (request.getItemsList().isEmpty()) {
            throw new InvalidArgumentException("Order items list is empty");
        }

        // Validate items
        for (CreateOrderItem item : request.getItemsList()) {
            if (item.getSkuId().isEmpty()) {
                throw InvalidArgumentException.required("items[].sku_id");
            }
            if (!item.hasDate()) {
                throw InvalidArgumentException.required("items[].date");
            }
            if (item.getQuantity() <= 0) {
                throw InvalidArgumentException.invalid("items[].quantity", "must be > 0");
            }
        }

        Order order =
                orderService.createOrder(
                        request.getUserId(),
                        request.getItemsList(),
                        request.hasContact() ? request.getContact() : null,
                        request.hasSource() ? request.getSource() : null);

        responseObserver.onNext(CreateOrderResponse.newBuilder().setOrder(order).build());
        responseObserver.onCompleted();
    }

    @Override
    public void getOrder(
            GetOrderRequest request, StreamObserver<GetOrderResponse> responseObserver) {
        if (request.getId().isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        Order order =
                orderService
                        .getOrder(request.getId())
                        .orElseThrow(() -> new NotFoundException("Order", request.getId()));

        responseObserver.onNext(GetOrderResponse.newBuilder().setOrder(order).build());
        responseObserver.onCompleted();
    }

    @Override
    public void listUserOrders(
            ListUserOrdersRequest request,
            StreamObserver<ListUserOrdersResponse> responseObserver) {
        if (request.getUserId().isEmpty()) {
            throw InvalidArgumentException.required("user_id");
        }

        OrderStatus statusFilter =
                request.getStatus() != OrderStatus.ORDER_STATUS_UNSPECIFIED
                        ? request.getStatus()
                        : null;
        OrderType typeFilter =
                request.getType() != OrderType.ORDER_TYPE_UNSPECIFIED ? request.getType() : null;

        Page<Order> page =
                orderService.listUserOrders(
                        request.getUserId(),
                        statusFilter,
                        typeFilter,
                        request.getPageSize(),
                        request.getPageToken());

        ListUserOrdersResponse.Builder responseBuilder =
                ListUserOrdersResponse.newBuilder().addAllOrders(page.getContent());

        if (page.hasNext()) {
            responseBuilder.setNextPageToken(String.valueOf(page.getNumber() + 1));
        }

        responseObserver.onNext(responseBuilder.build());
        responseObserver.onCompleted();
    }

    @Override
    public void cancelOrder(
            CancelOrderRequest request, StreamObserver<CancelOrderResponse> responseObserver) {
        if (request.getOrderId().isEmpty()) {
            throw InvalidArgumentException.required("order_id");
        }

        Order order = orderService.cancelOrder(request.getOrderId(), request.getReason());

        responseObserver.onNext(CancelOrderResponse.newBuilder().setOrder(order).build());
        responseObserver.onCompleted();
    }

    @Override
    public void confirmPayment(
            ConfirmPaymentRequest request,
            StreamObserver<ConfirmPaymentResponse> responseObserver) {
        if (request.getOrderId().isEmpty()) {
            throw InvalidArgumentException.required("order_id");
        }

        Order order = orderService.confirmPayment(request.getOrderId(), request.getPaymentMethod());

        responseObserver.onNext(ConfirmPaymentResponse.newBuilder().setOrder(order).build());
        responseObserver.onCompleted();
    }
}
