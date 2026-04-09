package org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc;

import io.grpc.stub.StreamObserver;
import java.util.ArrayList;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.itinerary.application.dto.*;
import org.tripsphere.itinerary.application.exception.InvalidArgumentException;
import org.tripsphere.itinerary.application.service.AuthorizationService;
import org.tripsphere.itinerary.application.service.command.*;
import org.tripsphere.itinerary.application.service.query.GetItineraryUseCase;
import org.tripsphere.itinerary.application.service.query.ListUserItinerariesUseCase;
import org.tripsphere.itinerary.domain.model.Activity;
import org.tripsphere.itinerary.domain.model.DayPlan;
import org.tripsphere.itinerary.domain.model.Itinerary;
import org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.mapper.ActivityProtoMapper;
import org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.mapper.DayPlanProtoMapper;
import org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.mapper.ItineraryProtoMapper;
import org.tripsphere.itinerary.infrastructure.security.GrpcAuthContext;
import org.tripsphere.itinerary.v1.*;
import org.tripsphere.itinerary.v1.ItineraryServiceGrpc.ItineraryServiceImplBase;

@GrpcService
@RequiredArgsConstructor
public class ItineraryGrpcService extends ItineraryServiceImplBase {

    private final CreateItineraryUseCase createItineraryUseCase;
    private final UpdateItineraryUseCase updateItineraryUseCase;
    private final ReplaceItineraryUseCase replaceItineraryUseCase;
    private final DeleteItineraryUseCase deleteItineraryUseCase;
    private final AddDayPlanUseCase addDayPlanUseCase;
    private final DeleteDayPlanUseCase deleteDayPlanUseCase;
    private final AddActivityUseCase addActivityUseCase;
    private final UpdateActivityUseCase updateActivityUseCase;
    private final DeleteActivityUseCase deleteActivityUseCase;
    private final GetItineraryUseCase getItineraryUseCase;
    private final ListUserItinerariesUseCase listUserItinerariesUseCase;
    private final AuthorizationService authorizationService;
    private final ItineraryProtoMapper itineraryProtoMapper;
    private final DayPlanProtoMapper dayPlanProtoMapper;
    private final ActivityProtoMapper activityProtoMapper;

