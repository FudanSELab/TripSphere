package org.tripsphere.hotel.model;

import java.util.List;

import lombok.Data;

@Data
public class Room {
    private String name;
    private int total_number;
    private int remaining_number;
    private double bed_width;
    private int bed_number;
    private double min_area;
    private double max_area;
    private int people_number;
    private List<String> tags;
}
