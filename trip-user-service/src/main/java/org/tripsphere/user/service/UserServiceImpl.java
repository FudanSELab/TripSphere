package org.tripsphere.user.service;

import io.grpc.Status;
import io.grpc.stub.StreamObserver;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.user.grpc.JwtAuthenticationToken;
import org.tripsphere.user.model.Role;
import org.tripsphere.user.model.UserEntity;
import org.tripsphere.user.repository.UserRepository;
import org.tripsphere.user.util.JwtUtil;
import org.tripsphere.user.RegisterRequest;
import org.tripsphere.user.RegisterResponse;
import org.tripsphere.user.LoginRequest;
import org.tripsphere.user.LoginResponse;
import org.tripsphere.user.ChangePasswordRequest;
import org.tripsphere.user.ChangePasswordResponse;
import org.tripsphere.user.GetCurrentUserRequest;
import org.tripsphere.user.GetCurrentUserResponse;
import org.tripsphere.user.User;
import java.util.regex.Pattern;
import lombok.extern.slf4j.Slf4j;

@Service
@GrpcService
@Slf4j
public class UserServiceImpl extends org.tripsphere.user.UserServiceGrpc.UserServiceImplBase {

    // Username pattern: allows letters, numbers, and underscores
    private static final Pattern USERNAME_PATTERN = Pattern.compile("^[a-zA-Z0-9_]+$");

    // Password pattern: at least 6 characters, only letters and numbers
    private static final Pattern PASSWORD_PATTERN = Pattern.compile("^[a-zA-Z0-9]{6,}$");

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private AuthenticationManager authenticationManager;

    @Override
    public void register(RegisterRequest request,
            StreamObserver<RegisterResponse> responseObserver) {
        log.debug("Starting user registration request");
        try {
            String username = request.getUsername();
            String password = request.getPassword();

            log.debug("Registration request - username: {}", username);

            // Validate username and password
            if (username == null || username.trim().isEmpty()) {
                log.warn("Registration failed: username is empty");
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription("Username cannot be empty")
                        .asRuntimeException());
                return;
            }

            // Validate username format: allows letters, numbers, and underscores
            if (!USERNAME_PATTERN.matcher(username).matches()) {
                log.warn("Registration failed: invalid username format - {}", username);
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription(
                                "Username can only contain letters, numbers, and underscores")
                        .asRuntimeException());
                return;
            }

