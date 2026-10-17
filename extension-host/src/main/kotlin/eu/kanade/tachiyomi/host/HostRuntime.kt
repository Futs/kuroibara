package eu.kanade.tachiyomi.host

import android.app.Application
import eu.kanade.tachiyomi.network.NetworkHelper
import kotlinx.serialization.json.Json
import kotlinx.serialization.protobuf.ProtoBuf
import uy.kohesive.injekt.Injekt
import uy.kohesive.injekt.api.fullType

// Registers the app-level singletons that keiyoushi core and extensions fetch via Injekt.
// Call once per JVM, before any extension is loaded.
object HostRuntime {
    private var initialized = false

    @Synchronized
    fun init() {
        if (initialized) return
        Injekt.addSingleton(fullType<Application>(), Application())
        Injekt.addSingleton(fullType<NetworkHelper>(), NetworkHelper())
        Injekt.addSingleton(fullType<Json>(), HostRegistry.json)
        Injekt.addSingleton(fullType<ProtoBuf>(), HostRegistry.proto)
        initialized = true
    }
}
