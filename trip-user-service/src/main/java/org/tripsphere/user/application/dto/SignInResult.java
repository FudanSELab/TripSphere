package org.tripsphere.user.application.dto;

import java.util.List;

/** Result returned by a successful sign-in. No Protobuf dependency. */
public record SignInResult(String userId, String name, String email, List<String> roles, String token) {}
