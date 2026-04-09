package org.tripsphere.itinerary.infrastructure.security;

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

    public static final String ROLE_ADMIN = "ADMIN";
    public static final String ROLE_USER = "USER";

    private final String userId;
    private final List<String> roles;
    private final String token;

    public static GrpcAuthContext fromMetadata(Metadata metadata) {
        if (metadata == null) return anonymous();

        String userId = metadata.get(USER_ID_KEY);
        String rolesStr = metadata.get(USER_ROLES_KEY);
        String token = metadata.get(AUTHORIZATION_KEY);

        List<String> roles = Collections.emptyList();
        if (rolesStr != null && !rolesStr.isEmpty()) {
            roles = Arrays.asList(rolesStr.split(","));
        }

        return GrpcAuthContext.builder()
                .userId(userId)
                .roles(roles)
                .token(token)
                .build();
    }

    public static GrpcAuthContext anonymous() {
        return GrpcAuthContext.builder()
                .userId(null)
                .roles(Collections.emptyList())
                .token(null)
                .build();
    }

    public static GrpcAuthContext current() {
        GrpcAuthContext ctx = AUTH_CONTEXT_KEY.get();
        return ctx != null ? ctx : anonymous();
    }

    public Context attach(Context context) {
        return context.withValue(AUTH_CONTEXT_KEY, this);
    }

    public boolean isAuthenticated() {
        return userId != null && !userId.isEmpty();
    }

    public boolean hasRole(String role) {
        return roles != null && roles.contains(role);
    }

    public boolean isAdmin() {
        return hasRole(ROLE_ADMIN);
    }
}
