package org.tripsphere.attraction.domain.model;

import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class OpeningHours {
    private List<OpenRule> rules;
    private String specialTips;
}
