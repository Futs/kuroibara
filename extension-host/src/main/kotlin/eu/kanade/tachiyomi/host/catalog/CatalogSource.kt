package eu.kanade.tachiyomi.host.catalog

import eu.kanade.tachiyomi.host.Config
import java.io.File
import java.io.IOException
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull

// The catalog the user chose (default: Keiyoushi), and the refresh that turns its index into data/upstream/index.json.
// Only https is accepted, unless HOST_ALLOW_HTTP_CATALOG=1 (tests). The download is size-limited and must be valid JSON
// with an extension list. Nothing is installed by a refresh.
class CatalogSource(private val config: Config) {
    class CatalogError(message: String) : IOException(message)

    data class Settings(val url: String, val isDefault: Boolean)

    private val client = HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NORMAL).build()

    fun settings(): Settings {
        val saved = if (config.settingsFile.exists()) {
            Json.parseToJsonElement(config.settingsFile.readText()).jsonObject["catalog_url"]?.jsonPrimitive?.content
        } else null
        return if (saved.isNullOrBlank()) Settings(config.defaultCatalogUrl, true) else Settings(saved, false)
    }

    fun setUrl(url: String?): Settings {
        if (url == null) {
            config.settingsFile.delete()
            return settings()
        }
        validate(url)
        config.settingsFile.parentFile?.mkdirs()
        val tmp = File(config.settingsFile.parentFile, config.settingsFile.name + ".tmp")
        tmp.writeText("""{"catalog_url": ${kotlinx.serialization.json.JsonPrimitive(url)}}""")
        Files.move(tmp.toPath(), config.settingsFile.toPath(), StandardCopyOption.REPLACE_EXISTING)
        return settings()
    }

    fun validate(url: String) {
        val uri = try {
            URI.create(url)
        } catch (e: IllegalArgumentException) {
            throw CatalogError("not a valid URL")
        }
        val scheme = uri.scheme?.lowercase()
        val ok = scheme == "https" || (scheme == "http" && config.allowHttpCatalog)
        if (!ok || uri.host.isNullOrBlank()) throw CatalogError("catalog URL must be https://host/...")
    }

    // Fetches the catalog, validates it, and writes data/upstream/index.json (atomically). Returns the number of extensions.
    fun refresh(): Int {
        val url = settings().url
        validate(url)
        val body = download(url)
        val root = try {
            Json.parseToJsonElement(body).jsonObject
        } catch (e: Exception) {
            throw CatalogError("catalog is not valid JSON")
        }
        val list = (root["extensionList"] as? JsonObject)?.get("extensions") as? JsonArray
            ?: throw CatalogError("catalog has no extension list")
        val extensions = list.map { el -> extensionEntry(el.jsonObject) }
        val out = JsonObject(
            mapOf(
                "name" to kotlinx.serialization.json.JsonPrimitive(root["name"]?.jsonPrimitive?.content ?: ""),
                "fetched_at" to kotlinx.serialization.json.JsonPrimitive(java.time.Instant.now().toString()),
                "index_url" to kotlinx.serialization.json.JsonPrimitive(url),
                "extensions" to JsonArray(extensions),
            ),
        )
        val target = File(config.dataDir, "upstream/index.json")
        target.parentFile.mkdirs()
        val tmp = File(target.parentFile, target.name + ".tmp")
        tmp.writeText(out.toString())
        Files.move(tmp.toPath(), target.toPath(), StandardCopyOption.REPLACE_EXISTING)
        return extensions.size
    }

    private fun download(url: String): String {
        val req = HttpRequest.newBuilder(URI.create(url)).timeout(java.time.Duration.ofSeconds(60)).GET().build()
        val resp = try {
            client.send(req, HttpResponse.BodyHandlers.ofInputStream())
        } catch (e: IOException) {
            throw CatalogError("could not reach the catalog: ${e.message}")
        }
        resp.body().use { input ->
            if (resp.statusCode() !in 200..299) throw CatalogError("catalog answered HTTP ${resp.statusCode()}")
            val bytes = input.readNBytes(MAX_CATALOG_BYTES + 1)
            if (bytes.size > MAX_CATALOG_BYTES) throw CatalogError("catalog is larger than ${MAX_CATALOG_BYTES / 1_000_000} MB")
            return String(bytes, Charsets.UTF_8)
        }
    }

    private fun extensionEntry(o: JsonObject): JsonElementOut {
        val pkg = o["packageName"]?.jsonPrimitive?.content
            ?: throw CatalogError("an extension in the catalog has no packageName")
        val resources = o["resources"] as? JsonObject
        val sources = (o["sources"] as? JsonArray).orEmpty().map { it.jsonObject }
        return JsonObject(
            mapOf(
                "package" to kotlinx.serialization.json.JsonPrimitive(pkg),
                "module" to (moduleKey(pkg)?.let { kotlinx.serialization.json.JsonPrimitive(it) }
                    ?: kotlinx.serialization.json.JsonNull),
                "name" to kotlinx.serialization.json.JsonPrimitive(o["name"]?.jsonPrimitive?.content ?: pkg),
                "version_code" to kotlinx.serialization.json.JsonPrimitive(o["versionCode"]?.jsonPrimitive?.longOrNull?.toInt() ?: 0),
                "version_name" to kotlinx.serialization.json.JsonPrimitive(o["versionName"]?.jsonPrimitive?.content ?: ""),
                "content_warning" to kotlinx.serialization.json.JsonPrimitive(o["contentWarning"]?.jsonPrimitive?.content ?: ""),
                "jar_url" to (resources?.get("jarUrl")?.jsonPrimitive?.content?.let { kotlinx.serialization.json.JsonPrimitive(it) }
                    ?: kotlinx.serialization.json.JsonNull),
                "apk_url" to (resources?.get("apkUrl")?.jsonPrimitive?.content?.let { kotlinx.serialization.json.JsonPrimitive(it) }
                    ?: kotlinx.serialization.json.JsonNull),
                "sources" to JsonArray(sources.map { s ->
                    JsonObject(mapOf(
                        "id" to kotlinx.serialization.json.JsonPrimitive(s["id"]?.jsonPrimitive?.longOrNull ?: 0L),
                        "name" to kotlinx.serialization.json.JsonPrimitive(s["name"]?.jsonPrimitive?.content ?: ""),
                        "language" to kotlinx.serialization.json.JsonPrimitive(s["language"]?.jsonPrimitive?.content ?: ""),
                        "home_url" to kotlinx.serialization.json.JsonPrimitive(s["homeUrl"]?.jsonPrimitive?.content ?: ""),
                    ))
                }),
            ),
        )
    }

    companion object {
        const val MAX_CATALOG_BYTES = 30_000_000

        // eu.kanade.tachiyomi.extension.<lang>.<name> -> <lang>/<name>, the key our build uses. Null for other shapes.
        fun moduleKey(pkg: String): String? {
            val parts = pkg.split(".")
            return if (parts.size >= 6 && parts.take(4) == listOf("eu", "kanade", "tachiyomi", "extension")) "${parts[4]}/${parts[5]}" else null
        }
    }
}

typealias JsonElementOut = kotlinx.serialization.json.JsonElement
