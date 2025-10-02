First, generate the gRPC code:

```shell
mvnw clean
mvnw protobuf:compile
mvnw protobuf:compile-custom
```

Then, build jar package:

```shell
mvnw package
```

Finally, start the server:

```shell
java -jar target/trip-note-service-0.1.0.jar
```