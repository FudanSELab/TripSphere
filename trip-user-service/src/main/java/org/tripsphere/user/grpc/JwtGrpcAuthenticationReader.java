package org.tripsphere.user.grpc;

import io.grpc.Metadata;
import io.grpc.ServerCall;
import net.devh.boot.grpc.server.security.authentication.GrpcAuthenticationReader;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.stereotype.Component;
import org.tripsphere.user.util.JwtUtil;

/**
 * gRPC authentication reader that extracts JWT token from metadata
 * and creates Authentication object for Spring Security
 */
@Component
public class JwtGrpcAuthenticationReader implements GrpcAuthenticationReader {

    private static final String AUTHORIZATION_HEADER = "authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    @Autowired
    private JwtUtil jwtUtil;

    @Override
    public Authentication readAuthentication(ServerCall<?, ?> call, Metadata headers) throws AuthenticationException {
        String token = extractToken(headers);
        
        if (token == null) {
            return null; // No authentication provided, allow anonymous access
        }

        try {
            // Validate token and extract username
            String username = jwtUtil.extractUsername(token);
            if (username == null || !jwtUtil.validateToken(token, username)) {
                throw new BadCredentialsException("Invalid JWT token");
            }

            // Extract roles from token
            java.util.List<String> roles = jwtUtil.extractRoles(token);

            // Create JWT authentication token (already authenticated)
            JwtAuthenticationToken jwtAuth = new JwtAuthenticationToken(token, username, roles);
            
            // Return the authenticated token directly
            // The JwtAuthenticationProvider will handle it if needed
            return jwtAuth;
        } catch (Exception e) {
            throw new BadCredentialsException("Failed to authenticate JWT token: " + e.getMessage(), e);
        }
    }

    /**
     * Extract JWT token from metadata authorization header
     */
    private String extractToken(Metadata headers) {
        String authHeader = headers.get(Metadata.Key.of(AUTHORIZATION_HEADER, Metadata.ASCII_STRING_MARSHALLER));
        
        if (authHeader != null && authHeader.startsWith(BEARER_PREFIX)) {
            return authHeader.substring(BEARER_PREFIX.length()).trim();
        }
        
        return null;
    }
}

