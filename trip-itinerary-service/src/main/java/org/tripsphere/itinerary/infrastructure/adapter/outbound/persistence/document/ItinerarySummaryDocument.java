package org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.document;

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
public class ItinerarySummaryDocument {
    private MoneyDocument totalEstimatedCost;
    private Integer totalActivities;

    @Builder.Default
    private List<String> highlights = new ArrayList<>();
}
