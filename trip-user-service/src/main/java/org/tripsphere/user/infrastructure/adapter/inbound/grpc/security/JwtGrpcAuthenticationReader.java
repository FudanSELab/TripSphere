package org.tripsphere.user.infrastructure.adapter.inbound.grpc.security;

import io.grpc.Metadata;
import io.grpc.ServerCall;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.security.authentication.GrpcAuthenticationReader;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.stereotype.Component;

/**
 * gRPC inbound adapter that extracts JWT token from metadata. This reader only extracts the raw
 * token and wraps it in an unauthenticated {@link JwtAuthenticationToken}. Actual token validation
 * is delegated to {@link org.tripsphere.user.infrastructure.config.JwtAuthenticationProvider} via
 * the {@link org.springframework.security.authentication.AuthenticationManager}.
 */
@Slf4j
@Component
public class JwtGrpcAuthenticationReader implements GrpcAuthenticationReader {

    private static final String AUTHORIZATION_HEADER = "authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    @Override
    public Authentication readAuthentication(ServerCall<?, ?> call, Metadata headers) throws AuthenticationException {
        String token = extractToken(headers);

        if (token == null) {
            return null; // No token provided, allow anonymous access
        }

        // Return an unauthenticated token; validation is handled by JwtAuthenticationProvider
        return new JwtAuthenticationToken(token);
    }

    /** Extract JWT token from metadata authorization header. */
    private String extractToken(Metadata headers) {
        String authHeader = headers.get(Metadata.Key.of(AUTHORIZATION_HEADER, Metadata.ASCII_STRING_MARSHALLER));

        if (authHeader != null && authHeader.startsWith(BEARER_PREFIX)) {
            return authHeader.substring(BEARER_PREFIX.length()).trim();
        }

        return null;
    }
}
