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
    compileOnly(files("/home/futs/.gradle/caches/9.8.1/transforms/c1671c56efc5ebeea59d26e99f45c481/transformed/extensions-lib-42255ee5fa-runtime.jar"))
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-protobuf:1.11.0")
    implementation("com.squareup.okhttp3:okhttp-brotli:5.5.0")
    implementation("com.squareup.okhttp3:okhttp-zstd:5.5.0")
    implementation("com.squareup.zstd:zstd-kmp-okio:0.4.0")
    implementation("com.github.null2264.injekt:injekt-core:4135455a2a")
}

tasks.register("printRuntimeCp") {
    doLast { println(sourceSets["main"].runtimeClasspath.files.joinToString(":") { it.absolutePath }) }
}
