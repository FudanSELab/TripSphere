package org.tripsphere.user.grpc;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

/* JWT authentication token for Spring Security */
public class JwtAuthenticationToken extends AbstractAuthenticationToken {

    private final String token;
    private final String username;
    private final List<String> roles;

    public JwtAuthenticationToken(String token, String username, List<String> roles) {
        super(
                roles.stream()
                        .map(role -> role.startsWith("ROLE_") ? role : "ROLE_" + role)
                        .map(SimpleGrantedAuthority::new)
                        .collect(Collectors.toList()));
        this.token = token;
        this.username = username;
        this.roles = roles;
        setAuthenticated(true);
    }

    @Override
    public Object getCredentials() {
        return token;
    }

    @Override
    public Object getPrincipal() {
        return username;
    }

    public String getToken() {
        return token;
    }

    public String getUsername() {
        return username;
    }

    public List<String> getRoles() {
        return roles;
    }
}
