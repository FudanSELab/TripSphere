package org.tripsphere.user.infrastructure.adapter.outbound.security;

import java.util.Collection;
import java.util.stream.Collectors;
import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.tripsphere.user.domain.model.Role;
import org.tripsphere.user.domain.model.User;

/**
 * Custom {@link UserDetails} implementation that wraps the domain {@link User}. By carrying the
 * full domain object, the {@link
 * org.tripsphere.user.application.service.command.SignInUseCase#execute(
 * org.tripsphere.user.application.dto.SignInCommand) SignInUseCase} can retrieve user data directly
 * from the {@link org.springframework.security.core.Authentication#getPrincipal() Authentication
 * principal} after a successful authenticate call, eliminating a redundant second database query.
 */
public class CustomUserDetails implements UserDetails {

    /** The wrapped domain entity — available after successful authentication. */
    @Getter
    private final User user;

    private final Collection<? extends GrantedAuthority> authorities;

    public CustomUserDetails(User user) {
        this.user = user;
        this.authorities = user.getRoles().stream()
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
        return user.getPassword();
    }

    /** Returns the email address used as the login username. */
    @Override
    public String getUsername() {
        return user.getEmail();
    }
}
