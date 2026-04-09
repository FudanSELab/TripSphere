package org.tripsphere.user.infrastructure.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.user.application.dto.SignInResult;
import org.tripsphere.user.application.dto.UserDto;
import org.tripsphere.user.v1.SignInResponse;
import org.tripsphere.user.v1.User;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface UserProtoMapper {

    User toProto(UserDto userDto);

    List<User> toProtoList(List<UserDto> userDtos);

    @Mapping(target = "user", expression = "java(toUserProto(result))")
    @Mapping(target = "token", source = "token")
    SignInResponse toSignInResponse(SignInResult result);

    default User toUserProto(SignInResult result) {
        return User.newBuilder()
                .setId(result.userId())
                .setName(result.name())
                .setEmail(result.email())
                .addAllRoles(result.roles())
                .build();
    }
}
