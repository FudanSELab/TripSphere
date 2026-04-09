package org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.advice;

import io.grpc.Status;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.advice.GrpcAdvice;
import net.devh.boot.grpc.server.advice.GrpcExceptionHandler;
import org.tripsphere.itinerary.application.exception.BusinessException;
import org.tripsphere.itinerary.domain.exception.ActivityNotFoundException;
import org.tripsphere.itinerary.domain.exception.DayPlanNotFoundException;
import org.tripsphere.itinerary.domain.exception.ItineraryDomainException;

@Slf4j
@GrpcAdvice
public class GrpcExceptionAdvice {

    @GrpcExceptionHandler(BusinessException.class)
    public Status handleBusinessException(BusinessException e) {
        log.warn("Business exception: {}", e.getMessage());
        return e.toGrpcStatus();
    }

    @GrpcExceptionHandler(DayPlanNotFoundException.class)
    public Status handleDayPlanNotFoundException(DayPlanNotFoundException e) {
        log.warn("DayPlan not found: {}", e.getMessage());
        return Status.NOT_FOUND.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(ActivityNotFoundException.class)
    public Status handleActivityNotFoundException(ActivityNotFoundException e) {
        log.warn("Activity not found: {}", e.getMessage());
        return Status.NOT_FOUND.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(ItineraryDomainException.class)
    public Status handleDomainException(ItineraryDomainException e) {
        log.warn("Domain exception: {}", e.getMessage());
        return Status.INTERNAL.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(IllegalArgumentException.class)
    public Status handleIllegalArgumentException(IllegalArgumentException e) {
        log.warn("Illegal argument: {}", e.getMessage());
        return Status.INVALID_ARGUMENT.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(NullPointerException.class)
    public Status handleNullPointerException(NullPointerException e) {
        log.error("Null pointer exception", e);
        return Status.INTERNAL.withDescription("Internal error: null reference");
    }

    @GrpcExceptionHandler(Exception.class)
    public Status handleException(Exception e) {
        log.error("Unexpected exception in gRPC service", e);
        return Status.INTERNAL.withDescription("Internal server error: " + e.getMessage());
    }
}
