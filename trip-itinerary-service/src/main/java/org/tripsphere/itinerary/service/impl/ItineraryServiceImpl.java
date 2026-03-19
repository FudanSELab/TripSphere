package org.tripsphere.itinerary.service.impl;

import com.github.f4b6a3.uuid.UuidCreator;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.exception.InvalidArgumentException;
import org.tripsphere.itinerary.exception.NotFoundException;
import org.tripsphere.itinerary.mapper.ActivityMapper;
import org.tripsphere.itinerary.mapper.DayPlanMapper;
import org.tripsphere.itinerary.mapper.ItineraryMapper;
import org.tripsphere.itinerary.model.ActivityDoc;
import org.tripsphere.itinerary.model.DayPlanDoc;
import org.tripsphere.itinerary.model.ItineraryDoc;
import org.tripsphere.itinerary.repository.ItineraryDocRepository;
import org.tripsphere.itinerary.service.ItineraryService;
import org.tripsphere.itinerary.v1.Activity;
import org.tripsphere.itinerary.v1.DayPlan;
import org.tripsphere.itinerary.v1.Itinerary;

@Slf4j
@Service
@RequiredArgsConstructor
public class ItineraryServiceImpl implements ItineraryService {

    private final ItineraryDocRepository itineraryDocRepository;
    private final ItineraryMapper itineraryMapper = ItineraryMapper.INSTANCE;
    private final DayPlanMapper dayPlanMapper = DayPlanMapper.INSTANCE;
    private final ActivityMapper activityMapper = ActivityMapper.INSTANCE;

    private static final int DEFAULT_PAGE_SIZE = 20;
    private static final int MAX_PAGE_SIZE = 100;

    @Override
    public Itinerary createItinerary(Itinerary itinerary) {
        log.debug("Creating new itinerary: {}", itinerary.getTitle());

        ItineraryDoc doc = itineraryMapper.toDoc(itinerary);
        // Server generates the ID, ignore any client-provided ID
        doc.setId(null);

        // Ensure all day plans and activities have IDs
        if (doc.getDayPlans() != null) {
            for (DayPlanDoc dayPlan : doc.getDayPlans()) {
                ensureDayPlanId(dayPlan);
            }
        }

        ItineraryDoc saved = itineraryDocRepository.save(doc);
        log.info("Created itinerary with id: {}", saved.getId());

        return itineraryMapper.toProto(saved);
    }

    @Override
    public Itinerary getItinerary(String id) {
        log.debug("Getting itinerary by id: {}", id);

        ItineraryDoc doc =
                itineraryDocRepository.findById(id).orElseThrow(() -> new NotFoundException("Itinerary", id));

        return itineraryMapper.toProto(doc);
    }

    @Override
    public PageResult<Itinerary> listUserItineraries(String userId, int pageSize, String pageToken) {
        log.debug("Listing itineraries for user: {}, pageSize: {}", userId, pageSize);

        // Normalize page size
        int normalizedPageSize = normalizePageSize(pageSize);

        // Decode cursor from page token
        CursorToken cursor = decodeCursorToken(pageToken);

        // Fetch one extra to determine if there are more results
        List<ItineraryDoc> docs = itineraryDocRepository.findByUserIdWithPagination(
                userId,
                normalizedPageSize + 1,
                cursor != null ? cursor.createdAt() : null,
                cursor != null ? cursor.id() : null);

        boolean hasMore = docs.size() > normalizedPageSize;
        if (hasMore) {
            docs = docs.subList(0, normalizedPageSize);
        }

        List<Itinerary> itineraries = itineraryMapper.toProtoList(docs);

        // Generate next page token from the last item's cursor values
        String nextPageToken = null;
        if (hasMore && !docs.isEmpty()) {
            ItineraryDoc lastDoc = docs.get(docs.size() - 1);
            nextPageToken = encodeCursorToken(lastDoc.getCreatedAt(), lastDoc.getId());
        }

        return new PageResult<>(itineraries, nextPageToken);
    }

    @Override
    public void deleteItinerary(String id) {
        log.debug("Deleting itinerary: {}", id);
        if (!itineraryDocRepository.existsById(id)) {
            throw new NotFoundException("Itinerary", id);
        }
        itineraryDocRepository.deleteById(id);
        log.info("Deleted itinerary with id: {}", id);
    }

