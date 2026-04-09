package org.tripsphere.user.infrastructure.adapter.inbound.grpc;

import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.springframework.security.access.annotation.Secured;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.tripsphere.user.application.dto.SignInCommand;
import org.tripsphere.user.application.dto.SignInResult;
import org.tripsphere.user.application.dto.SignUpCommand;
import org.tripsphere.user.application.dto.UserDto;
import org.tripsphere.user.application.service.command.SignInUseCase;
import org.tripsphere.user.application.service.command.SignUpUseCase;
import org.tripsphere.user.application.service.query.GetUserUseCase;
import org.tripsphere.user.infrastructure.adapter.inbound.grpc.mapper.UserProtoMapper;
import org.tripsphere.user.infrastructure.adapter.inbound.grpc.security.JwtAuthenticationToken;
import org.tripsphere.user.v1.GetCurrentUserRequest;
import org.tripsphere.user.v1.GetCurrentUserResponse;
import org.tripsphere.user.v1.SignInRequest;
import org.tripsphere.user.v1.SignInResponse;
import org.tripsphere.user.v1.SignUpRequest;
import org.tripsphere.user.v1.SignUpResponse;
import org.tripsphere.user.v1.UserServiceGrpc;

@GrpcService
@RequiredArgsConstructor
public class UserGrpcService extends UserServiceGrpc.UserServiceImplBase {

    private final SignUpUseCase signUpUseCase;
    private final SignInUseCase signInUseCase;
    private final GetUserUseCase getUserUseCase;
    private final UserProtoMapper userProtoMapper;

    /** Public endpoint — no authentication required. */
    @Override
    public void signUp(SignUpRequest request, StreamObserver<SignUpResponse> responseObserver) {
        signUpUseCase.execute(new SignUpCommand(request.getName(), request.getEmail(), request.getPassword()));

        responseObserver.onNext(SignUpResponse.newBuilder().build());
        responseObserver.onCompleted();
    }

    /** Public endpoint — no authentication required. */
    @Override
    public void signIn(SignInRequest request, StreamObserver<SignInResponse> responseObserver) {
        SignInResult result = signInUseCase.execute(new SignInCommand(request.getEmail(), request.getPassword()));

        responseObserver.onNext(userProtoMapper.toSignInResponse(result));
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

        UserDto userDto = getUserUseCase.getByEmail(auth.getEmail());

        GetCurrentUserResponse response = GetCurrentUserResponse.newBuilder()
                .setUser(userProtoMapper.toProto(userDto))
                .build();

        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }
}
