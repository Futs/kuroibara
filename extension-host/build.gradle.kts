plugins {
    kotlin("jvm") version "2.4.10"
    kotlin("plugin.serialization") version "2.4.10"
}

repositories { mavenCentral(); maven("https://jitpack.io") }


dependencies {
    implementation("com.squareup.okhttp3:okhttp:5.5.0")
    implementation("com.squareup.okio:okio-jvm:3.17.0")
    implementation("org.jsoup:jsoup:1.22.2")
    implementation("io.reactivex:rxjava:1.3.8")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json-okio:1.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-protobuf:1.11.0")
    implementation("com.squareup.okhttp3:okhttp-brotli:5.5.0")
    implementation("com.squareup.okhttp3:okhttp-zstd:5.5.0")
    implementation("com.squareup.zstd:zstd-kmp-okio:0.4.0")
    implementation("com.github.null2264.injekt:injekt-core:4135455a2a")
    // Built by tools/vendor.sh from extensions-source. Not in git.
    implementation(files("vendor/keiyoushi-core.jar", "vendor/androidx-preference-stubs.jar"))
}

dependencies {
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit5")
    testImplementation("org.junit.jupiter:junit-jupiter:5.11.4")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
    // HOST_IT is read from the environment; without this input Gradle reuses a cached skip.
    inputs.property("HOST_IT", System.getenv("HOST_IT") ?: "")
}

// Copies every runtime dependency to build/lib, for the container image.
tasks.register<Copy>("installLib") {
    from(configurations.runtimeClasspath)
    into(layout.buildDirectory.dir("lib"))
}

tasks.register("printRuntimeCp") {
    doLast { println(sourceSets["main"].runtimeClasspath.files.joinToString(":") { it.absolutePath }) }
}
