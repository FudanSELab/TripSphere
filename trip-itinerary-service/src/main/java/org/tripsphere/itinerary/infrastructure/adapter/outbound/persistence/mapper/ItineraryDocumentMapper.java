package org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.mapper;

import java.math.BigDecimal;
import java.util.Currency;
import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.itinerary.domain.model.*;
import org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.document.*;

@Mapper(
        componentModel = "spring",
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface ItineraryDocumentMapper {

    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    ItineraryDocument toDocument(Itinerary itinerary);

    Itinerary toDomain(ItineraryDocument document);

    List<Itinerary> toDomainList(List<ItineraryDocument> documents);

    DayPlanDocument toDayPlanDocument(DayPlan dayPlan);

    DayPlan toDayPlanDomain(DayPlanDocument document);

    ActivityDocument toActivityDocument(Activity activity);

    Activity toActivityDomain(ActivityDocument document);

    ItinerarySummaryDocument toSummaryDocument(ItinerarySummary summary);

    ItinerarySummary toSummaryDomain(ItinerarySummaryDocument document);

    GeoPointDocument toGeoPointDocument(GeoPoint geoPoint);

    GeoPoint toGeoPointDomain(GeoPointDocument document);

    AddressDocument toAddressDocument(Address address);

    Address toAddressDomain(AddressDocument document);

    default MoneyDocument toMoneyDocument(Money money) {
        if (money == null) return null;
        return MoneyDocument.builder()
                .currencyCode(money.currency().getCurrencyCode())
                .amount(money.amount())
                .build();
    }

    default Money toMoneyDomain(MoneyDocument document) {
        if (document == null) return null;
        Currency currency = Currency.getInstance(document.getCurrencyCode());
        BigDecimal amount = document.getAmount() != null ? document.getAmount() : BigDecimal.ZERO;
        return new Money(currency, amount);
    }

    default String activityKindToString(ActivityKind kind) {
        return kind != null ? kind.name() : null;
    }

    default ActivityKind stringToActivityKind(String kind) {
        if (kind == null || kind.isEmpty()) return ActivityKind.UNSPECIFIED;
        try {
            return ActivityKind.valueOf(kind);
        } catch (IllegalArgumentException e) {
            return ActivityKind.UNSPECIFIED;
        }
    }
}
