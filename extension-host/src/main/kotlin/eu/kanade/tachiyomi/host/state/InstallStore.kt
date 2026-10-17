package eu.kanade.tachiyomi.host.state

import java.io.File
import java.time.Instant
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonObject

data class Health(
    val checkedAt: String,
    val ok: Boolean,
    val errorClass: String?,
    val message: String?,
    val steps: Map<String, String>,
)

data class Installed(
    val module: String,
    val versionCode: Int?,
    val hash: String,
    val jar: String,
    val enabled: Boolean,
    val installedAt: String,
    val health: Health?,
    val source: String = "local",
    val packageName: String? = null,
)

// Which extensions are installed, which version, enabled or not, and the last health check.
// Written to state.json on each change. Access is serialized by this object.
class InstallStore(private val file: File) {
    private val items = LinkedHashMap<String, Installed>()

    init {
        if (file.exists()) {
            val root = Json.parseToJsonElement(file.readText()).jsonObject
            (root["extensions"] as? JsonObject)?.forEach { (module, el) -> items[module] = fromJson(module, el.jsonObject) }
        }
    }

    @Synchronized fun all(): List<Installed> = items.values.toList()

    @Synchronized fun get(module: String): Installed? = items[module]

    @Synchronized fun put(entry: Installed) {
        items[entry.module] = entry
        save()
    }

    @Synchronized fun remove(module: String): Installed? {
        val old = items.remove(module)
        save()
        return old
    }

    @Synchronized fun update(module: String, transform: (Installed) -> Installed): Installed? {
        val cur = items[module] ?: return null
        val next = transform(cur)
        items[module] = next
        save()
        return next
    }

    private fun save() {
        file.parentFile?.mkdirs()
        val obj = buildJsonObject {
            putJsonObject("extensions") {
                items.values.forEach { e -> put(e.module, toJson(e)) }
            }
        }
        val tmp = File(file.parentFile, file.name + ".tmp")
        tmp.writeText(obj.toString())
        tmp.renameTo(file)
    }

    private fun toJson(e: Installed): JsonObject = buildJsonObject {
        e.versionCode?.let { put("version_code", it) }
        put("hash", e.hash)
        put("jar", e.jar)
        put("enabled", e.enabled)
        put("source", e.source)
        e.packageName?.let { put("package", it) }
        put("installed_at", e.installedAt)
        e.health?.let { h ->
            putJsonObject("health") {
                put("checked_at", h.checkedAt)
                put("ok", h.ok)
                h.errorClass?.let { put("error_class", it) }
                h.message?.let { put("message", it) }
                putJsonObject("steps") { h.steps.forEach { (k, v) -> put(k, v) } }
            }
        }
    }

    private fun fromJson(module: String, o: JsonObject): Installed = Installed(
        module = module,
        versionCode = o["version_code"]?.jsonPrimitive?.intOrNull,
        hash = o["hash"]!!.jsonPrimitive.content,
        jar = o["jar"]!!.jsonPrimitive.content,
        enabled = o["enabled"]?.jsonPrimitive?.booleanOrNull ?: true,
        source = o["source"]?.jsonPrimitive?.content ?: "local",
        packageName = o["package"]?.jsonPrimitive?.content,
        installedAt = o["installed_at"]?.jsonPrimitive?.content.orEmpty(),
        health = (o["health"] as? JsonObject)?.let { h ->
            Health(
                checkedAt = h["checked_at"]?.jsonPrimitive?.content.orEmpty(),
                ok = h["ok"]?.jsonPrimitive?.booleanOrNull ?: false,
                errorClass = h["error_class"]?.jsonPrimitive?.content,
                message = h["message"]?.jsonPrimitive?.content,
                steps = (h["steps"] as? JsonObject)?.mapValues { (_, v) -> v.jsonPrimitive.content }.orEmpty(),
            )
        },
    )

    companion object {
        fun now(): String = Instant.now().toString()
    }
}
