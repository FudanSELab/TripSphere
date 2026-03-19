package org.tripsphere.itinerary.model;

import java.util.ArrayList;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class ItinerarySummaryDoc {
    private Money totalEstimatedCost;
    private Integer totalActivities;

    @Builder.Default
    private List<String> highlights = new ArrayList<>();
}
