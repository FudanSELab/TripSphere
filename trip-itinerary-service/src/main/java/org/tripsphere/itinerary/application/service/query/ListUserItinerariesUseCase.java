package org.tripsphere.itinerary.application.service.query;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.dto.ItineraryPage;
import org.tripsphere.itinerary.application.dto.ListItinerariesQuery;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.Itinerary;

@Slf4j
@Service
@RequiredArgsConstructor
public class ListUserItinerariesUseCase {

    private static final int DEFAULT_PAGE_SIZE = 20;
    private static final int MAX_PAGE_SIZE = 100;
    private static final String CURSOR_SEPARATOR = "|";

    private final ItineraryRepository itineraryRepository;

    public ItineraryPage execute(ListItinerariesQuery query) {
        log.debug("Listing itineraries for user: {}, pageSize: {}", query.userId(), query.pageSize());

        int normalizedPageSize = normalizePageSize(query.pageSize());
        CursorToken cursor = decodeCursorToken(query.pageToken());

        List<Itinerary> results = itineraryRepository.findByUserIdWithPagination(
                query.userId(),
                normalizedPageSize + 1,
                cursor != null ? cursor.createdAt() : null,
                cursor != null ? cursor.id() : null);

        boolean hasMore = results.size() > normalizedPageSize;
        if (hasMore) {
            results = results.subList(0, normalizedPageSize);
        }

        String nextPageToken = null;
        if (hasMore && !results.isEmpty()) {
            Itinerary last = results.get(results.size() - 1);
            nextPageToken = encodeCursorToken(last.getCreatedAt(), last.getId());
        }

        return new ItineraryPage(results, nextPageToken);
    }

    private int normalizePageSize(int pageSize) {
        if (pageSize <= 0) return DEFAULT_PAGE_SIZE;
        return Math.min(pageSize, MAX_PAGE_SIZE);
    }

    private record CursorToken(Instant createdAt, String id) {}

    private String encodeCursorToken(Instant createdAt, String id) {
        String raw = createdAt.toEpochMilli() + CURSOR_SEPARATOR + id;
        return Base64.getUrlEncoder().withoutPadding().encodeToString(raw.getBytes(StandardCharsets.UTF_8));
    }

    private CursorToken decodeCursorToken(String pageToken) {
        if (pageToken == null || pageToken.isEmpty()) return null;
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
