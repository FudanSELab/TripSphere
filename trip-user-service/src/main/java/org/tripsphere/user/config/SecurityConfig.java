package org.tripsphere.user.config;

import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.ProviderManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

/**
 * Security configuration for this gRPC-only service. No Servlet container is present, so HTTP
 * security ({@code SecurityFilterChain}, {@code @EnableWebSecurity}) is not used. gRPC-level
 * security is handled by {@link org.tripsphere.user.security.JwtGrpcAuthenticationReader} and
 * {@link JwtAuthenticationProvider} via the grpc-spring-boot-starter security interceptor.
 */
@Configuration
@RequiredArgsConstructor
@EnableMethodSecurity(securedEnabled = true)
public class SecurityConfig {

    private final JwtAuthenticationProvider jwtAuthenticationProvider;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public AuthenticationManager authenticationManager(
            UserDetailsService userDetailsService, PasswordEncoder passwordEncoder) {
        // Add DAO authentication provider for email/password authentication
        DaoAuthenticationProvider daoAuthenticationProvider = new DaoAuthenticationProvider(userDetailsService);
        daoAuthenticationProvider.setPasswordEncoder(passwordEncoder);

        List<AuthenticationProvider> providers = List.of(jwtAuthenticationProvider, daoAuthenticationProvider);

        return new ProviderManager(providers);
    }
}
