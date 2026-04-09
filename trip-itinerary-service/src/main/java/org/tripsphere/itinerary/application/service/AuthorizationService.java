package org.tripsphere.itinerary.application.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.exception.PermissionDeniedException;
import org.tripsphere.itinerary.application.exception.UnauthenticatedException;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.Itinerary;
import org.tripsphere.itinerary.infrastructure.security.GrpcAuthContext;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthorizationService {

    private final ItineraryRepository itineraryRepository;

    public void requireAuthenticated(GrpcAuthContext authContext) {
        if (!authContext.isAuthenticated()) {
            log.warn("Unauthenticated access attempt");
            throw UnauthenticatedException.authenticationRequired();
        }
    }

    public void checkItineraryAccess(GrpcAuthContext authContext, String itineraryId) {
        requireAuthenticated(authContext);

        if (authContext.isAdmin()) {
            log.debug("Admin access granted for itinerary: {}", itineraryId);
            return;
        }

        Itinerary itinerary = itineraryRepository.findById(itineraryId).orElse(null);
        if (itinerary == null) return;

        if (!authContext.getUserId().equals(itinerary.getUserId())) {
            log.warn(
                    "User {} attempted to access itinerary {} owned by {}",
                    authContext.getUserId(),
                    itineraryId,
                    itinerary.getUserId());
            throw PermissionDeniedException.notOwner();
        }
    }

    public void checkActivityAccess(GrpcAuthContext authContext, String activityId) {
        requireAuthenticated(authContext);

        if (authContext.isAdmin()) {
            log.debug("Admin access granted for activity: {}", activityId);
            return;
        }

        Itinerary itinerary = itineraryRepository.findByActivityId(activityId).orElse(null);
        if (itinerary == null) return;

        if (!authContext.getUserId().equals(itinerary.getUserId())) {
            log.warn(
                    "User {} attempted to access activity {} in itinerary {} owned by {}",
                    authContext.getUserId(),
                    activityId,
                    itinerary.getId(),
                    itinerary.getUserId());
            throw PermissionDeniedException.notOwner();
        }
    }

    public void checkListAccess(GrpcAuthContext authContext, String targetUserId) {
        requireAuthenticated(authContext);

        if (authContext.isAdmin()) {
            log.debug("Admin access granted for listing user {} itineraries", targetUserId);
            return;
        }

        if (!authContext.getUserId().equals(targetUserId)) {
            log.warn("User {} attempted to list itineraries for user {}", authContext.getUserId(), targetUserId);
            throw PermissionDeniedException.notOwner();
        }
    }
}
