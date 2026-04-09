To generate the gRPC java code:

```bash
task gen-proto
```

Then, build jar package:

```bash
./mvnw package -DskipTests
```

Finally, start the server:

```bash
java -jar target/order-${project.version}.jar
```