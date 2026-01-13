FROM alpine:latest AS builder

# Install Java and Maven
RUN apk add --no-cache openjdk17 maven

WORKDIR /app

COPY trip-user-service/.mvn/ .mvn/
COPY trip-user-service/mvnw trip-user-service/mvnw.cmd ./
COPY trip-user-service/pom.xml ./

# Make mvnw executable
RUN chmod +x mvnw

RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw -B dependency:go-offline

# Copy entire project for protobuf generation
COPY contracts /contracts
COPY trip-user-service/src ./src

# Generate protobuf code first
RUN ./mvnw protobuf:compile protobuf:compile-custom

RUN ./mvnw -B clean package -DskipTests


FROM alpine:latest

# Install Java JRE
RUN apk add --no-cache openjdk17-jre

# Setup a non-root user
RUN addgroup -S nonroot && \
    adduser -S nonroot -G nonroot

ARG JAR=target/trip-user-service-*.jar
COPY --from=builder --chown=nonroot:nonroot /app/${JAR} app.jar

# Use the non-root user to run our application
USER nonroot

EXPOSE 9007

ENTRYPOINT ["java", "-jar", "app.jar"]
