package org.tripsphere.order.application.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.order.application.exception.PermissionDeniedException;
import org.tripsphere.order.application.exception.UnauthenticatedException;
import org.tripsphere.order.domain.model.Order;
import org.tripsphere.order.infrastructure.security.GrpcAuthContext;

@Slf4j
@Service
public class OrderAuthorizationService {

    public String requireAuthenticated(GrpcAuthContext authContext) {
        if (!authContext.isAuthenticated()) {
            log.warn("Unauthenticated order access attempt");
            throw UnauthenticatedException.authenticationRequired();
        }
        return authContext.getUserId();
    }

    public String requireRequestedUser(GrpcAuthContext authContext, String requestedUserId) {
        String currentUserId = requireAuthenticated(authContext);
        if (!currentUserId.equals(requestedUserId)) {
            log.warn("User {} attempted to access orders for user {}", currentUserId, requestedUserId);
            throw PermissionDeniedException.notOwner();
        }
        return currentUserId;
    }

    public void requireOrderOwner(String currentUserId, Order order) {
        if (!currentUserId.equals(order.getUserId())) {
            log.warn(
                    "User {} attempted to access order {} owned by {}",
                    currentUserId,
                    order.getId(),
                    order.getUserId());
            throw PermissionDeniedException.notOwner();
        }
    }
}
