FROM eclipse-temurin:17-jdk AS builder

WORKDIR /app

ARG ALIYUN_MIRROR=false

COPY .mvn/ .mvn/
COPY mvnw mvnw.cmd ./
RUN chmod +x mvnw
COPY pom.xml ./

RUN <<EOF cat > /tmp/settings.xml
<?xml version="1.0" encoding="UTF-8"?>
<settings>
    <mirrors>
        <mirror>
            <id>aliyun-maven</id>
            <mirrorOf>*</mirrorOf>
            <name>Aliyun Maven Repository</name>
            <url>https://maven.aliyun.com/repository/public</url>
        </mirror>
    </mirrors>
</settings>
EOF

RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw -B dependency:go-offline $([ "$ALIYUN_MIRROR" = "true" ] && echo "-s /tmp/settings.xml")

COPY src ./src

RUN ./mvnw -B clean package -DskipTests $([ "$ALIYUN_MIRROR" = "true" ] && echo "-s /tmp/settings.xml")


FROM eclipse-temurin:17-jre

# Setup a non-root user
RUN addgroup --system nonroot \
 && adduser --system nonroot --ingroup nonroot

ARG JAR=target/user-*.jar
COPY --from=builder --chown=nonroot:nonroot /app/${JAR} app.jar

# Use the non-root user to run our application
USER nonroot

# Default gRPC port
EXPOSE 50056
# Default HTTP port
EXPOSE 24217

ENTRYPOINT ["java", "-jar", "app.jar"]
