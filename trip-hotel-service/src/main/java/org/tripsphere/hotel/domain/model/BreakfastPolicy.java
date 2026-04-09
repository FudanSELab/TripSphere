package org.tripsphere.hotel.domain.model;

import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class BreakfastPolicy {
    private String format;
    private List<String> cuisines;
    private String openingHours;
    private Money price;
}
