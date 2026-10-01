package org.tripsphere.order.infrastructure.observability;

import io.grpc.Context;
import io.grpc.Contexts;
import io.grpc.ForwardingServerCallListener;
import io.grpc.Metadata;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;
import net.devh.boot.grpc.server.interceptor.GrpcGlobalServerInterceptor;

@GrpcGlobalServerInterceptor
public class CorrelationServerInterceptor implements ServerInterceptor {

    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
            ServerCall<ReqT, RespT> call, Metadata headers, ServerCallHandler<ReqT, RespT> next) {
        String requestId = CorrelationContext.requestIdFromMetadata(headers);
        Context context = CorrelationContext.attach(Context.current(), requestId);
        ServerCall.Listener<ReqT> listener = Contexts.interceptCall(context, call, headers, next);

        return new ForwardingServerCallListener.SimpleForwardingServerCallListener<>(listener) {
            @Override
            public void onMessage(ReqT message) {
                withCorrelation(() -> super.onMessage(message));
            }

            @Override
            public void onHalfClose() {
                withCorrelation(super::onHalfClose);
            }

            @Override
            public void onCancel() {
                withCorrelation(super::onCancel);
            }

            @Override
            public void onComplete() {
                withCorrelation(super::onComplete);
            }

            @Override
            public void onReady() {
                withCorrelation(super::onReady);
            }

            private void withCorrelation(Runnable operation) {
                try (CorrelationContext.Scope ignored = CorrelationContext.openMdc(requestId)) {
                    operation.run();
                }
            }
        };
    }
}
