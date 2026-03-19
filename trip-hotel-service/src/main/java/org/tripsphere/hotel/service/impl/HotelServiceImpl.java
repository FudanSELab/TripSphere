package org.tripsphere.hotel.service.impl;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.geo.Point;
import org.springframework.stereotype.Service;
import org.tripsphere.common.v1.GeoPoint;
import org.tripsphere.hotel.mapper.HotelMapper;
import org.tripsphere.hotel.mapper.RoomTypeMapper;
import org.tripsphere.hotel.model.HotelDoc;
import org.tripsphere.hotel.model.RoomTypeDoc;
import org.tripsphere.hotel.repository.HotelDocRepository;
import org.tripsphere.hotel.repository.RoomTypeDocRepository;
import org.tripsphere.hotel.service.HotelService;
import org.tripsphere.hotel.util.CoordinateTransformUtil;
import org.tripsphere.hotel.v1.Hotel;
import org.tripsphere.hotel.v1.RoomType;

@Slf4j
@Service
@RequiredArgsConstructor
public class HotelServiceImpl implements HotelService {

    private final HotelDocRepository hotelDocRepository;
    private final RoomTypeDocRepository roomTypeDocRepository;
    private final HotelMapper hotelMapper = HotelMapper.INSTANCE;
    private final RoomTypeMapper roomTypeMapper = RoomTypeMapper.INSTANCE;

    private static final int DEFAULT_NEARBY_LIMIT = 100;
    private static final int DEFAULT_PAGE_SIZE = 20;
    private static final int MAX_PAGE_SIZE = 100;

    @Override
    public Optional<Hotel> findById(String id) {
        log.debug("Finding hotel by id: {}", id);
        return hotelDocRepository.findById(id).map(hotelMapper::toProto);
    }

    @Override
    public List<Hotel> findAllByIds(List<String> ids) {
        log.debug("Finding hotels by ids, count: {}", ids.size());
        List<HotelDoc> docs = hotelDocRepository.findAllById(ids);
        return hotelMapper.toProtoList(docs);
    }

    @Override
    public List<Hotel> searchNearby(GeoPoint location, double radiusMeters) {
        log.debug(
                "Searching hotels nearby location: ({}, {}), radius: {}m",
                location.getLongitude(),
                location.getLatitude(),
                radiusMeters);

        // Convert GCJ-02 (from client) to WGS84 (for MongoDB)
        Point wgs84Location = toWgs84Point(location);

        List<HotelDoc> docs =
                hotelDocRepository.findAllByLocationNear(wgs84Location, radiusMeters, DEFAULT_NEARBY_LIMIT);
        return hotelMapper.toProtoList(docs);
    }

    @Override
    public HotelPage listHotels(String province, String city, int pageSize, String pageToken) {
        log.debug(
                "Listing hotels: province={}, city={}, pageSize={}, pageToken={}", province, city, pageSize, pageToken);

        // Normalize page size
        int normalizedPageSize = normalizePageSize(pageSize);

        // Decode cursor from page token
        CursorToken cursor = decodeCursorToken(pageToken);

        // Fetch one extra to determine if there are more results
        List<HotelDoc> docs = hotelDocRepository.findByAddressWithPagination(
                province,
                city,
                normalizedPageSize + 1,
                cursor != null ? cursor.createdAt() : null,
                cursor != null ? cursor.id() : null);

        boolean hasMore = docs.size() > normalizedPageSize;
        if (hasMore) {
            docs = docs.subList(0, normalizedPageSize);
        }

        List<Hotel> hotels = hotelMapper.toProtoList(docs);

        // Generate next page token from the last item's cursor values
        String nextPageToken = null;
        if (hasMore && !docs.isEmpty()) {
            HotelDoc lastDoc = docs.get(docs.size() - 1);
            nextPageToken = encodeCursorToken(lastDoc.getCreatedAt(), lastDoc.getId());
        }

        return new HotelPage(hotels, nextPageToken);
    }

    @Override
    public List<RoomType> findRoomTypesByHotelId(String hotelId) {
        log.debug("Finding room types for hotel: {}", hotelId);
        List<RoomTypeDoc> docs = roomTypeDocRepository.findByHotelId(hotelId);
        return roomTypeMapper.toProtoList(docs);
    }

    // ==================== Helper Methods ====================

    /** Convert GeoPoint (GCJ-02) to Spring Point (WGS84) for MongoDB queries. */
    private Point toWgs84Point(GeoPoint geoPoint) {
        double[] wgs84 = CoordinateTransformUtil.gcj02ToWgs84(geoPoint.getLongitude(), geoPoint.getLatitude());
        return new Point(wgs84[0], wgs84[1]);
    }

    private int normalizePageSize(int pageSize) {
        if (pageSize <= 0) {
            return DEFAULT_PAGE_SIZE;
        }
        return Math.min(pageSize, MAX_PAGE_SIZE);
    }

    // ==================== Cursor Token Methods ====================

    /** Cursor token containing the pagination cursor values. */
    private record CursorToken(Instant createdAt, String id) {}

    private static final String CURSOR_SEPARATOR = "|";

    /**
     * Encodes cursor values into a Base64 page token. Format: "epochMillis|id" encoded in Base64.
     */
    private String encodeCursorToken(Instant createdAt, String id) {
        String raw = createdAt.toEpochMilli() + CURSOR_SEPARATOR + id;
        return Base64.getUrlEncoder().withoutPadding().encodeToString(raw.getBytes(StandardCharsets.UTF_8));
    }

    /**
     * Decodes a Base64 page token into cursor values.
     *
     * @return CursorToken if valid, null if token is empty or invalid
     */
    private CursorToken decodeCursorToken(String pageToken) {
        if (pageToken == null || pageToken.isEmpty()) {
            return null;
        }
        try {
            String decoded = new String(Base64.getUrlDecoder().decode(pageToken), StandardCharsets.UTF_8);
            int separatorIndex = decoded.indexOf(CURSOR_SEPARATOR);
            if (separatorIndex == -1) {
                log.warn("Invalid cursor token format: {}", pageToken);
                return null;
            }
            long epochMilli = Long.parseLong(decoded.substring(0, separatorIndex));
            String id = decoded.substring(separatorIndex + 1);
            return new CursorToken(Instant.ofEpochMilli(epochMilli), id);
        } catch (Exception e) {
            log.warn("Failed to decode cursor token: {}", pageToken, e);
            return null;
        }
    }
}
