package org.tripsphere.user.config;

import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.stereotype.Component;
import org.tripsphere.user.grpc.JwtAuthenticationToken;

/**
 * Authentication provider for JWT tokens
 */
@Component
public class JwtAuthenticationProvider implements AuthenticationProvider {

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        if (!(authentication instanceof JwtAuthenticationToken)) {
            return null;
        }

        JwtAuthenticationToken jwtAuth = (JwtAuthenticationToken) authentication;
        
        // Token validation is already done in JwtGrpcAuthenticationReader
        // Here we just return the authenticated token
        return jwtAuth;
    }

    @Override
    public boolean supports(Class<?> authentication) {
        return JwtAuthenticationToken.class.isAssignableFrom(authentication);
    }
}

