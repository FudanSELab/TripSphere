package org.tripsphere.user.security;

import java.util.Collection;
import java.util.stream.Collectors;
import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.tripsphere.user.model.Role;
import org.tripsphere.user.model.UserEntity;

/**
 * Custom {@link UserDetails} implementation that wraps {@link UserEntity}. By carrying the full
 * entity, the {@link org.tripsphere.user.service.impl.UserServiceImpl#signIn(String, String)}
 * method can retrieve user data directly from the {@link
 * org.springframework.security.core.Authentication#getPrincipal() Authentication principal} after a
 * successful {@link org.springframework.security.authentication.AuthenticationManager#authenticate
 * authenticate} call, eliminating the redundant second database query.
 */
public class CustomUserDetails implements UserDetails {

    /** The wrapped entity — available after successful authentication. */
    @Getter
    private final UserEntity userEntity;

    private final Collection<? extends GrantedAuthority> authorities;

    public CustomUserDetails(UserEntity userEntity) {
        this.userEntity = userEntity;
        this.authorities = userEntity.getRoles().stream()
                .map(Role::name)
                .map(name -> new SimpleGrantedAuthority("ROLE_" + name))
                .collect(Collectors.toList());
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    /** Returns the hashed password stored in the database. */
    @Override
    public String getPassword() {
        return userEntity.getPassword();
    }

    /** Returns the email address used as the login username. */
    @Override
    public String getUsername() {
        return userEntity.getEmail();
    }
}
