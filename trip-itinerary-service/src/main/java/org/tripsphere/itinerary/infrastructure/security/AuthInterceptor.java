package org.tripsphere.itinerary.infrastructure.security;

import io.grpc.Context;
import io.grpc.Contexts;
import io.grpc.Metadata;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.interceptor.GrpcGlobalServerInterceptor;

@Slf4j
@GrpcGlobalServerInterceptor
public class AuthInterceptor implements ServerInterceptor {

    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
            ServerCall<ReqT, RespT> call, Metadata headers, ServerCallHandler<ReqT, RespT> next) {
        GrpcAuthContext authContext = GrpcAuthContext.fromMetadata(headers);

        if (authContext.isAuthenticated()) {
            log.debug(
                    "Authenticated request from user: {}, roles: {}", authContext.getUserId(), authContext.getRoles());
        } else {
            log.debug("Unauthenticated request");
        }

        Context context = authContext.attach(Context.current());
        return Contexts.interceptCall(context, call, headers, next);
    }
}
