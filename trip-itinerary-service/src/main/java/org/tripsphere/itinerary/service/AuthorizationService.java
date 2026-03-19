package org.tripsphere.itinerary.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.exception.PermissionDeniedException;
import org.tripsphere.itinerary.exception.UnauthenticatedException;
import org.tripsphere.itinerary.model.ItineraryDoc;
import org.tripsphere.itinerary.repository.ItineraryDocRepository;
import org.tripsphere.itinerary.security.GrpcAuthContext;

/**
 * Service for authorization checks. Ensures users can only access their own resources unless they
 * have admin privileges.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AuthorizationService {

    private final ItineraryDocRepository itineraryDocRepository;

    /**
     * Ensure the user is authenticated.
     *
     * @param authContext the auth context
     * @throws PermissionDeniedException if not authenticated
     */
    public void requireAuthenticated(GrpcAuthContext authContext) {
        if (!authContext.isAuthenticated()) {
            log.warn("Unauthenticated access attempt");
            throw UnauthenticatedException.authenticationRequired();
        }
    }

    /**
     * Check if the user can access a specific itinerary.
     *
     * @param authContext the auth context
     * @param itineraryId the itinerary ID to access
     * @throws PermissionDeniedException if user cannot access the itinerary
     */
    public void checkItineraryAccess(GrpcAuthContext authContext, String itineraryId) {
        requireAuthenticated(authContext);

        // Admins can access any itinerary
        if (authContext.isAdmin()) {
            log.debug("Admin access granted for itinerary: {}", itineraryId);
            return;
        }

        // Check if user owns the itinerary
        ItineraryDoc doc = itineraryDocRepository.findById(itineraryId).orElse(null);
        if (doc == null) {
            // Let the service layer handle not found - don't leak existence info
            return;
        }

        if (!authContext.getUserId().equals(doc.getUserId())) {
            log.warn(
                    "User {} attempted to access itinerary {} owned by {}",
                    authContext.getUserId(),
                    itineraryId,
                    doc.getUserId());
            throw PermissionDeniedException.notOwner();
        }
    }

    /**
     * Check if the user can access a specific activity. Finds the itinerary containing the activity
     * and checks ownership.
     *
     * @param authContext the auth context
     * @param activityId the activity ID to access
     * @throws PermissionDeniedException if user cannot access the activity
     */
    public void checkActivityAccess(GrpcAuthContext authContext, String activityId) {
        requireAuthenticated(authContext);

        // Admins can access any activity
        if (authContext.isAdmin()) {
            log.debug("Admin access granted for activity: {}", activityId);
            return;
        }

        // Find the itinerary containing the activity
        ItineraryDoc doc = itineraryDocRepository.findByActivityId(activityId).orElse(null);
        if (doc == null) {
            // Let the service layer handle not found - don't leak existence info
            return;
        }

        if (!authContext.getUserId().equals(doc.getUserId())) {
            log.warn(
                    "User {} attempted to access activity {} in itinerary {} owned by {}",
                    authContext.getUserId(),
                    activityId,
                    doc.getId(),
                    doc.getUserId());
            throw PermissionDeniedException.notOwner();
        }
    }

    /**
     * Check if the user can list itineraries for a specific user.
     *
     * @param authContext the auth context
     * @param targetUserId the user ID whose itineraries are being listed
     * @throws PermissionDeniedException if user cannot list the itineraries
     */
    public void checkListAccess(GrpcAuthContext authContext, String targetUserId) {
        requireAuthenticated(authContext);

        // Admins can list any user's itineraries
        if (authContext.isAdmin()) {
            log.debug("Admin access granted for listing user {} itineraries", targetUserId);
            return;
        }

        // Users can only list their own itineraries
        if (!authContext.getUserId().equals(targetUserId)) {
            log.warn("User {} attempted to list itineraries for user {}", authContext.getUserId(), targetUserId);
            throw PermissionDeniedException.notOwner();
        }
    }
}
