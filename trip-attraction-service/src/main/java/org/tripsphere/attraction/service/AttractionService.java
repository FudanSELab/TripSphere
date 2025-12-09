package org.tripsphere.attraction.service;

import org.springaicommunity.mcp.annotation.McpTool;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Example;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.tripsphere.attraction.model.Attraction;
import org.tripsphere.attraction.repository.AttractionRepository;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;
import java.util.logging.Logger;

@Service
public class AttractionService {
    private static final Logger logger = Logger.getLogger(Attraction.class.getName());
    @Autowired
    private AttractionRepository attractionRepository;

    /**
     * Add attraction
     *
     * @param attraction attraction
     * @return the attraction id
     */
    public String addAttraction(Attraction attraction) {
        attractionRepository.save(attraction);
        return attraction.getId();
    }

    /**
     * Delete attraction
     *
     * @param id      attraction id
     * @return if delete success, return true, else return false
     */
    public boolean deleteAttraction(String id) {
        Optional<Attraction> attractionOptional = attractionRepository.findById(id);
        if (attractionOptional.isPresent()) {
            Attraction attraction = attractionOptional.get();
            attractionRepository.delete(attraction);
        } else
            return false;
        return true;
    }

    /**
     * Change attraction information except images
     *
     * @param attraction attraction
     * @return if change success, return true, else return false
     */
    public boolean changAttraction(Attraction attraction) {
        Optional<Attraction> attractionOptional = attractionRepository.findById(attraction.getId());
        if (!attractionOptional.isPresent()) return false;
        Attraction attractionOld = attractionOptional.get();
        attractionOld.setName(attraction.getName());
        attractionOld.setAddress(attraction.getAddress());
        attractionOld.setIntroduction(attraction.getIntroduction());
        attractionOld.setLocation(attraction.getLocation());
        attractionOld.setTags(attraction.getTags());
        return true;
    }

    /**
     * find attraction by id
     *
     * @param id attraction id
     * @return if found, return attraction, else return null
     */
    public Attraction findAttractionById(String id) {
        Optional<Attraction> attractionOptional = attractionRepository.findById(id);
        if (attractionOptional.isPresent()) {
            Attraction attraction = attractionOptional.get();
            return attraction;
        } else
            return null;
    }


}
