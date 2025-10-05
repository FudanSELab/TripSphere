FROM eclipse-temurin:17-jdk AS builder

WORKDIR /app

COPY .mvn/ .mvn/
COPY mvnw mvnw.cmd ./
COPY pom.xml ./

RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw -B dependency:go-offline

COPY src ./src

RUN ./mvnw -B clean package -DskipTests


FROM eclipse-temurin:17-jre-alpine

# Setup a non-root user
RUN addgroup --system nonroot \
 && adduser --system nonroot --ingroup nonroot

ARG JAR=target/trip-note-service-*.jar
COPY --from=builder --chown=nonroot:nonroot /app/${JAR} app.jar

# Use the non-root user to run our application
USER nonroot

EXPOSE 9090

ENTRYPOINT ["java", "-jar", "app.jar"]