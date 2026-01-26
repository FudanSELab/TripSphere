FROM eclipse-temurin:21-jdk AS builder

WORKDIR /app

ARG MAVEN_MIRROR_URL

COPY .mvn/ .mvn/
COPY mvnw mvnw.cmd ./
RUN chmod +x mvnw
COPY pom.xml ./

RUN <<EOF cat > /tmp/settings.xml
<?xml version="1.0" encoding="UTF-8"?>
<settings>
    <mirrors>
        <mirror>
            <id>maven-mirror</id>
            <mirrorOf>*</mirrorOf>
            <name>Maven Mirror Repository</name>
            <url>${MAVEN_MIRROR_URL}</url>
        </mirror>
    </mirrors>
</settings>
EOF

RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw -B dependency:go-offline $([ -n "$MAVEN_MIRROR_URL" ] && echo "-s /tmp/settings.xml")

COPY src ./src

RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw -B clean package -DskipTests $([ -n "$MAVEN_MIRROR_URL" ] && echo "-s /tmp/settings.xml")


FROM eclipse-temurin:21-jre

ARG OTEL_JAVA_AGENT_VERSION=2.23.0

WORKDIR /app

# Setup a non-root user
RUN addgroup --system nonroot \
 && adduser --system nonroot --ingroup nonroot

ARG JAR=target/hotel-*.jar
COPY --from=builder --chown=nonroot:nonroot /app/${JAR} app.jar
ADD --chmod=644 \
    https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v${OTEL_JAVA_AGENT_VERSION}/opentelemetry-javaagent.jar \
    /app/opentelemetry-javaagent.jar
ENV JAVA_TOOL_OPTIONS=-javaagent:/app/opentelemetry-javaagent.jar
ENV OTEL_SERVICE_NAME="trip-hotel-service" \
    OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318

# Use the non-root user to run our application
USER nonroot

# Default gRPC port
EXPOSE 50054
# Default HTTP port
EXPOSE 24214

ENTRYPOINT ["java", "-jar", "app.jar"]
