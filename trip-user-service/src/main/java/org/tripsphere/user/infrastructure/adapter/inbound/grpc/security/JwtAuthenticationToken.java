package org.tripsphere.user.infrastructure.adapter.inbound.grpc.security;

import java.util.Collection;
import java.util.List;
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

/** JWT authentication token for Spring Security. */
public class JwtAuthenticationToken extends AbstractAuthenticationToken {

    private final String token;
    private final String userId;
    private final String email;
    private final List<String> roles;

    /**
     * Create an unauthenticated token with only the raw JWT string. Used by {@link
     * JwtGrpcAuthenticationReader} to pass the token to the {@link
     * org.tripsphere.user.infrastructure.config.JwtAuthenticationProvider} for validation.
     *
     * @param token the raw JWT token string
     */
    public JwtAuthenticationToken(String token) {
        super(null);
        this.token = token;
        this.userId = null;
        this.email = null;
        this.roles = null;
        setAuthenticated(false);
    }

    /**
     * Create a fully authenticated token with user details and authorities. This constructor should
     * only be called by {@link
     * org.tripsphere.user.infrastructure.config.JwtAuthenticationProvider} after successful token
     * validation.
     */
    private JwtAuthenticationToken(
            String token,
            String userId,
            String email,
            List<String> roles,
            Collection<? extends GrantedAuthority> authorities) {
        super(authorities);
        this.token = token;
        this.userId = userId;
        this.email = email;
        this.roles = roles;
        setAuthenticated(true);
    }

    /**
     * Factory method to create an authenticated token. Should only be called by {@link
     * org.tripsphere.user.infrastructure.config.JwtAuthenticationProvider} after validating the JWT.
     */
    public static JwtAuthenticationToken authenticated(String token, String userId, String email, List<String> roles) {
        Collection<SimpleGrantedAuthority> authorities = roles.stream()
                .map(role -> role.startsWith("ROLE_") ? role : "ROLE_" + role)
                .map(SimpleGrantedAuthority::new)
                .toList();
        return new JwtAuthenticationToken(token, userId, email, roles, authorities);
    }

    @Override
    public Object getCredentials() {
        return token;
    }

    @Override
    public Object getPrincipal() {
        return userId;
    }

    public String getToken() {
        return token;
    }

    public String getUserId() {
        return userId;
    }

    public String getEmail() {
        return email;
    }

    public List<String> getRoles() {
        return roles;
    }
}