    @Override
    public Itinerary updateItinerary(Itinerary itinerary) {
        log.debug("Updating itinerary meta: {}", itinerary.getId());

        if (itinerary.getId().isEmpty()) {
            throw InvalidArgumentException.required("itinerary.id");
        }

        ItineraryDoc existing = getItineraryDoc(itinerary.getId());
        // Map incoming proto to a temporary doc to reuse converter logic for dates and summary
        ItineraryDoc incoming = itineraryMapper.toDoc(itinerary);

        // Update only meta-level fields; preserve day plans and ownership
        if (!itinerary.getTitle().isEmpty()) existing.setTitle(itinerary.getTitle());
        if (itinerary.hasStartDate()) existing.setStartDate(incoming.getStartDate());
        if (itinerary.hasEndDate()) existing.setEndDate(incoming.getEndDate());
        if (!itinerary.getDestinationName().isEmpty()) existing.setDestinationName(itinerary.getDestinationName());
        if (!itinerary.getMarkdownContent().isEmpty()) existing.setMarkdownContent(itinerary.getMarkdownContent());
        if (itinerary.hasSummary()) existing.setSummary(incoming.getSummary());

        ItineraryDoc saved = itineraryDocRepository.save(existing);
        log.info("Updated itinerary meta for id: {}", saved.getId());
        return itineraryMapper.toProto(saved);
    }

    @Override
    public Itinerary replaceItinerary(String id, Itinerary itinerary) {
        log.debug("Replacing itinerary: {}", id);

        ItineraryDoc existing =
                itineraryDocRepository.findById(id).orElseThrow(() -> new NotFoundException("Itinerary", id));

        ItineraryDoc replacement = itineraryMapper.toDoc(itinerary);
        // Preserve identity and ownership from the existing document
        replacement.setId(existing.getId());
        replacement.setUserId(existing.getUserId());
        // createdAt is preserved by @CreatedDate + Spring Data (it won't overwrite an existing value)
        replacement.setCreatedAt(existing.getCreatedAt());

        // Ensure all day plans and activities have IDs
        if (replacement.getDayPlans() != null) {
            for (DayPlanDoc dayPlan : replacement.getDayPlans()) {
                ensureDayPlanId(dayPlan);
            }
        }

        ItineraryDoc saved = itineraryDocRepository.save(replacement);
        log.info("Replaced itinerary with id: {}", saved.getId());

        return itineraryMapper.toProto(saved);
    }

    @Override
    public DayPlan addDayPlan(String itineraryId, DayPlan dayPlan) {
        log.debug("Adding day plan to itinerary: {}", itineraryId);

        ItineraryDoc doc = getItineraryDoc(itineraryId);

        DayPlanDoc dayPlanDoc = dayPlanMapper.toDoc(dayPlan);
        ensureDayPlanId(dayPlanDoc);

        if (doc.getDayPlans() == null) {
            doc.setDayPlans(new ArrayList<>());
        }
        doc.getDayPlans().add(dayPlanDoc);

        itineraryDocRepository.save(doc);
        log.info("Added day plan {} to itinerary {}", dayPlanDoc.getId(), itineraryId);

        return dayPlanMapper.toProto(dayPlanDoc);
    }

    @Override
    public void deleteDayPlan(String itineraryId, String dayPlanId) {
        log.debug("Deleting day plan {} from itinerary {}", dayPlanId, itineraryId);

        ItineraryDoc doc = getItineraryDoc(itineraryId);

        boolean removed = doc.getDayPlans() != null
                && doc.getDayPlans().removeIf(dp -> dp.getId().equals(dayPlanId));

        if (!removed) {
            throw new NotFoundException("DayPlan", dayPlanId);
        }

        itineraryDocRepository.save(doc);
        log.info("Deleted day plan {} from itinerary {}", dayPlanId, itineraryId);
    }

    @Override
    public Activity addActivity(String itineraryId, String dayPlanId, Activity activity, int insertIndex) {
        log.debug("Adding activity to day plan {} in itinerary {} at index {}", dayPlanId, itineraryId, insertIndex);

        ItineraryDoc doc = getItineraryDoc(itineraryId);
        DayPlanDoc dayPlanDoc = findDayPlan(doc, dayPlanId);

        ActivityDoc activityDoc = activityMapper.toDoc(activity);
        ensureActivityId(activityDoc);

        if (dayPlanDoc.getActivities() == null) {
            dayPlanDoc.setActivities(new ArrayList<>());
        }

        List<ActivityDoc> activities = dayPlanDoc.getActivities();
        if (insertIndex < 0 || insertIndex >= activities.size()) {
            activities.add(activityDoc);
        } else {
            activities.add(insertIndex, activityDoc);
        }

        itineraryDocRepository.save(doc);
        log.info("Added activity {} to day plan {} in itinerary {}", activityDoc.getId(), dayPlanId, itineraryId);

        return activityMapper.toProto(activityDoc);
    }

