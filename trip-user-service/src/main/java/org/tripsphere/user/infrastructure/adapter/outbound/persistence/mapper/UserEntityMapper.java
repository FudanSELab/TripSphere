package org.tripsphere.user.infrastructure.adapter.outbound.persistence.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.user.domain.model.User;
import org.tripsphere.user.infrastructure.adapter.outbound.persistence.entity.UserJpaEntity;

@Mapper(
        componentModel = "spring",
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface UserEntityMapper {

    User toDomain(UserJpaEntity entity);

    UserJpaEntity toEntity(User user);
}
