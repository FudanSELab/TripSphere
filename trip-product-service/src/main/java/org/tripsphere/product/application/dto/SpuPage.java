package org.tripsphere.product.application.dto;

import java.util.List;
import org.tripsphere.product.domain.model.Spu;

public record SpuPage(List<Spu> spus, String nextPageToken) {}
