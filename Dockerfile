# Build stage for Java engine
FROM maven:3.9-eclipse-temurin-21 AS engine-build
COPY engine /app/engine
WORKDIR /app/engine
RUN mvn clean package -DskipTests

# Build stage for C collector
FROM gcc:latest AS collector-build
COPY collector /app/collector
WORKDIR /app/collector
RUN make

# Final stage
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=engine-build /app/engine/target/sentry-engine-1.0.jar /app/engine.jar
COPY --from=collector-build /app/collector/sentry_collector /app/collector
COPY assets /app/assets

# Note: Requires --net=host and -v /proc:/proc:ro to function correctly
ENTRYPOINT ["/bin/bash", "-c", "/app/collector 1 | java -jar /app/engine.jar"]
