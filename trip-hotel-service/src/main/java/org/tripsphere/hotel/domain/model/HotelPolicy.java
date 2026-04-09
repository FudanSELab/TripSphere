package org.tripsphere.hotel.domain.model;

import java.time.LocalTime;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class HotelPolicy {
    private LocalTime checkInTime;
    private LocalTime checkOutTime;
    private BreakfastPolicy breakfast;
    private boolean petsAllowed;
}
