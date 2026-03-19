package org.tripsphere.itinerary.api.grpc;

import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import net.devh.boot.grpc.server.service.GrpcService;
import org.tripsphere.itinerary.exception.InvalidArgumentException;
import org.tripsphere.itinerary.security.GrpcAuthContext;
import org.tripsphere.itinerary.service.AuthorizationService;
import org.tripsphere.itinerary.service.ItineraryService;
import org.tripsphere.itinerary.service.ItineraryService.PageResult;
import org.tripsphere.itinerary.v1.Activity;
import org.tripsphere.itinerary.v1.AddActivityRequest;
import org.tripsphere.itinerary.v1.AddActivityResponse;
import org.tripsphere.itinerary.v1.AddDayPlanRequest;
import org.tripsphere.itinerary.v1.AddDayPlanResponse;
import org.tripsphere.itinerary.v1.CreateItineraryRequest;
import org.tripsphere.itinerary.v1.CreateItineraryResponse;
import org.tripsphere.itinerary.v1.DayPlan;
import org.tripsphere.itinerary.v1.DeleteActivityRequest;
import org.tripsphere.itinerary.v1.DeleteActivityResponse;
import org.tripsphere.itinerary.v1.DeleteDayPlanRequest;
import org.tripsphere.itinerary.v1.DeleteDayPlanResponse;
import org.tripsphere.itinerary.v1.DeleteItineraryRequest;
import org.tripsphere.itinerary.v1.DeleteItineraryResponse;
import org.tripsphere.itinerary.v1.GetItineraryRequest;
import org.tripsphere.itinerary.v1.GetItineraryResponse;
import org.tripsphere.itinerary.v1.Itinerary;
import org.tripsphere.itinerary.v1.ItineraryServiceGrpc.ItineraryServiceImplBase;
import org.tripsphere.itinerary.v1.ListUserItinerariesRequest;
import org.tripsphere.itinerary.v1.ListUserItinerariesResponse;
import org.tripsphere.itinerary.v1.ReplaceItineraryRequest;
import org.tripsphere.itinerary.v1.ReplaceItineraryResponse;
import org.tripsphere.itinerary.v1.UpdateActivityRequest;
import org.tripsphere.itinerary.v1.UpdateActivityResponse;
import org.tripsphere.itinerary.v1.UpdateItineraryRequest;
import org.tripsphere.itinerary.v1.UpdateItineraryResponse;

@GrpcService
@RequiredArgsConstructor
public class ItineraryGrpcService extends ItineraryServiceImplBase {

    private final ItineraryService itineraryService;
    private final AuthorizationService authorizationService;

    @Override
    public void createItinerary(
            CreateItineraryRequest request, StreamObserver<CreateItineraryResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();
        authorizationService.requireAuthenticated(authContext);

        if (!request.hasItinerary()) {
            throw InvalidArgumentException.required("itinerary");
        }

        // Override user_id with authenticated user's ID
        Itinerary requestItinerary = request.getItinerary();
        Itinerary itineraryWithUser =
                requestItinerary.toBuilder().setUserId(authContext.getUserId()).build();

        Itinerary created = itineraryService.createItinerary(itineraryWithUser);

        responseObserver.onNext(
                CreateItineraryResponse.newBuilder().setItinerary(created).build());
        responseObserver.onCompleted();
    }

    @Override
    public void getItinerary(GetItineraryRequest request, StreamObserver<GetItineraryResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (request.getId().isEmpty()) {
            throw InvalidArgumentException.required("id");
        }

        // Check access permission
        authorizationService.checkItineraryAccess(authContext, request.getId());

        Itinerary itinerary = itineraryService.getItinerary(request.getId());

        responseObserver.onNext(
                GetItineraryResponse.newBuilder().setItinerary(itinerary).build());
        responseObserver.onCompleted();
    }

    @Override
    public void listUserItineraries(
            ListUserItinerariesRequest request, StreamObserver<ListUserItinerariesResponse> responseObserver) {
        GrpcAuthContext authContext = GrpcAuthContext.current();

        if (request.getUserId().isEmpty()) {
            throw InvalidArgumentException.required("user_id");
        }

        // Check if user can list itineraries for the target user
        authorizationService.checkListAccess(authContext, request.getUserId());

        PageResult<Itinerary> result = itineraryService.listUserItineraries(
                request.getUserId(), request.getPageSize(), request.getPageToken());

        ListUserItinerariesResponse.Builder responseBuilder =
                ListUserItinerariesResponse.newBuilder().addAllItineraries(result.items());

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

        itineraryService.deleteItinerary(request.getId());

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

        Itinerary updated = itineraryService.updateItinerary(request.getItinerary());

        responseObserver.onNext(
                UpdateItineraryResponse.newBuilder().setItinerary(updated).build());
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

        Itinerary replaced = itineraryService.replaceItinerary(request.getId(), request.getItinerary());

        responseObserver.onNext(
                ReplaceItineraryResponse.newBuilder().setItinerary(replaced).build());
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

        // Check access permission
        authorizationService.checkItineraryAccess(authContext, request.getItineraryId());

        DayPlan added = itineraryService.addDayPlan(request.getItineraryId(), request.getDayPlan());

        responseObserver.onNext(
                AddDayPlanResponse.newBuilder().setDayPlan(added).build());
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

        // Check access permission
        authorizationService.checkItineraryAccess(authContext, request.getItineraryId());

        itineraryService.deleteDayPlan(request.getItineraryId(), request.getDayPlanId());

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

        // Check access permission
        authorizationService.checkItineraryAccess(authContext, request.getItineraryId());

        Activity added = itineraryService.addActivity(
                request.getItineraryId(), request.getDayPlanId(), request.getActivity(), request.getInsertIndex());

        responseObserver.onNext(
                AddActivityResponse.newBuilder().setActivity(added).build());
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

        // Look up itinerary by activity ID, then check access permission
        authorizationService.checkActivityAccess(
                authContext, request.getActivity().getId());

        Activity updated = itineraryService.updateActivity(request.getActivity());

        responseObserver.onNext(
                UpdateActivityResponse.newBuilder().setActivity(updated).build());
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

        // Check access permission
        authorizationService.checkItineraryAccess(authContext, request.getItineraryId());

        itineraryService.deleteActivity(request.getItineraryId(), request.getDayPlanId(), request.getActivityId());

        responseObserver.onNext(DeleteActivityResponse.newBuilder().build());
        responseObserver.onCompleted();
    }
}