    @Override
    public Activity updateActivity(Activity activity) {
        log.debug("Updating activity {}", activity.getId());

        if (activity.getId().isEmpty()) {
            throw InvalidArgumentException.required("activity.id");
        }

        ItineraryDoc doc = itineraryDocRepository
                .findByActivityId(activity.getId())
                .orElseThrow(() -> new NotFoundException("Activity", activity.getId()));

        // Find the day plan and activity index
        ActivityDoc updatedDoc = activityMapper.toDoc(activity);
        boolean found = false;

        for (DayPlanDoc dayPlan : doc.getDayPlans()) {
            List<ActivityDoc> activities = dayPlan.getActivities();
            if (activities == null) continue;

            for (int i = 0; i < activities.size(); i++) {
                if (activities.get(i).getId().equals(activity.getId())) {
                    activities.set(i, updatedDoc);
                    found = true;
                    break;
                }
            }
            if (found) break;
        }

        if (!found) {
            throw new NotFoundException("Activity", activity.getId());
        }

        itineraryDocRepository.save(doc);
        log.info("Updated activity {} in itinerary {}", activity.getId(), doc.getId());

        return activityMapper.toProto(updatedDoc);
    }

    @Override
    public void deleteActivity(String itineraryId, String dayPlanId, String activityId) {
        log.debug("Deleting activity {} from day plan {} in itinerary {}", activityId, dayPlanId, itineraryId);

        ItineraryDoc doc = getItineraryDoc(itineraryId);
        DayPlanDoc dayPlanDoc = findDayPlan(doc, dayPlanId);

        boolean removed = dayPlanDoc.getActivities() != null
                && dayPlanDoc.getActivities().removeIf(a -> a.getId().equals(activityId));

        if (!removed) {
            throw new NotFoundException("Activity", activityId);
        }

        itineraryDocRepository.save(doc);
        log.info("Deleted activity {} from day plan {} in itinerary {}", activityId, dayPlanId, itineraryId);
    }

    // ==================== Helper Methods ====================

    private ItineraryDoc getItineraryDoc(String itineraryId) {
        return itineraryDocRepository
                .findById(itineraryId)
                .orElseThrow(() -> new NotFoundException("Itinerary", itineraryId));
    }

    private DayPlanDoc findDayPlan(ItineraryDoc doc, String dayPlanId) {
        if (doc.getDayPlans() == null) {
            throw new NotFoundException("DayPlan", dayPlanId);
        }
        return doc.getDayPlans().stream()
                .filter(dp -> dp.getId().equals(dayPlanId))
                .findFirst()
                .orElseThrow(() -> new NotFoundException("DayPlan", dayPlanId));
    }

    private void ensureDayPlanId(DayPlanDoc dayPlan) {
        if (dayPlan.getId() == null || dayPlan.getId().isEmpty()) {
            dayPlan.setId(UuidCreator.getTimeOrderedEpoch().toString());
        }
        if (dayPlan.getActivities() != null) {
            for (ActivityDoc activity : dayPlan.getActivities()) {
                ensureActivityId(activity);
            }
        }
    }

    private void ensureActivityId(ActivityDoc activity) {
        if (activity.getId() == null || activity.getId().isEmpty()) {
            activity.setId(UuidCreator.getTimeOrderedEpoch().toString());
        }
    }

    private int normalizePageSize(int pageSize) {
        if (pageSize <= 0) {
            return DEFAULT_PAGE_SIZE;
        }
        return Math.min(pageSize, MAX_PAGE_SIZE);
    }

    // ==================== Cursor Token Methods ====================

    /** Cursor token containing the pagination cursor values. */
    private record CursorToken(Instant createdAt, String id) {}

    private static final String CURSOR_SEPARATOR = "|";

    /**
     * Encodes cursor values into a Base64 page token. Format: "epochMillis|id" encoded in Base64.
     */
    private String encodeCursorToken(Instant createdAt, String id) {
        String raw = createdAt.toEpochMilli() + CURSOR_SEPARATOR + id;
        return Base64.getUrlEncoder().withoutPadding().encodeToString(raw.getBytes(StandardCharsets.UTF_8));
    }

    /**
     * Decodes a Base64 page token into cursor values.
     *
     * @return CursorToken if valid, null if token is empty or invalid
     */
    private CursorToken decodeCursorToken(String pageToken) {
        if (pageToken == null || pageToken.isEmpty()) {
            return null;
        }
        try {
            String decoded = new String(Base64.getUrlDecoder().decode(pageToken), StandardCharsets.UTF_8);
            int separatorIndex = decoded.indexOf(CURSOR_SEPARATOR);
            if (separatorIndex == -1) {
                log.warn("Invalid cursor token format: {}", pageToken);
                return null;
            }
            long epochMilli = Long.parseLong(decoded.substring(0, separatorIndex));
            String id = decoded.substring(separatorIndex + 1);
            return new CursorToken(Instant.ofEpochMilli(epochMilli), id);
        } catch (Exception e) {
            log.warn("Failed to decode cursor token: {}", pageToken, e);
            return null;
        }
    }
}
