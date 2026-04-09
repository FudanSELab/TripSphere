package org.tripsphere.user.application.service.command;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.user.application.dto.SignUpCommand;
import org.tripsphere.user.application.exception.AlreadyExistsException;
import org.tripsphere.user.application.port.UserRepository;
import org.tripsphere.user.application.service.UserValidator;
import org.tripsphere.user.domain.model.Role;
import org.tripsphere.user.domain.model.User;

@Slf4j
@Service
@RequiredArgsConstructor
public class SignUpUseCase {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final UserValidator userValidator;

    @Transactional
    public void execute(SignUpCommand command) {
        log.debug("Signing up user with email: {}", command.email());

        userValidator.validateName(command.name());
        userValidator.validateEmail(command.email());
        userValidator.validatePassword(command.password());

        if (userRepository.existsByEmail(command.email())) {
            log.warn("Sign up failed: email already exists - {}", command.email());
            throw new AlreadyExistsException("Email", command.email());
        }

        User user = new User();
        user.setName(command.name());
        user.setEmail(command.email());
        user.setPassword(passwordEncoder.encode(command.password()));
        user.getRoles().add(Role.USER);

        User saved = userRepository.save(user);
        log.info("User signed up successfully - email: {}, userId: {}", command.email(), saved.getId());
    }
}
