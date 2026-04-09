package org.tripsphere.itinerary.domain.model;

import java.util.ArrayList;
import java.util.List;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class ItinerarySummary {
    private Money totalEstimatedCost;
    private Integer totalActivities;

    @Builder.Default
    private List<String> highlights = new ArrayList<>();
}
