package org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.document;

import java.math.BigDecimal;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class MoneyDocument {
    private String currencyCode;
    private BigDecimal amount;
}
