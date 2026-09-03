package org.tripsphere.order.infrastructure.security;

import io.grpc.Context;
import io.grpc.Metadata;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class GrpcAuthContext {

    private static final Context.Key<GrpcAuthContext> AUTH_CONTEXT_KEY = Context.key("auth-context");

    private static final Metadata.Key<String> USER_ID_KEY =
            Metadata.Key.of("x-user-id", Metadata.ASCII_STRING_MARSHALLER);
    private static final Metadata.Key<String> USER_ROLES_KEY =
            Metadata.Key.of("x-user-roles", Metadata.ASCII_STRING_MARSHALLER);
    private static final Metadata.Key<String> AUTHORIZATION_KEY =
            Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER);

    private final String userId;
    private final List<String> roles;
    private final String token;

    public static GrpcAuthContext fromMetadata(Metadata metadata) {
        if (metadata == null) return anonymous();

        String rolesValue = metadata.get(USER_ROLES_KEY);
        List<String> roles = Collections.emptyList();
        if (rolesValue != null && !rolesValue.isBlank()) {
            roles = Arrays.stream(rolesValue.split(","))
                    .map(String::trim)
                    .filter(role -> !role.isEmpty())
                    .toList();
        }

        return GrpcAuthContext.builder()
                .userId(metadata.get(USER_ID_KEY))
                .roles(roles)
                .token(metadata.get(AUTHORIZATION_KEY))
                .build();
    }

    public static GrpcAuthContext anonymous() {
        return GrpcAuthContext.builder().roles(Collections.emptyList()).build();
    }

    public static GrpcAuthContext current() {
        GrpcAuthContext context = AUTH_CONTEXT_KEY.get();
        return context != null ? context : anonymous();
    }

    public Context attach(Context context) {
        return context.withValue(AUTH_CONTEXT_KEY, this);
    }

    public boolean isAuthenticated() {
        return userId != null && !userId.isBlank();
    }
}
