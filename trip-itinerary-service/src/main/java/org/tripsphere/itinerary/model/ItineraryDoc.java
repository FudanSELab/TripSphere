package org.tripsphere.itinerary.model;

import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.mongodb.core.mapping.Document;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Document(collection = "itineraries")
public class ItineraryDoc {
    @Id
    private String id;

    private String userId;
    private String title;
    private String destinationPoiId;
    private LocalDate startDate;
    private LocalDate endDate;

    @Builder.Default
    private List<DayPlanDoc> dayPlans = new ArrayList<>();

    private Map<String, Object> metadata;
    private String destinationName;
    private ItinerarySummaryDoc summary;
    private String markdownContent;

    @CreatedDate
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;
}
