package org.tripsphere.itinerary.service.impl;

import com.github.f4b6a3.uuid.UuidCreator;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.exception.InvalidArgumentException;
import org.tripsphere.itinerary.exception.NotFoundException;
import org.tripsphere.itinerary.mapper.ActivityMapper;
import org.tripsphere.itinerary.mapper.DayPlanMapper;
import org.tripsphere.itinerary.mapper.ItineraryMapper;
import org.tripsphere.itinerary.model.ActivityDoc;
import org.tripsphere.itinerary.model.DayPlanDoc;
import org.tripsphere.itinerary.model.ItineraryDoc;
import org.tripsphere.itinerary.repository.ItineraryRepository;
import org.tripsphere.itinerary.service.ItineraryService;
import org.tripsphere.itinerary.v1.DayPlan;
import org.tripsphere.itinerary.v1.Itinerary;
import org.tripsphere.itinerary.v1.Activity;

@Slf4j
@Service
@RequiredArgsConstructor
public class ItineraryServiceImpl implements ItineraryService {

    private final ItineraryRepository itineraryRepository;
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

        ItineraryDoc saved = itineraryRepository.save(doc);
        log.info("Created itinerary with id: {}", saved.getId());

        return itineraryMapper.toProto(saved);
    }

    @Override
    public Itinerary getItinerary(String id) {
        log.debug("Getting itinerary by id: {}", id);

        ItineraryDoc doc =
                itineraryRepository
                        .findById(id)
                        .orElseThrow(() -> new NotFoundException("Itinerary", id));

        return itineraryMapper.toProto(doc);
    }

    @Override
    public PageResult<Itinerary> listUserItineraries(
            String userId, int pageSize, String pageToken) {
        log.debug("Listing itineraries for user: {}, pageSize: {}", userId, pageSize);

        // Normalize page size
        int normalizedPageSize = normalizePageSize(pageSize);

        // Decode cursor from page token
        CursorToken cursor = decodeCursorToken(pageToken);

        // Fetch one extra to determine if there are more results
        List<ItineraryDoc> docs;
        PageRequest limit = PageRequest.of(0, normalizedPageSize + 1);

        if (cursor == null) {
            // First page: no cursor, just fetch the first batch
            docs = itineraryRepository.findByUserIdOrderByCreatedAtDescIdDesc(userId, limit);
        } else {
            // Subsequent pages: use cursor for efficient keyset pagination
            docs =
                    itineraryRepository.findByUserIdWithCursor(
                            userId, cursor.createdAt(), cursor.id(), limit);
        }

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
    public DayPlan addDayPlan(String itineraryId, DayPlan dayPlan) {
        log.debug("Adding day plan to itinerary: {}", itineraryId);

        ItineraryDoc doc = getItineraryDoc(itineraryId);

        DayPlanDoc dayPlanDoc = dayPlanMapper.toDoc(dayPlan);
        ensureDayPlanId(dayPlanDoc);

        if (doc.getDayPlans() == null) {
            doc.setDayPlans(new ArrayList<>());
        }
        doc.getDayPlans().add(dayPlanDoc);

        itineraryRepository.save(doc);
        log.info("Added day plan {} to itinerary {}", dayPlanDoc.getId(), itineraryId);

        return dayPlanMapper.toProto(dayPlanDoc);
    }

    @Override
    public void deleteDayPlan(String itineraryId, String dayPlanId) {
        log.debug("Deleting day plan {} from itinerary {}", dayPlanId, itineraryId);

        ItineraryDoc doc = getItineraryDoc(itineraryId);

        boolean removed =
                doc.getDayPlans() != null
                        && doc.getDayPlans().removeIf(dp -> dp.getId().equals(dayPlanId));

        if (!removed) {
            throw new NotFoundException("DayPlan", dayPlanId);
        }

        itineraryRepository.save(doc);
        log.info("Deleted day plan {} from itinerary {}", dayPlanId, itineraryId);
    }

    @Override
    public Activity addActivity(
            String itineraryId, String dayPlanId, Activity activity, int insertIndex) {
        log.debug(
                "Adding activity to day plan {} in itinerary {} at index {}",
                dayPlanId,
                itineraryId,
                insertIndex);

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

        itineraryRepository.save(doc);
        log.info(
                "Added activity {} to day plan {} in itinerary {}",
                activityDoc.getId(),
                dayPlanId,
                itineraryId);

        return activityMapper.toProto(activityDoc);
    }

    @Override
    public Activity updateActivity(Activity activity) {
        String activityId = activity.getId();
        log.debug("Updating activity {}", activityId);

        if (activityId.isEmpty()) {
            throw InvalidArgumentException.required("activity.id");
        }

        ItineraryDoc doc =
                itineraryRepository
                        .findByActivityId(activityId)
                        .orElseThrow(() -> new NotFoundException("Activity", activityId));

        DayPlanDoc dayPlanDoc =
                doc.getDayPlans().stream()
                        .filter(
                                dp ->
                                        dp.getActivities() != null
                                                && dp.getActivities().stream()
                                                        .anyMatch(a -> a.getId().equals(activityId)))
                        .findFirst()
                        .orElseThrow(() -> new NotFoundException("Activity", activityId));

        List<ActivityDoc> activities = dayPlanDoc.getActivities();
        int index = -1;
        for (int i = 0; i < activities.size(); i++) {
            if (activities.get(i).getId().equals(activityId)) {
                index = i;
                break;
            }
        }

        ActivityDoc updatedDoc = activityMapper.toDoc(activity);
        activities.set(index, updatedDoc);

        itineraryRepository.save(doc);
        log.info("Updated activity {} in itinerary {}", activityId, doc.getId());

        return activityMapper.toProto(updatedDoc);
    }

    @Override
    public String findItineraryIdByActivityId(String activityId) {
        return itineraryRepository
                .findByActivityId(activityId)
                .map(ItineraryDoc::getId)
                .orElseThrow(() -> new NotFoundException("Activity", activityId));
    }

    @Override
    public void deleteActivity(String itineraryId, String dayPlanId, String activityId) {
        log.debug(
                "Deleting activity {} from day plan {} in itinerary {}",
                activityId,
                dayPlanId,
                itineraryId);

        ItineraryDoc doc = getItineraryDoc(itineraryId);
        DayPlanDoc dayPlanDoc = findDayPlan(doc, dayPlanId);

        boolean removed =
                dayPlanDoc.getActivities() != null
                        && dayPlanDoc.getActivities().removeIf(a -> a.getId().equals(activityId));

        if (!removed) {
            throw new NotFoundException("Activity", activityId);
        }

        itineraryRepository.save(doc);
        log.info(
                "Deleted activity {} from day plan {} in itinerary {}",
                activityId,
                dayPlanId,
                itineraryId);
    }

    // ==================== Helper Methods ====================

    private ItineraryDoc getItineraryDoc(String itineraryId) {
        return itineraryRepository
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
        return Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(raw.getBytes(StandardCharsets.UTF_8));
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
            String decoded =
                    new String(Base64.getUrlDecoder().decode(pageToken), StandardCharsets.UTF_8);
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
