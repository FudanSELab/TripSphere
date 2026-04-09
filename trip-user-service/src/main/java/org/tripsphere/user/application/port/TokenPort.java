package org.tripsphere.user.application.port;

import java.util.List;

/** Output port — defines the contract for generating authentication tokens. */
public interface TokenPort {

    String generateToken(String userId, String name, String email, List<String> roles);
}
