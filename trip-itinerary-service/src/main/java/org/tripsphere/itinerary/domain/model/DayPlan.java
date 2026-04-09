package org.tripsphere.itinerary.domain.model;

import com.github.f4b6a3.uuid.UuidCreator;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import lombok.Builder;
import lombok.Getter;
import org.tripsphere.itinerary.domain.exception.ActivityNotFoundException;

@Getter
@Builder
public class DayPlan {
    private String id;
    private LocalDate date;
    private String title;

    @Builder.Default
    private List<Activity> activities = new ArrayList<>();

    private String notes;
    private Map<String, Object> metadata;
    private Integer dayNumber;

    public void ensureId() {
        if (id == null || id.isEmpty()) {
            id = UuidCreator.getTimeOrderedEpoch().toString();
        }
        if (activities != null) {
            activities.forEach(Activity::ensureId);
        }
    }

    public Activity addActivity(Activity activity, int insertIndex) {
        activity.ensureId();
        if (activities == null) {
            activities = new ArrayList<>();
        }
        if (insertIndex < 0 || insertIndex >= activities.size()) {
            activities.add(activity);
        } else {
            activities.add(insertIndex, activity);
        }
        return activity;
    }

    public void removeActivity(String activityId) {
        if (activities == null || !activities.removeIf(a -> a.getId().equals(activityId))) {
            throw new ActivityNotFoundException(activityId);
        }
    }

    public Activity findActivity(String activityId) {
        if (activities == null) {
            throw new ActivityNotFoundException(activityId);
        }
        return activities.stream()
                .filter(a -> a.getId().equals(activityId))
                .findFirst()
                .orElseThrow(() -> new ActivityNotFoundException(activityId));
    }
}
