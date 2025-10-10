package org.tripsphere.hotel.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.tripsphere.hotel.service.HotelService;

@CrossOrigin
@RestController
public class HotelController {
    @Autowired private HotelService hotelService;
}
