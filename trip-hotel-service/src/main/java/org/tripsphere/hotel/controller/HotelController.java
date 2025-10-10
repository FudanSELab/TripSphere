package org.tripsphere.hotel.controller;

import org.tripsphere.hotel.model.Hotel;
import org.tripsphere.hotel.service.HotelService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@CrossOrigin
@RestController
public class HotelController {

    @Autowired
    private HotelService hotelService;


}
