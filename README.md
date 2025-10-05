# TripSphere

Refresh protobuf files for a specific service. For example, for trip-itinerary-service:

```shell
make refresh-protos SERVICE=trip-itinerary-service
```

This will copy the protobuf files from `contracts/protobuf` to a `proto` directory of the specified service.

Then compile the protobuf files. For example, for trip-itinerary-service:

```shell
make compile-protos SERVICE=trip-itinerary-service
```