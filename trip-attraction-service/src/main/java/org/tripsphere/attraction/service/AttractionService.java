package org.tripsphere.attraction.service;

import java.util.Optional;
import java.util.logging.Logger;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Example;
import org.springframework.stereotype.Service;
import org.tripsphere.attraction.model.Attraction;
import org.tripsphere.attraction.repository.AttractionRepository;

@Service
public class AttractionService {
    private static final Logger logger = Logger.getLogger(Attraction.class.getName());
    @Autowired private AttractionRepository attractionRepository;

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
     * @param id attraction id
     * @return if delete success, return true, else return false
     */
    public boolean deleteAttraction(String id) {
        Optional<Attraction> attractionOptional = attractionRepository.findById(id);
        if (attractionOptional.isPresent()) {
            Attraction attraction = attractionOptional.get();
            attractionRepository.delete(attraction);
        } else return false;
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
        } else return null;
    }

    /**
     * find attraction id by name
     *
     * @param name attraction name
     * @return if found, return attraction id, else return null
     */
    public String findAttractionIdByName(String name) {
        Attraction probe = new Attraction();
        probe.setName(name);
        Example<Attraction> example = Example.of(probe);
        Optional<Attraction> attractionOptional = attractionRepository.findOne(example);
        if (attractionOptional.isPresent()) {
            Attraction attraction = attractionOptional.get();
            return attraction.getId();
        } else return null;
    }
}
