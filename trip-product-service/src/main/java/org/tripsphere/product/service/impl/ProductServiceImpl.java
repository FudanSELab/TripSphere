package org.tripsphere.product.service.impl;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.product.exception.NotFoundException;
import org.tripsphere.product.mapper.SkuMapper;
import org.tripsphere.product.mapper.SpuMapper;
import org.tripsphere.product.model.SkuDoc;
import org.tripsphere.product.model.SpuDoc;
import org.tripsphere.product.repository.SpuDocRepository;
import org.tripsphere.product.service.ProductService;
import org.tripsphere.product.v1.Sku;
import org.tripsphere.product.v1.Spu;

@Slf4j
@Service
@RequiredArgsConstructor
public class ProductServiceImpl implements ProductService {

    private final SpuDocRepository spuDocRepository;
    private final SpuMapper spuMapper = SpuMapper.INSTANCE;
    private final SkuMapper skuMapper = SkuMapper.INSTANCE;

    private static final int DEFAULT_PAGE_SIZE = 20;
    private static final int MAX_PAGE_SIZE = 100;
    private static final String CURSOR_SEPARATOR = "|";

    @Override
    public Spu createSpu(Spu spu) {
        log.debug("Creating SPU: {}", spu.getName());
        SpuDoc doc = spuMapper.toDoc(spu);
        doc.setId(null);
        if (doc.getSkus() != null) {
            for (SkuDoc sku : doc.getSkus()) {
                if (sku.getId() == null || sku.getId().isEmpty()) {
                    sku.setId(UUID.randomUUID().toString());
                }
            }
        }
        if (doc.getStatus() == null || doc.getStatus().equals("DRAFT")) {
            doc.setStatus("DRAFT");
        }

        SpuDoc saved = spuDocRepository.save(doc);
        log.info("Created SPU with id: {}", saved.getId());
        return spuMapper.toProto(saved);
    }

    @Override
    public List<Spu> batchCreateSpus(List<Spu> spus) {
        log.debug("Batch creating {} SPUs", spus.size());
        List<SpuDoc> docs = new ArrayList<>();
        for (Spu spu : spus) {
            SpuDoc doc = spuMapper.toDoc(spu);
            doc.setId(null);
            if (doc.getSkus() != null) {
                for (SkuDoc sku : doc.getSkus()) {
                    if (sku.getId() == null || sku.getId().isEmpty()) {
                        sku.setId(UUID.randomUUID().toString());
                    }
                }
            }
            if (doc.getStatus() == null) {
                doc.setStatus("DRAFT");
            }
            docs.add(doc);
        }
        List<SpuDoc> saved = spuDocRepository.saveAll(docs);
        log.info("Batch created {} SPUs", saved.size());
        return spuMapper.toProtoList(saved);
    }

    @Override
    public Optional<Spu> getSpuById(String id) {
        log.debug("Finding SPU by id: {}", id);
        return spuDocRepository.findById(id).map(spuMapper::toProto);
    }

    @Override
    public List<Spu> batchGetSpus(List<String> ids) {
        log.debug("Batch getting SPUs, count: {}", ids.size());
        List<SpuDoc> docs = spuDocRepository.findAllById(ids);
        return spuMapper.toProtoList(docs);
    }

    @Override
    public SpuPage listSpusByResource(
            String resourceType, String resourceId, int pageSize, String pageToken) {
        log.debug(
                "Listing SPUs by resource: type={}, id={}, pageSize={}, pageToken={}",
                resourceType,
                resourceId,
                pageSize,
                pageToken);

        // Normalize page size
        int normalizedPageSize = normalizePageSize(pageSize);

        // Decode cursor from page token
        CursorToken cursor = decodeCursorToken(pageToken);

        // Fetch one extra to determine if there are more results
        List<SpuDoc> docs =
                spuDocRepository.findByResourceWithCursor(
                        resourceType,
                        resourceId,
                        normalizedPageSize + 1,
                        cursor != null ? cursor.createdAt() : null,
                        cursor != null ? cursor.id() : null);

        boolean hasMore = docs.size() > normalizedPageSize;
        if (hasMore) {
            docs = docs.subList(0, normalizedPageSize);
        }

        List<Spu> spus = spuMapper.toProtoList(docs);

        // Generate next page token from the last item's cursor values
        String nextPageToken = null;
        if (hasMore && !docs.isEmpty()) {
            SpuDoc lastDoc = docs.get(docs.size() - 1);
            nextPageToken = encodeCursorToken(lastDoc.getCreatedAt(), lastDoc.getId());
        }

        return new SpuPage(spus, nextPageToken);
    }

    @Override
    public Spu updateSpu(Spu spu, List<String> fieldPaths) {
        String id = spu.getId();
        log.debug("Updating SPU id={}, fields={}", id, fieldPaths);

        if (!spuDocRepository.existsById(id)) {
            throw new NotFoundException("SPU", id);
        }

        SpuDoc updates = spuMapper.toDoc(spu);
        spuDocRepository.updateSpuFields(id, updates, fieldPaths);

        SpuDoc updated =
                spuDocRepository.findById(id).orElseThrow(() -> new NotFoundException("SPU", id));
        return spuMapper.toProto(updated);
    }

    @Override
    public Optional<Sku> getSkuById(String skuId) {
        log.debug("Finding SKU by id: {}", skuId);
        return spuDocRepository
                .findBySkuId(skuId)
                .flatMap(
                        spuDoc -> {
                            if (spuDoc.getSkus() == null) return Optional.empty();
                            return spuDoc.getSkus().stream()
                                    .filter(sku -> skuId.equals(sku.getId()))
                                    .findFirst()
                                    .map(skuDoc -> skuMapper.toProto(skuDoc, spuDoc.getId()));
                        });
    }

    @Override
    public List<Sku> batchGetSkus(List<String> skuIds) {
        log.debug("Batch getting SKUs, count: {}", skuIds.size());

        List<SpuDoc> spuDocs = spuDocRepository.findBySkuIds(skuIds);
        Set<String> requestedIds = new HashSet<>(skuIds);
        List<Sku> result = new ArrayList<>();

        for (SpuDoc spuDoc : spuDocs) {
            if (spuDoc.getSkus() != null) {
                for (SkuDoc skuDoc : spuDoc.getSkus()) {
                    if (requestedIds.contains(skuDoc.getId())) {
                        result.add(skuMapper.toProto(skuDoc, spuDoc.getId()));
                    }
                }
            }
        }
        return result;
    }

    // ==================== Helper Methods ====================

    private int normalizePageSize(int pageSize) {
        if (pageSize <= 0) {
            return DEFAULT_PAGE_SIZE;
        }
        return Math.min(pageSize, MAX_PAGE_SIZE);
    }

    // ==================== Cursor Token Methods ====================

    /** Cursor token containing the pagination cursor values. */
    private record CursorToken(Instant createdAt, String id) {}

    /**
     * Encodes cursor values into a Base64 page token. Format: "epochMillis|id" encoded in Base64.
     */
    private String encodeCursorToken(Instant createdAt, String id) {
        String raw = createdAt.toEpochMilli() + CURSOR_SEPARATOR + id;
        return Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(raw.getBytes(StandardCharsets.UTF_8));
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
            String decoded =
                    new String(Base64.getUrlDecoder().decode(pageToken), StandardCharsets.UTF_8);
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
