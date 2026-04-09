package org.tripsphere.user.application.port;

import java.util.Optional;
import org.tripsphere.user.domain.model.User;

/** Output port — defines the persistence contract for the application core. */
public interface UserRepository {

    User save(User user);

    Optional<User> findById(String id);

    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);
}
