# TripSphere

Refresh proto files for a specific service, for example:

```shell
scripts/refresh-protos.sh trip-itinerary-service
```

This will copy the latest proto files from `contracts/protobuf` into somewhere `proto` directory of the specified service. Then cd into the service directory and run its command to regenerate the gRPC code.