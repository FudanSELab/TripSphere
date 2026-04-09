package org.tripsphere.attraction.domain.model;

import java.time.DayOfWeek;
import java.time.LocalTime;
import java.util.List;
import java.util.Objects;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.jspecify.annotations.NonNull;
import org.jspecify.annotations.Nullable;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class OpenRule {
    private List<DayOfWeek> days;
    private List<TimeRange> timeRanges;
    private String note;

    public record TimeRange(
            @NonNull LocalTime openTime,
            @NonNull LocalTime closeTime,
            @Nullable LocalTime lastEntryTime) {
        public TimeRange {
            Objects.requireNonNull(openTime, "openTime cannot be null");
            Objects.requireNonNull(closeTime, "closeTime cannot be null");
            if (!openTime.isBefore(closeTime)) {
                throw new IllegalArgumentException("openTime must be before closeTime");
            }
            if (lastEntryTime != null && (lastEntryTime.isBefore(openTime) || lastEntryTime.isAfter(closeTime))) {
                throw new IllegalArgumentException("lastEntryTime must be between openTime and closeTime");
            }
        }
    }
}
