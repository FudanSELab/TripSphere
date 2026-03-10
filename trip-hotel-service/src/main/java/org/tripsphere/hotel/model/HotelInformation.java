package org.tripsphere.hotel.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class HotelInformation {
    /** The year the hotel was opened. For example, 2017. */
    private int openingSince;

    private String phoneNumber;
    private int roomCount;
    private String introduction;
}
