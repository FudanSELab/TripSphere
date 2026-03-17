package org.tripsphere.product.application.service.query;

import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.product.application.dto.SpuPage;
import org.tripsphere.product.application.util.CursorTokenUtil;
import org.tripsphere.product.application.util.CursorTokenUtil.CursorToken;
import org.tripsphere.product.domain.model.ResourceType;
import org.tripsphere.product.domain.model.Spu;
import org.tripsphere.product.domain.repository.SpuRepository;

@Slf4j
@Service
@RequiredArgsConstructor
public class ListSpusByResourceUseCase {
    private final SpuRepository spuRepository;

    private static final int DEFAULT_PAGE_SIZE = 20;
    private static final int MAX_PAGE_SIZE = 100;

    public SpuPage execute(ResourceType resourceType, String resourceId, int pageSize, String pageToken) {
        log.debug(
                "Listing SPUs by resource: type={}, id={}, pageSize={}, pageToken={}",
                resourceType,
                resourceId,
                pageSize,
                pageToken);

        int normalizedPageSize = normalizePageSize(pageSize);
        String afterId = decodeAfterIdOrNull(pageToken);

        List<Spu> spus = spuRepository.findByResource(resourceType, resourceId, normalizedPageSize + 1, afterId);

        boolean hasMore = spus.size() > normalizedPageSize;
        if (hasMore) {
            spus = spus.subList(0, normalizedPageSize);
        }

        String nextPageToken = null;
        if (hasMore && !spus.isEmpty()) {
            String lastId = spus.getLast().getId();
            nextPageToken = CursorTokenUtil.encode(new CursorToken(lastId));
        }

        return new SpuPage(spus, nextPageToken);
    }

    private int normalizePageSize(int pageSize) {
        if (pageSize <= 0) return DEFAULT_PAGE_SIZE;
        return Math.min(pageSize, MAX_PAGE_SIZE);
    }

    private String decodeAfterIdOrNull(String pageToken) {
        if (pageToken == null || pageToken.isEmpty()) return null;
        try {
            return CursorTokenUtil.decode(pageToken).id();
        } catch (IllegalArgumentException e) {
            log.warn("Invalid page token, starting from beginning: {}", pageToken);
            return null;
        }
    }
}
