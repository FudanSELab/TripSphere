package org.tripsphere.user.application.service.query;

import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.user.application.dto.UserDto;
import org.tripsphere.user.application.exception.NotFoundException;
import org.tripsphere.user.application.port.UserRepository;
import org.tripsphere.user.domain.model.Role;
import org.tripsphere.user.domain.model.User;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetUserUseCase {

    private final UserRepository userRepository;

    @Transactional(readOnly = true)
    public UserDto getByEmail(String email) {
        log.debug("Finding user by email: {}", email);
        return userRepository
                .findByEmail(email)
                .map(this::toDto)
                .orElseThrow(() -> new NotFoundException("User", email));
    }

    @Transactional(readOnly = true)
    public Optional<UserDto> findByEmail(String email) {
        log.debug("Finding user by email: {}", email);
        return userRepository.findByEmail(email).map(this::toDto);
    }

    @Transactional(readOnly = true)
    public UserDto getById(String id) {
        log.debug("Finding user by id: {}", id);
        return userRepository.findById(id).map(this::toDto).orElseThrow(() -> new NotFoundException("User", id));
    }

    private UserDto toDto(User user) {
        List<String> roles = user.getRoles().stream().map(Role::name).toList();
        return new UserDto(user.getId(), user.getName(), user.getEmail(), roles);
    }
}
