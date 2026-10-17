package eu.kanade.tachiyomi.host

import kotlinx.serialization.json.Json
import kotlinx.serialization.protobuf.ProtoBuf

// Instances the Mihon app normally registers in its DI graph. keiyoushi core fetches these via Injekt.
object HostRegistry {
    val json: Json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
        isLenient = true
        coerceInputValues = true
        encodeDefaults = true
    }
    val proto: ProtoBuf = ProtoBuf
}