            if (password == null || password.trim().isEmpty()) {
                log.warn("Registration failed: password is empty - username: {}", username);
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription("Password cannot be empty")
                        .asRuntimeException());
                return;
            }

            // Validate password format: at least 6 characters, only letters and numbers
            if (!PASSWORD_PATTERN.matcher(password).matches()) {
                log.warn("Registration failed: invalid password format - username: {}", username);
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription(
                                "Password must be at least 6 characters and can only contain letters and numbers")
                        .asRuntimeException());
                return;
            }

            // Check if username already exists
            if (userRepository.existsByUsername(username)) {
                log.warn("Registration failed: username already exists - {}", username);
                responseObserver.onError(Status.ALREADY_EXISTS
                        .withDescription("Username already exists")
                        .asRuntimeException());
                return;
            }

            // Create new user with default role USER
            UserEntity user = new UserEntity();
            user.setUsername(username);
            user.setPassword(passwordEncoder.encode(password));
            user.getRoles().add(Role.USER);

            userRepository.save(user);
            log.info("User registration successful - username: {}, userId: {}", username, user.getId());

            responseObserver.onNext(RegisterResponse.newBuilder().build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("User registration exception - username: {}", request.getUsername(), e);
            responseObserver.onError(Status.INTERNAL
                    .withDescription("Registration failed: " + e.getMessage())
                    .asRuntimeException());
        }
    }

    @Override
    public void login(LoginRequest request,
            StreamObserver<LoginResponse> responseObserver) {
        log.debug("Starting user login request");
        try {
            String username = request.getUsername();
            String password = request.getPassword();

            log.debug("Login request - username: {}", username);

            // Validate username and password
            if (username == null || username.trim().isEmpty()) {
                log.warn("Login failed: username is empty");
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription("Username cannot be empty")
                        .asRuntimeException());
                return;
            }

            // Validate username format: allows letters, numbers, and underscores
            if (!USERNAME_PATTERN.matcher(username).matches()) {
                log.warn("Login failed: invalid username format - {}", username);
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription(
                                "Username can only contain letters, numbers, and underscores")
                        .asRuntimeException());
                return;
            }

            if (password == null || password.trim().isEmpty()) {
                log.warn("Login failed: password is empty - username: {}", username);
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription("Password cannot be empty")
                        .asRuntimeException());
                return;
            }

            // Authenticate user credentials
            try {
                authenticationManager.authenticate(
                        new UsernamePasswordAuthenticationToken(username, password));
            } catch (Exception e) {
                log.warn("Login failed: invalid username or password - username: {}", username);
                responseObserver.onError(Status.UNAUTHENTICATED
                        .withDescription("Invalid username or password")
                        .asRuntimeException());
                return;
            }

            // Get user information
            UserEntity user = userRepository.findByUsername(username)
                    .orElseThrow(() -> new RuntimeException("User not found"));

            // Generate JWT token with roles array
            java.util.List<String> rolesList = user.getRoles().stream()
                    .map(Role::name)
                    .collect(java.util.stream.Collectors.toList());
            String token = jwtUtil.generateToken(username, rolesList);

            log.info("User login successful - username: {}, userId: {}, roles: {}", username, user.getId(),
                    rolesList);

            LoginResponse response = LoginResponse.newBuilder()
                    .setUser(User.newBuilder()
                            .setId(user.getId())
                            .setUsername(user.getUsername())
                            .addAllRoles(rolesList)
                            .build())
                    .setToken(token)
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("User login exception - username: {}", request.getUsername(), e);
            responseObserver.onError(Status.INTERNAL
                    .withDescription("Login failed: " + e.getMessage())
                    .asRuntimeException());
        }
    }

    @Override
    public void changePassword(ChangePasswordRequest request,
            StreamObserver<ChangePasswordResponse> responseObserver) {
        log.debug("Starting change password request");
        try {
            String username = request.getUsername();
            String oldPassword = request.getOldPassword();
            String newPassword = request.getNewPassword();

            log.debug("Change password request - username: {}", username);

            // Validate input
            if (username == null || username.trim().isEmpty()) {
                log.warn("Change password failed: username is empty");
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription("Username cannot be empty")
                        .asRuntimeException());
                return;
            }

            if (oldPassword == null || oldPassword.trim().isEmpty()) {
                log.warn("Change password failed: old password is empty - username: {}", username);
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription("Old password cannot be empty")
                        .asRuntimeException());
                return;
            }

            if (newPassword == null || newPassword.trim().isEmpty()) {
                log.warn("Change password failed: new password is empty - username: {}", username);
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription("New password cannot be empty")
                        .asRuntimeException());
                return;
            }

            // Validate new password format: at least 6 characters, only letters and numbers
            if (!PASSWORD_PATTERN.matcher(newPassword).matches()) {
                log.warn("Change password failed: invalid new password format - username: {}",
                        username);
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription(
                                "New password must be at least 6 characters and can only contain letters and numbers")
                        .asRuntimeException());
                return;
            }

            // Get user
            UserEntity user = userRepository.findByUsername(username)
                    .orElseThrow(() -> new RuntimeException("User not found"));

            // Verify old password
            if (!passwordEncoder.matches(oldPassword, user.getPassword())) {
                log.warn("Change password failed: invalid old password - username: {}", username);
                responseObserver.onError(Status.UNAUTHENTICATED
                        .withDescription("Invalid old password")
                        .asRuntimeException());
                return;
            }

            // Update password
            user.setPassword(passwordEncoder.encode(newPassword));
            userRepository.save(user);
            log.info("Password change successful - username: {}, userId: {}", username, user.getId());

            responseObserver.onNext(ChangePasswordResponse.newBuilder().build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("Change password exception - username: {}", request.getUsername(), e);
            responseObserver.onError(Status.INTERNAL
                    .withDescription("Change password failed: " + e.getMessage())
                    .asRuntimeException());
        }
    }

    @Override
    public void getCurrentUser(GetCurrentUserRequest request,
            StreamObserver<GetCurrentUserResponse> responseObserver) {
        log.debug("Starting get current user request");
        try {
            // Get authentication from Spring Security context
            Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

            if (authentication == null || !authentication.isAuthenticated()
                    || !(authentication instanceof JwtAuthenticationToken)) {
                log.warn("Get current user failed: not authenticated");
                responseObserver.onError(Status.UNAUTHENTICATED
                        .withDescription("Authentication required")
                        .asRuntimeException());
                return;
            }

            JwtAuthenticationToken jwtAuth = (JwtAuthenticationToken) authentication;
            String username = jwtAuth.getUsername();

            if (username == null || username.trim().isEmpty()) {
                log.warn("Get current user failed: username is empty");
                responseObserver.onError(Status.UNAUTHENTICATED
                        .withDescription("Authentication required")
                        .asRuntimeException());
                return;
            }

            log.debug("Get current user info - username: {}", username);

            // Get user from database
            UserEntity userEntity = userRepository.findByUsername(username)
                    .orElseThrow(() -> new RuntimeException("User not found"));

            // Convert UserEntity to proto User message
            User.Builder userBuilder = User.newBuilder()
                    .setId(userEntity.getId())
                    .setUsername(userEntity.getUsername());

            // Add roles
            for (Role role : userEntity.getRoles()) {
                userBuilder.addRoles(role.name());
            }

            // Build response
            GetCurrentUserResponse response = GetCurrentUserResponse.newBuilder()
                    .setUser(userBuilder.build())
                    .build();

            log.info("Get current user successful - username: {}, userId: {}", username,
                    userEntity.getId());
            responseObserver.onNext(response);
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("Get current user exception", e);
            responseObserver.onError(Status.INTERNAL
                    .withDescription("Get current user failed: " + e.getMessage())
                    .asRuntimeException());
        }
    }
}
