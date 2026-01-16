FROM eclipse-temurin:17-jdk AS builder

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

RUN ./mvnw -B clean package -DskipTests $([ -n "$MAVEN_MIRROR_URL" ] && echo "-s /tmp/settings.xml")


FROM eclipse-temurin:17-jre

# Setup a non-root user
RUN addgroup --system nonroot \
 && adduser --system nonroot --ingroup nonroot

ARG JAR=target/attraction-*.jar
COPY --from=builder --chown=nonroot:nonroot /app/${JAR} app.jar

# Use the non-root user to run our application
USER nonroot

# Default gRPC port
EXPOSE 50053
# Default HTTP port
EXPOSE 24213

ENTRYPOINT ["java", "-jar", "app.jar"]

