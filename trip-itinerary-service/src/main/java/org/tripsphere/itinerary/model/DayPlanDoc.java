package org.tripsphere.itinerary.model;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class DayPlanDoc {
    private String id;
    private LocalDate date;
    private String title;

    @Builder.Default
    private List<ActivityDoc> activities = new ArrayList<>();

    private String notes;
    private Map<String, Object> metadata;
    private Integer dayNumber;
}
