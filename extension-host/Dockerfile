# Extension host: runs Keiyoushi extensions (JARs) behind an HTTP API.
# Prerequisite: tools/vendor.sh has produced vendor/*.jar on the build machine (not in git).
FROM eclipse-temurin:21-jdk AS build
WORKDIR /src
COPY gradle/ gradle/
COPY gradlew settings.gradle.kts build.gradle.kts ./
RUN chmod +x gradlew && ./gradlew --no-daemon -q dependencies > /dev/null || true
COPY vendor/ vendor/
COPY src/ src/
RUN ./gradlew --no-daemon -q jar installLib

FROM eclipse-temurin:21-jre
RUN useradd --system --uid 10001 --create-home host
WORKDIR /app
COPY --from=build /src/build/libs/extension-host.jar /app/extension-host.jar
COPY --from=build /src/build/lib/ /app/lib/
ENV HOST_PORT=8800 \
    HOST_DATA_DIR=/data
VOLUME ["/data"]
EXPOSE 8800
USER host
ENTRYPOINT ["java", "-cp", "/app/extension-host.jar:/app/lib/*", "eu.kanade.tachiyomi.host.MainKt"]
