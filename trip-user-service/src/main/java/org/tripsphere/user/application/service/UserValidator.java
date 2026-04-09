package org.tripsphere.user.application.service;

import java.util.regex.Pattern;
import org.springframework.stereotype.Component;
import org.tripsphere.user.application.exception.InvalidArgumentException;

/** Validates user-related input fields for use cases. */
@Component
public class UserValidator {

    private static final Pattern EMAIL_PATTERN = Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$");

    private static final Pattern PASSWORD_PATTERN =
            Pattern.compile("^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[^a-zA-Z0-9]).{8,}$");

    public void validateName(String name) {
        if (name == null || name.trim().isEmpty()) {
            throw InvalidArgumentException.empty("Name");
        }
    }

    public void validateEmail(String email) {
        if (email == null || email.trim().isEmpty()) {
            throw InvalidArgumentException.empty("Email");
        }
        if (!EMAIL_PATTERN.matcher(email).matches()) {
            throw InvalidArgumentException.invalid("Email", "must be a valid email address");
        }
    }

    public void validatePassword(String password) {
        if (password == null || password.trim().isEmpty()) {
            throw InvalidArgumentException.empty("Password");
        }
        if (!PASSWORD_PATTERN.matcher(password).matches()) {
            throw InvalidArgumentException.invalid(
                    "Password",
                    "must be at least 8 characters and contain at least one letter, one number, and"
                            + " one special character");
        }
    }

    public void validatePasswordNotEmpty(String password) {
        if (password == null || password.trim().isEmpty()) {
            throw InvalidArgumentException.empty("Password");
        }
    }
}
