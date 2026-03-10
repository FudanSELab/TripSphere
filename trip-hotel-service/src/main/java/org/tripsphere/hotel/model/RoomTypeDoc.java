package org.tripsphere.hotel.model;

import java.time.Instant;
import java.util.List;
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
@Document(collection = "room_types")
public class RoomTypeDoc {
    @Id private String id;
    private String hotelId;
    private String name;
    private String areaDescription;
    private String bedDescription;
    private int maxOccupancy;
    private boolean hasWindow;
    private List<String> images;
    private String description;
    private List<String> amenities;
    @CreatedDate private Instant createdAt;
    @LastModifiedDate private Instant updatedAt;
}
