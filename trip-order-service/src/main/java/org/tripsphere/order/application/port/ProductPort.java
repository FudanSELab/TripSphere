package org.tripsphere.order.application.port;

import java.util.List;
import org.tripsphere.order.application.dto.SkuInfo;
import org.tripsphere.order.application.dto.SpuInfo;

public interface ProductPort {

    List<SkuInfo> batchGetSkus(List<String> skuIds);

    List<SpuInfo> batchGetSpus(List<String> spuIds);
}
