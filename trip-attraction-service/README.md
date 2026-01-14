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
java -jar target/attraction-0.0.1-SNAPSHOT.jar
```

