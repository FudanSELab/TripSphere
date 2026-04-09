package org.tripsphere.user.application.service.command;

import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.AuthenticationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.user.application.dto.SignInCommand;
import org.tripsphere.user.application.dto.SignInResult;
import org.tripsphere.user.application.exception.NotFoundException;
import org.tripsphere.user.application.exception.UnauthenticatedException;
import org.tripsphere.user.application.port.TokenPort;
import org.tripsphere.user.application.port.UserRepository;
import org.tripsphere.user.application.service.UserValidator;
import org.tripsphere.user.domain.model.Role;
import org.tripsphere.user.domain.model.User;

@Slf4j
@Service
@RequiredArgsConstructor
public class SignInUseCase {

    private final AuthenticationManager authenticationManager;
    private final UserRepository userRepository;
    private final TokenPort tokenPort;
    private final UserValidator userValidator;

    @Transactional(readOnly = true)
    public SignInResult execute(SignInCommand command) {
        log.debug("User sign in attempt: {}", command.email());

        userValidator.validateEmail(command.email());
        userValidator.validatePasswordNotEmpty(command.password());

        try {
            authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(command.email(), command.password()));
        } catch (AuthenticationException e) {
            log.warn("Sign in failed: invalid credentials - email: {}", command.email());
            throw UnauthenticatedException.invalidCredentials();
        }

        User user = userRepository
                .findByEmail(command.email())
                .orElseThrow(() -> new NotFoundException("User", command.email()));

        List<String> rolesList = user.getRoles().stream().map(Role::name).toList();
        String token = tokenPort.generateToken(user.getId(), user.getName(), user.getEmail(), rolesList);

        log.info(
                "User sign in successful - email: {}, userId: {}, roles: {}", command.email(), user.getId(), rolesList);

        return new SignInResult(user.getId(), user.getName(), user.getEmail(), rolesList, token);
    }
}
