package org.tripsphere.user.config;

import io.jsonwebtoken.JwtException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.stereotype.Component;
import org.tripsphere.user.security.JwtAuthenticationToken;
import org.tripsphere.user.util.JwtUtil;

/**
 * Authentication provider for JWT tokens. Validates the raw JWT token and creates a fully
 * authenticated {@link JwtAuthenticationToken} with user details and granted authorities.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationProvider implements AuthenticationProvider {

    private final JwtUtil jwtUtil;

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        if (!(authentication instanceof JwtAuthenticationToken jwtAuth)) {
            return null;
        }

        String token = jwtAuth.getToken();

        try {
            // Single parse: validate signature + expiration and extract all claims at once
            JwtUtil.TokenClaims claims = jwtUtil.parseAndValidate(token);
            return JwtAuthenticationToken.authenticated(token, claims.userId(), claims.email(), claims.roles());
        } catch (JwtException | IllegalArgumentException e) {
            log.debug("JWT token validation failed: {}", e.getMessage());
            throw new BadCredentialsException("Invalid or expired JWT token", e);
        }
    }

    @Override
    public boolean supports(Class<?> authentication) {
        return JwtAuthenticationToken.class.isAssignableFrom(authentication);
    }
}
