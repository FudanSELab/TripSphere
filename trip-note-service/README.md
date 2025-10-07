To generate the gRPC java code:

```bash
./mvnw clean
./mvnw protobuf:compile
./mvnw protobuf:compile-custom
```

Then, build jar package:

```bash
./mvnw package
```

Finally, start the server:

```bash
java -jar target/trip-note-service-0.1.0.jar
```