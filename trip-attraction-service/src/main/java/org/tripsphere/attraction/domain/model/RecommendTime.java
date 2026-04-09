package org.tripsphere.attraction.domain.model;

public record RecommendTime(double minHours, double maxHours) {
    public RecommendTime {
        if (minHours <= 0) {
            throw new IllegalArgumentException("minHours must be greater than 0");
        }
        if (maxHours <= minHours) {
            throw new IllegalArgumentException("maxHours must be greater than minHours");
        }
    }
}
