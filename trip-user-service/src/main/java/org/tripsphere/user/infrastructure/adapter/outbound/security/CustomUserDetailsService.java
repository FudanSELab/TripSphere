package org.tripsphere.user.infrastructure.adapter.outbound.security;

import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.user.application.port.UserRepository;

@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    /**
     * Loads the user by email and wraps the domain {@link org.tripsphere.user.domain.model.User} in
     * a {@link CustomUserDetails}. This allows callers to retrieve the domain object directly from
     * the {@link org.springframework.security.core.Authentication#getPrincipal() Authentication
     * principal} after a successful authentication, avoiding a redundant second database query.
     */
    @Override
    @Transactional(readOnly = true)
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        return userRepository
                .findByEmail(email)
                .map(CustomUserDetails::new)
                .orElseThrow(() -> new UsernameNotFoundException("User not found: " + email));
    }
}
