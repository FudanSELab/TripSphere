package org.tripsphere.itinerary.service;

import java.util.List;
import org.tripsphere.itinerary.v1.Activity;
import org.tripsphere.itinerary.v1.DayPlan;
import org.tripsphere.itinerary.v1.Itinerary;

public interface ItineraryService {

    Itinerary createItinerary(Itinerary itinerary);

    Itinerary getItinerary(String id);

    PageResult<Itinerary> listUserItineraries(String userId, int pageSize, String pageToken);

    void deleteItinerary(String id);

    Itinerary updateItinerary(Itinerary itinerary);

    Itinerary replaceItinerary(String id, Itinerary itinerary);

    DayPlan addDayPlan(String itineraryId, DayPlan dayPlan);

    void deleteDayPlan(String itineraryId, String dayPlanId);

    Activity addActivity(String itineraryId, String dayPlanId, Activity activity, int insertIndex);

    Activity updateActivity(Activity activity);

    void deleteActivity(String itineraryId, String dayPlanId, String activityId);

    record PageResult<T>(List<T> items, String nextPageToken) {}
}
