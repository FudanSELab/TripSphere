package org.tripsphere.user.api.grpc;

import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.springframework.security.access.annotation.Secured;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.tripsphere.user.exception.NotFoundException;
import org.tripsphere.user.security.JwtAuthenticationToken;
import org.tripsphere.user.service.UserService;
import org.tripsphere.user.v1.GetCurrentUserRequest;
import org.tripsphere.user.v1.GetCurrentUserResponse;
import org.tripsphere.user.v1.SignInRequest;
import org.tripsphere.user.v1.SignInResponse;
import org.tripsphere.user.v1.SignUpRequest;
import org.tripsphere.user.v1.SignUpResponse;
import org.tripsphere.user.v1.User;
import org.tripsphere.user.v1.UserServiceGrpc;

@GrpcService
@RequiredArgsConstructor
public class UserGrpcService extends UserServiceGrpc.UserServiceImplBase {

    private final UserService userService;

    /** Public endpoint — no authentication required. */
    @Override
    public void signUp(SignUpRequest request, StreamObserver<SignUpResponse> responseObserver) {
        String name = request.getName();
        String email = request.getEmail();
        String password = request.getPassword();

        userService.signUp(name, email, password);

        responseObserver.onNext(SignUpResponse.newBuilder().build());
        responseObserver.onCompleted();
    }

    /** Public endpoint — no authentication required. */
    @Override
    public void signIn(SignInRequest request, StreamObserver<SignInResponse> responseObserver) {
        String email = request.getEmail();
        String password = request.getPassword();

        UserService.SignInResult result = userService.signIn(email, password);

        SignInResponse response = SignInResponse.newBuilder()
                .setUser(result.user())
                .setToken(result.token())
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    /** Protected endpoint — requires an authenticated user with ROLE_USER. */
    @Override
    @Secured({"ROLE_USER"})
    public void getCurrentUser(GetCurrentUserRequest request, StreamObserver<GetCurrentUserResponse> responseObserver) {
        Authentication rawAuth = SecurityContextHolder.getContext().getAuthentication();
        if (!(rawAuth instanceof JwtAuthenticationToken auth)) {
            throw new StatusRuntimeException(Status.UNAUTHENTICATED.withDescription("Invalid auth context"));
        }
        String email = auth.getEmail();

        User user = userService.findByEmail(email).orElseThrow(() -> new NotFoundException("User", email));

        GetCurrentUserResponse response =
                GetCurrentUserResponse.newBuilder().setUser(user).build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }
}
