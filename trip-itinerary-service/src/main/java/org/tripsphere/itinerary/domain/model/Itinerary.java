package org.tripsphere.itinerary.domain.model;

import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import lombok.Builder;
import lombok.Getter;
import org.tripsphere.itinerary.domain.exception.ActivityNotFoundException;
import org.tripsphere.itinerary.domain.exception.DayPlanNotFoundException;

@Getter
@Builder
public class Itinerary {
    private String id;
    private String userId;
    private String title;
    private String destinationPoiId;
    private String destinationName;
    private LocalDate startDate;
    private LocalDate endDate;

    @Builder.Default
    private List<DayPlan> dayPlans = new ArrayList<>();

    private Map<String, Object> metadata;
    private ItinerarySummary summary;
    private String markdownContent;
    private Instant createdAt;
    private Instant updatedAt;

    public void updateMetadata(
            String title,
            LocalDate startDate,
            LocalDate endDate,
            String destinationName,
            String markdownContent,
            ItinerarySummary summary) {
        if (title != null && !title.isBlank()) this.title = title;
        if (startDate != null) this.startDate = startDate;
        if (endDate != null) this.endDate = endDate;
        if (destinationName != null && !destinationName.isBlank()) this.destinationName = destinationName;
        if (markdownContent != null && !markdownContent.isBlank()) this.markdownContent = markdownContent;
        if (summary != null) this.summary = summary;
    }

    public void replaceContent(Itinerary replacement) {
        this.title = replacement.title;
        this.destinationPoiId = replacement.destinationPoiId;
        this.destinationName = replacement.destinationName;
        this.startDate = replacement.startDate;
        this.endDate = replacement.endDate;
        this.metadata = replacement.metadata;
        this.summary = replacement.summary;
        this.markdownContent = replacement.markdownContent;
        this.dayPlans = replacement.dayPlans != null ? new ArrayList<>(replacement.dayPlans) : new ArrayList<>();
        ensureAllIds();
    }

    public DayPlan addDayPlan(DayPlan dayPlan) {
        dayPlan.ensureId();
        if (dayPlans == null) {
            dayPlans = new ArrayList<>();
        }
        dayPlans.add(dayPlan);
        return dayPlan;
    }

    public void removeDayPlan(String dayPlanId) {
        if (dayPlans == null || !dayPlans.removeIf(dp -> dp.getId().equals(dayPlanId))) {
            throw new DayPlanNotFoundException(dayPlanId);
        }
    }

    public DayPlan findDayPlan(String dayPlanId) {
        if (dayPlans == null) {
            throw new DayPlanNotFoundException(dayPlanId);
        }
        return dayPlans.stream()
                .filter(dp -> dp.getId().equals(dayPlanId))
                .findFirst()
                .orElseThrow(() -> new DayPlanNotFoundException(dayPlanId));
    }

    public Activity addActivity(String dayPlanId, Activity activity, int insertIndex) {
        return findDayPlan(dayPlanId).addActivity(activity, insertIndex);
    }

    public void removeActivity(String dayPlanId, String activityId) {
        findDayPlan(dayPlanId).removeActivity(activityId);
    }

    public Activity replaceActivity(Activity updated) {
        if (dayPlans == null) {
            throw new ActivityNotFoundException(updated.getId());
        }
        for (DayPlan dayPlan : dayPlans) {
            List<Activity> activities = dayPlan.getActivities();
            if (activities == null) continue;
            for (int i = 0; i < activities.size(); i++) {
                if (activities.get(i).getId().equals(updated.getId())) {
                    activities.set(i, updated);
                    return updated;
                }
            }
        }
        throw new ActivityNotFoundException(updated.getId());
    }

    public void ensureAllIds() {
        if (dayPlans != null) {
            dayPlans.forEach(DayPlan::ensureId);
        }
    }
}
