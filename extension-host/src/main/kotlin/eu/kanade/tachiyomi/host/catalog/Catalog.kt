package eu.kanade.tachiyomi.host.catalog

import java.io.File
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import kotlinx.serialization.json.intOrNull

data class SourceInfo(val name: String, val lang: String, val id: Long, val baseUrl: String)

data class VersionRecord(
    val versionCode: Int?,
    val packageName: String?,
    val hash: String,
    val jar: String,
    val sources: List<SourceInfo>,
    val builtAt: String,
    val builtFrom: String,
)

data class ModuleEntry(
    val module: String,
    val theme: String?,
    val versions: List<VersionRecord>,
) {
    val latest: VersionRecord? get() = versions.lastOrNull()
    fun version(versionCode: Int?, hash: String? = null): VersionRecord? =
        versions.lastOrNull { it.versionCode == versionCode && (hash == null || it.hash.startsWith(hash)) }
}

// Reads the index written by tools/build-jars.py. Read-only; the file is replaced on each build.
class Catalog(private val indexFile: File, private val jarsDir: File) {
    @Volatile private var cached: Map<String, ModuleEntry> = emptyMap()
    @Volatile private var mtime: Long = -1

    fun modules(): Map<String, ModuleEntry> {
        if (!indexFile.exists()) return emptyMap()
        val t = indexFile.lastModified()
        if (t != mtime) {
            cached = parse(indexFile.readText())
            mtime = t
        }
        return cached
    }

    fun module(name: String): ModuleEntry? = modules()[name]

    fun jarFile(record: VersionRecord): File = File(jarsDir, record.jar)

    private fun parse(text: String): Map<String, ModuleEntry> {
        val root = Json.parseToJsonElement(text).jsonObject
        val mods = root["modules"]?.jsonObject ?: return emptyMap()
        return mods.mapValues { (name, el) ->
            val o = el.jsonObject
            ModuleEntry(
                module = name,
                theme = o["theme"]?.takeUnless { it.toString() == "null" }?.jsonPrimitive?.content,
                versions = (o["versions"] as? JsonArray).orEmpty().map { v ->
                    val vo = v.jsonObject
                    VersionRecord(
                        versionCode = vo["version_code"]?.takeUnless { it.toString() == "null" }?.jsonPrimitive?.intOrNull,
                        packageName = vo["package"]?.takeUnless { it.toString() == "null" }?.jsonPrimitive?.content,
                        hash = vo["hash"]!!.jsonPrimitive.content,
                        jar = vo["jar"]!!.jsonPrimitive.content,
                        sources = (vo["sources"] as? JsonArray).orEmpty().map { s ->
                            val so = s.jsonObject
                            SourceInfo(
                                name = so["name"]!!.jsonPrimitive.content,
                                lang = so["lang"]!!.jsonPrimitive.content,
                                id = so["id"]!!.jsonPrimitive.longOrNull ?: 0L,
                                baseUrl = so["baseUrl"]!!.jsonPrimitive.content,
                            )
                        },
                        builtAt = vo["built_at"]?.jsonPrimitive?.content.orEmpty(),
                        builtFrom = vo["built_from"]?.jsonPrimitive?.content.orEmpty(),
                    )
                },
            )
        }
    }
}