    @Override
    public void createItinerary(
            CreateItineraryRequest request, StreamObserver<CreateItineraryResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();
        authorizationService.requireAuthenticated(authContext);

        if (!request.hasItinerary()) {
            throw InvalidArgumentException.required("itinerary");
        }

        org.tripsphere.itinerary.v1.Itinerary proto = request.getItinerary();
        Itinerary mapped = itineraryProtoMapper.toDomain(proto);

        CreateItineraryCommand command = new CreateItineraryCommand(
                authContext.getUserId(),
                mapped.getTitle(),
                mapped.getDestinationPoiId(),
                mapped.getDestinationName(),
                mapped.getStartDate(),
                mapped.getEndDate(),
                mapped.getDayPlans() != null ? new ArrayList<>(mapped.getDayPlans()) : new ArrayList<>(),
                mapped.getMetadata(),
                mapped.getSummary(),
                mapped.getMarkdownContent());

        Itinerary created = createItineraryUseCase.execute(command);

        responseObserver.onNext(CreateItineraryResponse.newBuilder()
                .setItinerary(itineraryProtoMapper.toProto(created))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void getItinerary(GetItineraryRequest request, StreamObserver<GetItineraryResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (request.getId().isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        authorizationService.checkItineraryAccess(authContext, request.getId());

        Itinerary itinerary = getItineraryUseCase.execute(request.getId());

        responseObserver.onNext(GetItineraryResponse.newBuilder()
                .setItinerary(itineraryProtoMapper.toProto(itinerary))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void listUserItineraries(
            ListUserItinerariesRequest request, StreamObserver<ListUserItinerariesResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (request.getUserId().isEmpty()) {
            throw InvalidArgumentException.required("user_id");
        }

        authorizationService.checkListAccess(authContext, request.getUserId());

        ListItinerariesQuery query =
                new ListItinerariesQuery(request.getUserId(), request.getPageSize(), request.getPageToken());

        ItineraryPage result = listUserItinerariesUseCase.execute(query);

        ListUserItinerariesResponse.Builder responseBuilder = ListUserItinerariesResponse.newBuilder()
                .addAllItineraries(itineraryProtoMapper.toProtoList(result.items()));

        if (result.nextPageToken() != null) {
            responseBuilder.setNextPageToken(result.nextPageToken());
        }

        responseObserver.onNext(responseBuilder.build());
        responseObserver.onCompleted();
    }

    @Override
    public void deleteItinerary(
            DeleteItineraryRequest request, StreamObserver<DeleteItineraryResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (request.getId().isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        authorizationService.checkItineraryAccess(authContext, request.getId());
        deleteItineraryUseCase.execute(request.getId());

        responseObserver.onNext(DeleteItineraryResponse.newBuilder().build());
        responseObserver.onCompleted();
    }

    @Override
    public void updateItinerary(
            UpdateItineraryRequest request, StreamObserver<UpdateItineraryResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (!request.hasItinerary()) {
            throw InvalidArgumentException.required("itinerary");
        }
        if (request.getItinerary().getId().isEmpty()) {
            throw InvalidArgumentException.required("itinerary.id");
        }

        authorizationService.checkItineraryAccess(
                authContext, request.getItinerary().getId());

        Itinerary mapped = itineraryProtoMapper.toDomain(request.getItinerary());

        UpdateItineraryCommand command = new UpdateItineraryCommand(
                request.getItinerary().getId(),
                mapped.getTitle(),
                mapped.getStartDate(),
                mapped.getEndDate(),
                mapped.getDestinationName(),
                mapped.getMarkdownContent(),
                mapped.getSummary());

        Itinerary updated = updateItineraryUseCase.execute(command);

        responseObserver.onNext(UpdateItineraryResponse.newBuilder()
                .setItinerary(itineraryProtoMapper.toProto(updated))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void replaceItinerary(
            ReplaceItineraryRequest request, StreamObserver<ReplaceItineraryResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (request.getId().isEmpty()) {
            throw InvalidArgumentException.required("id");
        }
        if (!request.hasItinerary()) {
            throw InvalidArgumentException.required("itinerary");
        }

        authorizationService.checkItineraryAccess(authContext, request.getId());

        Itinerary mapped = itineraryProtoMapper.toDomain(request.getItinerary());

        ReplaceItineraryCommand command = new ReplaceItineraryCommand(
                request.getId(),
                mapped.getTitle(),
                mapped.getDestinationPoiId(),
                mapped.getDestinationName(),
                mapped.getStartDate(),
                mapped.getEndDate(),
                mapped.getDayPlans() != null ? new ArrayList<>(mapped.getDayPlans()) : new ArrayList<>(),
                mapped.getMetadata(),
                mapped.getSummary(),
                mapped.getMarkdownContent());

        Itinerary replaced = replaceItineraryUseCase.execute(command);

        responseObserver.onNext(ReplaceItineraryResponse.newBuilder()
                .setItinerary(itineraryProtoMapper.toProto(replaced))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void addDayPlan(AddDayPlanRequest request, StreamObserver<AddDayPlanResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (request.getItineraryId().isEmpty()) {
            throw InvalidArgumentException.required("itinerary_id");
        }
        if (!request.hasDayPlan()) {
            throw InvalidArgumentException.required("day_plan");
        }

        authorizationService.checkItineraryAccess(authContext, request.getItineraryId());

        DayPlan dayPlan = dayPlanProtoMapper.toDomain(request.getDayPlan());
        AddDayPlanCommand command = new AddDayPlanCommand(request.getItineraryId(), dayPlan);

        DayPlan added = addDayPlanUseCase.execute(command);

        responseObserver.onNext(AddDayPlanResponse.newBuilder()
                .setDayPlan(dayPlanProtoMapper.toProto(added))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void deleteDayPlan(DeleteDayPlanRequest request, StreamObserver<DeleteDayPlanResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (request.getItineraryId().isEmpty()) {
            throw InvalidArgumentException.required("itinerary_id");
        }
        if (request.getDayPlanId().isEmpty()) {
            throw InvalidArgumentException.required("day_plan_id");
        }

        authorizationService.checkItineraryAccess(authContext, request.getItineraryId());
        deleteDayPlanUseCase.execute(request.getItineraryId(), request.getDayPlanId());

        responseObserver.onNext(DeleteDayPlanResponse.newBuilder().build());
        responseObserver.onCompleted();
    }

    @Override
    public void addActivity(AddActivityRequest request, StreamObserver<AddActivityResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (request.getItineraryId().isEmpty()) {
            throw InvalidArgumentException.required("itinerary_id");
        }
        if (request.getDayPlanId().isEmpty()) {
            throw InvalidArgumentException.required("day_plan_id");
        }
        if (!request.hasActivity()) {
            throw InvalidArgumentException.required("activity");
        }

        authorizationService.checkItineraryAccess(authContext, request.getItineraryId());

        Activity activity = activityProtoMapper.toDomain(request.getActivity());
        AddActivityCommand command = new AddActivityCommand(
                request.getItineraryId(), request.getDayPlanId(), activity, request.getInsertIndex());

        Activity added = addActivityUseCase.execute(command);

        responseObserver.onNext(AddActivityResponse.newBuilder()
                .setActivity(activityProtoMapper.toProto(added))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void updateActivity(UpdateActivityRequest request, StreamObserver<UpdateActivityResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (!request.hasActivity()) {
            throw InvalidArgumentException.required("activity");
        }
        if (request.getActivity().getId().isEmpty()) {
            throw InvalidArgumentException.required("activity.id");
        }

        authorizationService.checkActivityAccess(
                authContext, request.getActivity().getId());

        Activity activity = activityProtoMapper.toDomain(request.getActivity());
        UpdateActivityCommand command = new UpdateActivityCommand(activity);

        Activity updated = updateActivityUseCase.execute(command);

        responseObserver.onNext(UpdateActivityResponse.newBuilder()
                .setActivity(activityProtoMapper.toProto(updated))
                .build());
        responseObserver.onCompleted();
    }

    @Override
    public void deleteActivity(DeleteActivityRequest request, StreamObserver<DeleteActivityResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (request.getItineraryId().isEmpty()) {
            throw InvalidArgumentException.required("itinerary_id");
        }
        if (request.getDayPlanId().isEmpty()) {
            throw InvalidArgumentException.required("day_plan_id");
        }
        if (request.getActivityId().isEmpty()) {
            throw InvalidArgumentException.required("activity_id");
        }

        authorizationService.checkItineraryAccess(authContext, request.getItineraryId());
        deleteActivityUseCase.execute(request.getItineraryId(), request.getDayPlanId(), request.getActivityId());

        responseObserver.onNext(DeleteActivityResponse.newBuilder().build());
        responseObserver.onCompleted();
    }
}
