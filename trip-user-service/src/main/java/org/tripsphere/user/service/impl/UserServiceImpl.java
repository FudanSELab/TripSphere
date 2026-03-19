package org.tripsphere.user.service.impl;

import java.util.List;
import java.util.Optional;
import java.util.regex.Pattern;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.user.exception.AlreadyExistsException;
import org.tripsphere.user.exception.InvalidArgumentException;
import org.tripsphere.user.exception.UnauthenticatedException;
import org.tripsphere.user.mapper.UserMapper;
import org.tripsphere.user.model.Role;
import org.tripsphere.user.model.UserEntity;
import org.tripsphere.user.repository.UserEntityRepository;
import org.tripsphere.user.security.CustomUserDetails;
import org.tripsphere.user.service.UserService;
import org.tripsphere.user.util.JwtUtil;
import org.tripsphere.user.v1.User;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    // Email pattern: basic email validation
    private static final Pattern EMAIL_PATTERN = Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$");

    // Password pattern: at least 8 characters, must contain a letter, a number, and a special
    // character
    private static final Pattern PASSWORD_PATTERN =
            Pattern.compile("^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[^a-zA-Z0-9]).{8,}$");

    private final UserEntityRepository userEntityRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final AuthenticationManager authenticationManager;
    private final UserMapper userMapper;

    @Override
    @Transactional
    public void signUp(String name, String email, String password) {
        log.debug("Signing up user with email: {}", email);

        validateName(name);
        validateEmail(email);
        validatePassword(password);

        if (userEntityRepository.existsByEmail(email)) {
            log.warn("Sign up failed: email already exists - {}", email);
            throw new AlreadyExistsException("Email", email);
        }

        UserEntity user = new UserEntity();
        user.setName(name);
        user.setEmail(email);
        user.setPassword(passwordEncoder.encode(password));
        user.getRoles().add(Role.USER);

        userEntityRepository.save(user);
        log.info("User signed up successfully - email: {}, userId: {}", email, user.getId());
    }

    @Override
    @Transactional(readOnly = true)
    public SignInResult signIn(String email, String password) {
        log.debug("User sign in attempt: {}", email);

        validateEmail(email);
        validatePasswordNotEmpty(password);

        final Authentication authenticated;
        try {
            authenticated =
                    authenticationManager.authenticate(new UsernamePasswordAuthenticationToken(email, password));
        } catch (AuthenticationException e) {
            log.warn("Sign in failed: invalid credentials - email: {}", email);
            throw UnauthenticatedException.invalidCredentials();
        }

        // Extract the entity directly from the Authentication principal — no second DB query.
        // DaoAuthenticationProvider sets the principal to the UserDetails returned by
        // CustomUserDetailsService, which is always a CustomUserDetails wrapping UserEntity.
        UserEntity userEntity = ((CustomUserDetails) authenticated.getPrincipal()).getUserEntity();

        List<String> rolesList = userEntity.getRoles().stream().map(Role::name).toList();
        String token = jwtUtil.generateToken(userEntity.getId(), userEntity.getName(), email, rolesList);

        User user = userMapper.toProto(userEntity);
        log.info("User sign in successful - email: {}, userId: {}, roles: {}", email, userEntity.getId(), rolesList);

        return new SignInResult(user, token);
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<User> findByEmail(String email) {
        log.debug("Finding user by email: {}", email);
        return userEntityRepository.findByEmail(email).map(userMapper::toProto);
    }

    private void validateName(String name) {
        if (name == null || name.trim().isEmpty()) {
            throw InvalidArgumentException.empty("Name");
        }
    }

    private void validateEmail(String email) {
        if (email == null || email.trim().isEmpty()) {
            throw InvalidArgumentException.empty("Email");
        }
        if (!EMAIL_PATTERN.matcher(email).matches()) {
            throw InvalidArgumentException.invalid("Email", "must be a valid email address");
        }
    }

    private void validatePassword(String password) {
        validatePassword(password, "Password");
    }

    private void validatePassword(String password, String fieldName) {
        if (password == null || password.trim().isEmpty()) {
            throw InvalidArgumentException.empty(fieldName);
        }
        if (!PASSWORD_PATTERN.matcher(password).matches()) {
            throw InvalidArgumentException.invalid(
                    fieldName,
                    "must be at least 8 characters and contain at least one letter, one number, and"
                            + " one special character");
        }
    }

    private void validatePasswordNotEmpty(String password) {
        validatePasswordNotEmpty(password, "Password");
    }

    private void validatePasswordNotEmpty(String password, String fieldName) {
        if (password == null || password.trim().isEmpty()) {
            throw InvalidArgumentException.empty(fieldName);
        }
    }
}
