package eu.kanade.tachiyomi.host.catalog

import java.io.File
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

data class UpstreamExtension(
    val packageName: String,
    val module: String?,
    val name: String,
    val versionCode: Int,
    val versionName: String,
    val contentWarning: String,
    val jarUrl: String?,
    val apkUrl: String?,
    val sourceNames: List<String>,
)

data class UpstreamCatalog(
    val name: String,
    val fetchedAt: String,
    val signingKeyFingerprint: String?,
    val extensions: List<UpstreamExtension>,
)

// Reads data/upstream/index.json written by tools/fetch-upstream.py. Display only: nothing here decides
// what gets installed. Installs come from the local build (see D2 / option b).
class Upstream(private val file: File) {
    @Volatile private var cached: UpstreamCatalog? = null
    @Volatile private var mtime: Long = -1

    fun catalog(): UpstreamCatalog? {
        if (!file.exists()) return null
        if (file.lastModified() != mtime) {
            cached = parse(file.readText())
            mtime = file.lastModified()
        }
        return cached
    }

    companion object {
        fun parse(text: String): UpstreamCatalog {
            val root = Json.parseToJsonElement(text).jsonObject
            return UpstreamCatalog(
                name = root["name"]?.jsonPrimitive?.content.orEmpty(),
                fetchedAt = root["fetched_at"]?.jsonPrimitive?.content.orEmpty(),
                signingKeyFingerprint = root["signing_key_fingerprint"]?.takeUnless { it.toString() == "null" }?.jsonPrimitive?.content,
                extensions = (root["extensions"] as? JsonArray).orEmpty().map { el ->
                    val o = el.jsonObject
                    UpstreamExtension(
                        packageName = o["package"]!!.jsonPrimitive.content,
                        module = o["module"]?.takeUnless { it.toString() == "null" }?.jsonPrimitive?.content,
                        name = o["name"]!!.jsonPrimitive.content,
                        versionCode = o["version_code"]?.jsonPrimitive?.intOrNull ?: 0,
                        versionName = o["version_name"]?.jsonPrimitive?.content.orEmpty(),
                        contentWarning = o["content_warning"]?.jsonPrimitive?.content.orEmpty(),
                        jarUrl = o["jar_url"]?.takeUnless { it.toString() == "null" }?.jsonPrimitive?.content,
                        apkUrl = o["apk_url"]?.takeUnless { it.toString() == "null" }?.jsonPrimitive?.content,
                        sourceNames = (o["sources"] as? JsonArray).orEmpty().map { it.jsonObject["name"]!!.jsonPrimitive.content },
                    )
                },
            )
        }
    }
}
