package org.tripsphere.user.domain.exception;

/** Base exception for domain-level rule violations. */
public class UserDomainException extends RuntimeException {

    public UserDomainException(String message) {
        super(message);
    }

    public UserDomainException(String message, Throwable cause) {
        super(message, cause);
    }
}
