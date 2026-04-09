package org.tripsphere.user.infrastructure.adapter.outbound.persistence;

import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;
import org.tripsphere.user.application.port.UserRepository;
import org.tripsphere.user.domain.model.User;
import org.tripsphere.user.infrastructure.adapter.outbound.persistence.entity.UserJpaEntity;
import org.tripsphere.user.infrastructure.adapter.outbound.persistence.mapper.UserEntityMapper;

/** Outbound persistence adapter — implements the {@link UserRepository} port using JPA. */
@Repository
@RequiredArgsConstructor
public class UserRepositoryImpl implements UserRepository {

    private final UserJpaRepository userJpaRepository;
    private final UserEntityMapper userEntityMapper;

    @Override
    public User save(User user) {
        UserJpaEntity entity = userEntityMapper.toEntity(user);
        UserJpaEntity saved = userJpaRepository.save(entity);
        return userEntityMapper.toDomain(saved);
    }

    @Override
    public Optional<User> findById(String id) {
        return userJpaRepository.findById(id).map(userEntityMapper::toDomain);
    }

    @Override
    public Optional<User> findByEmail(String email) {
        return userJpaRepository.findByEmail(email).map(userEntityMapper::toDomain);
    }

    @Override
    public boolean existsByEmail(String email) {
        return userJpaRepository.existsByEmail(email);
    }
}
