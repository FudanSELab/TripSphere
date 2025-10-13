package org.tripsphere.hotel.model;

import com.fasterxml.jackson.annotation.JsonInclude;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.io.Serializable;
import java.util.List;

@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
@Data
@Document("Hotels")
@JsonInclude(JsonInclude.Include.ALWAYS)
public class Hotel implements Serializable {
    @Id
    private String id;
    private String name;
    private String country;
    private String province;
    private String city;
    private String zone;
    private String address;
    private String introduction;
    private List<String> tags;
    private List<Room> rooms;
}
