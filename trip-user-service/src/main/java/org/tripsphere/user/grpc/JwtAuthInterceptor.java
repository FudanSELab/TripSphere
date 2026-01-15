package org.tripsphere.user.grpc;

import org.springframework.beans.factory.annotation.Autowired;
import org.tripsphere.user.util.JwtUtil;

import io.grpc.*;

/**
 * gRPC interceptor for JWT authentication Extracts and validates JWT token from metadata and stores
 * username in context
 *
 * <p>NOTE: This interceptor is now deprecated in favor of Spring Security's
 * GrpcServerSecurityAutoConfiguration which uses JwtGrpcAuthenticationReader. This class is kept
 * for backward compatibility but can be removed if not needed.
 */
// @Component
// @GrpcGlobalServerInterceptor
@Deprecated
public class JwtAuthInterceptor implements ServerInterceptor {

    private static final String AUTHORIZATION_HEADER = "authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    @Autowired private JwtUtil jwtUtil;

    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
            ServerCall<ReqT, RespT> call, Metadata headers, ServerCallHandler<ReqT, RespT> next) {

        String username = null;
        String token = extractToken(headers);

        if (token != null) {
            try {
                // Validate token and extract username
                String extractedUsername = jwtUtil.extractUsername(token);
                if (extractedUsername != null && jwtUtil.validateToken(token, extractedUsername)) {
                    username = extractedUsername;
                }
            } catch (Exception e) {
                // Token validation failed, username remains null
                // For public endpoints like Register and Login, this is acceptable
            }
        }

        // Store username in context (may be null for unauthenticated requests)
        Context context = Context.current().withValue(ContextKeys.USERNAME_KEY, username);

        return Contexts.interceptCall(context, call, headers, next);
    }

    /* Extract JWT token from metadata authorization header */
    private String extractToken(Metadata headers) {
        String authHeader =
                headers.get(
                        Metadata.Key.of(AUTHORIZATION_HEADER, Metadata.ASCII_STRING_MARSHALLER));

        if (authHeader != null && authHeader.startsWith(BEARER_PREFIX)) {
            return authHeader.substring(BEARER_PREFIX.length()).trim();
        }

        return null;
    }
}
