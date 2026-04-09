package org.tripsphere.user.application.dto;

import java.util.List;

/** Read-only view of a user, returned by query use cases. */
public record UserDto(String id, String name, String email, List<String> roles) {}
