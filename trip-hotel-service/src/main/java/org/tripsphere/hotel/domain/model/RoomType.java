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
public class RoomType {
    private String id;
    private String hotelId;
    private String name;
    private String areaDescription;
    private String bedDescription;
    private int maxOccupancy;
    private boolean hasWindow;
    private List<String> images;
    private String description;
    private List<String> amenities;
}
