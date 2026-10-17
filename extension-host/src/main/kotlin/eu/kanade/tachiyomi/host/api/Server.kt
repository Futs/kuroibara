package eu.kanade.tachiyomi.host.api

import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpServer
import eu.kanade.tachiyomi.host.Config
import eu.kanade.tachiyomi.host.Browse
import eu.kanade.tachiyomi.host.ImportInstaller
import eu.kanade.tachiyomi.host.Probe
import eu.kanade.tachiyomi.host.catalog.Catalog
import eu.kanade.tachiyomi.host.catalog.CatalogSource
import eu.kanade.tachiyomi.host.catalog.ModuleEntry
import eu.kanade.tachiyomi.host.catalog.Upstream
import eu.kanade.tachiyomi.host.state.Health
import eu.kanade.tachiyomi.host.state.Installed
import eu.kanade.tachiyomi.host.state.InstallStore
import eu.kanade.tachiyomi.host.upstream.UpstreamInstaller
import java.io.File
import java.net.InetSocketAddress
import java.net.URLDecoder
import java.nio.charset.StandardCharsets
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.longOrNull
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonObject

// HTTP API for the extension host. Bound to the internal network; every route except /health needs the token.
class Server(private val config: Config) {
    private val catalog = Catalog(config.indexFile, config.jarsDir)
    private val upstream = Upstream(File(config.dataDir, "upstream/index.json"))
    private val installer = UpstreamInstaller(config.githubApi, config.jarsDir)
    private val catalogSource = CatalogSource(config)
    private val importer = ImportInstaller(config)
    private val store = InstallStore(config.stateFile)
    private val probe = Probe(config.jarsDir, store)
    private val browse = Browse(probe)
    private val server = HttpServer.create(InetSocketAddress("0.0.0.0", config.port), 0)

    val port: Int get() = server.address.port

    fun stop() {
        server.stop(0)
        (server.executor as? java.util.concurrent.ExecutorService)?.shutdownNow()
    }

    fun start() {
        server.createContext("/") { ex -> handle(ex) }
        server.executor = java.util.concurrent.Executors.newCachedThreadPool()
        server.start()
    }

    private fun handle(ex: HttpExchange) {
        try {
            val path = ex.requestURI.path.trimEnd('/')
            val method = ex.requestMethod
            if (path == "/health" && method == "GET") return send(ex, 200, buildJsonObject { put("ok", true) })
            if (!authorized(ex)) return send(ex, 401, err("unauthorized"))

            val parts = path.split('/').filter { it.isNotEmpty() }
            val query = parseQuery(ex.requestURI.rawQuery)
            when {
                parts == listOf("catalog", "settings") && method == "GET" -> catalogSettings(ex)
                parts == listOf("catalog", "settings") && method == "PUT" -> catalogSettingsPut(ex)
                parts == listOf("catalog", "refresh") && method == "POST" -> catalogRefresh(ex)
                parts == listOf("catalog") && method == "GET" -> send(ex, 200, catalogJson())
                parts == listOf("extensions") && method == "GET" -> send(ex, 200, installedJson())
                parts == listOf("upstream") && method == "GET" -> upstreamJson()?.let { send(ex, 200, it) }
                    ?: send(ex, 404, err("no upstream catalog; run tools/fetch-upstream.py"))
                parts.firstOrNull() == "extensions" && parts.size >= 2 -> {
                    // Module names contain a slash (en/mangakatana), so the action is the last segment.
                    val action = if (parts.size >= 3 && parts.last() in ACTIONS) parts.last() else null
                    val module = if (action != null) parts.subList(1, parts.size - 1).joinToString("/") else parts.subList(1, parts.size).joinToString("/")
                    route(ex, method, module, action, query)
                }
                else -> send(ex, 404, err("no route"))
            }
        } catch (t: Throwable) {
            send(ex, 500, err("${t.javaClass.simpleName}: ${t.message}"))
        } finally {
            ex.close()
        }
    }

    private fun route(ex: HttpExchange, method: String, module: String, action: String?, query: Map<String, String>) {
        when {
            action == null && method == "DELETE" -> uninstall(ex, module)
            action == "install" && method == "POST" -> install(ex, module, query)
            action == "enable" && method == "POST" -> setEnabled(ex, module, true)
            action == "disable" && method == "POST" -> setEnabled(ex, module, false)
            action == "test" && method == "POST" -> test(ex, module, query)
            action == "health" && method == "GET" -> healthOf(ex, module)
            action == "search" && method == "POST" -> {
                val q = query["q"] ?: return send(ex, 400, err("q is required"))
                val page = query["page"]?.toIntOrNull() ?: 1
                browseCall(ex, module) { browse.search(module, q, page) }
            }
            action == "details" && method == "POST" -> {
                val url = urlFrom(ex) ?: return send(ex, 400, err("body needs {\"url\": ...}"))
                browseCall(ex, module) { browse.details(module, url) }
            }
            action == "image" && method == "POST" -> imageCall(ex, module)
            action == "import" && method == "POST" -> importCall(ex, module)
            action == "pages" && method == "POST" -> {
                val url = urlFrom(ex) ?: return send(ex, 400, err("body needs {\"url\": ...}"))
                browseCall(ex, module) { buildJsonObject { put("pages", browse.pages(module, url)) } }
            }
            else -> send(ex, 405, err("method or route not allowed"))
        }
    }

    // Default source is upstream (the Keiyoushi release JAR, checked against GitHub's sha256).
    // source=local installs a JAR from our own build (tools/build-jars.py).
    private fun install(ex: HttpExchange, module: String, query: Map<String, String>) {
        val prev = store.get(module)
        val enabled = prev?.enabled ?: true
        when ((query["source"] ?: "upstream")) {
            "upstream" -> {
                val up = upstream.catalog()?.extensions?.firstOrNull { it.module == module }
                    ?: return send(ex, 404, err("not in upstream catalog: $module"))
                val fetched = try {
                    installer.fetch(up)
                } catch (e: UpstreamInstaller.VerificationError) {
                    return send(ex, 502, err(e.message ?: "verification failed"))
                } catch (e: java.io.IOException) {
                    return send(ex, 502, err(e.message ?: "download failed"))
                }
                store.put(Installed(
                    module = module,
                    versionCode = up.versionCode,
                    hash = fetched.sha256,
                    jar = fetched.relativePath,
                    enabled = enabled,
                    installedAt = InstallStore.now(),
                    health = null,
                    source = "upstream",
                    packageName = up.packageName,
                ))
            }
            "local" -> {
                val entry = catalog.module(module) ?: return send(ex, 404, err("not in local build: $module"))
                val vc = query["version_code"]?.toIntOrNull()
                val hash = query["hash"]
                val version = when {
                    query.containsKey("version_code") -> entry.version(vc, hash)
                    else -> entry.latest
                } ?: return send(ex, 404, err("no such version"))
                if (!catalog.jarFile(version).exists()) return send(ex, 500, err("jar missing: ${version.jar}"))
                store.put(Installed(
                    module = module,
                    versionCode = version.versionCode,
                    hash = version.hash,
                    jar = version.jar,
                    enabled = enabled,
                    installedAt = InstallStore.now(),
                    health = null,
                    source = "local",
                    packageName = version.packageName,
                ))
            }
            else -> return send(ex, 400, err("source must be upstream or local"))
        }
        prev?.jar?.takeIf { it != store.get(module)?.jar }?.let { probe.forget(it) }
        send(ex, 200, installedOne(store.get(module)!!, catalog.module(module)))
    }

    private fun uninstall(ex: HttpExchange, module: String) {
        val old = store.remove(module) ?: return send(ex, 404, err("not installed: $module"))
        probe.forget(old.jar)
        send(ex, 200, buildJsonObject { put("removed", module) })
    }

    private fun setEnabled(ex: HttpExchange, module: String, enabled: Boolean) {
        val next = store.update(module) { it.copy(enabled = enabled) } ?: return send(ex, 404, err("not installed: $module"))
        send(ex, 200, installedOne(next, catalog.module(module)))
    }

    private fun test(ex: HttpExchange, module: String, query: Map<String, String>) {
        if (store.get(module) == null) return send(ex, 404, err("not installed: $module"))
        val health: Health = probe.test(module, query["q"] ?: "one")
        val next = store.update(module) { it.copy(health = health) }!!
        send(ex, 200, installedOne(next, catalog.module(module)))
    }

    private fun healthOf(ex: HttpExchange, module: String) {
        val item = store.get(module) ?: return send(ex, 404, err("not installed: $module"))
        send(ex, 200, buildJsonObject {
            put("module", module)
            item.health?.let { put("health", healthJson(it)) } ?: put("health", JsonPrimitive(null as String?))
        })
    }

    // Runs a browse call with a time limit. Extension failures come back as 502 with the same error class as the probe.
    private fun browseCall(ex: HttpExchange, module: String, block: suspend () -> JsonElement) {
        if (store.get(module) == null) return send(ex, 404, err("not installed: $module"))
        try {
            val body = runBlocking { withTimeout(120_000) { block() } }
            send(ex, 200, body)
        } catch (t: Throwable) {
            val root = generateSequence(t) { it.cause }.last()
            send(ex, 502, buildJsonObject {
                put("error", "${root.javaClass.name}: ${root.message}".take(300))
                put("error_class", Probe.classify(root))
            })
        }
    }

    private fun catalogSettings(ex: HttpExchange) {
        val s = catalogSource.settings()
        send(ex, 200, buildJsonObject { put("catalog_url", s.url); put("is_default", s.isDefault) })
    }

    private fun catalogSettingsPut(ex: HttpExchange) {
        val body = runCatching { Json.parseToJsonElement(ex.requestBody.readBytes().toString(StandardCharsets.UTF_8)).jsonObject }
            .getOrNull() ?: return send(ex, 400, err("body must be JSON"))
        // JSON null means "use the default"; a missing or blank string is treated the same way.
        val url = body["url"]?.takeUnless { it is kotlinx.serialization.json.JsonNull }?.jsonPrimitive?.content?.takeIf { it.isNotBlank() }
        try {
            url?.let { catalogSource.validate(it) }
            val s = catalogSource.setUrl(url)
            send(ex, 200, buildJsonObject { put("catalog_url", s.url); put("is_default", s.isDefault) })
        } catch (e: CatalogSource.CatalogError) {
            send(ex, 422, err(e.message ?: "invalid catalog URL"))
        }
    }

    private fun catalogRefresh(ex: HttpExchange) {
        try {
            val n = catalogSource.refresh()
            send(ex, 200, buildJsonObject { put("extensions", n); put("source", catalogSource.settings().url) })
        } catch (e: CatalogSource.CatalogError) {
            send(ex, 502, err(e.message ?: "catalog refresh failed"))
        }
    }

    // Body: the JAR bytes (application/octet-stream). The module is in the path: /extensions/{lang}/{name}/import.
    private fun importCall(ex: HttpExchange, module: String) {
        val bytes = ex.requestBody.readBytes()
        try {
            val imported = importer.import(module, bytes)
            val prev = store.get(module)
            store.put(Installed(
                module = module,
                versionCode = 0,
                hash = imported.sha256,
                jar = imported.relativePath,
                enabled = prev?.enabled ?: true,
                installedAt = InstallStore.now(),
                health = null,
                source = "import",
                packageName = imported.packageName,
            ))
            prev?.jar?.takeIf { it != imported.relativePath }?.let { probe.forget(it) }
            send(ex, 200, buildJsonObject {
                put("module", module)
                put("source", "import")
                put("package", imported.packageName)
                put("sources", buildJsonArray { imported.sourceNames.forEach { add(JsonPrimitive(it)) } })
            })
        } catch (e: ImportInstaller.ImportError) {
            send(ex, 422, err(e.message ?: "import failed"))
        }
    }

    // Body: {"url": page url, "image_url": optional, "index": n, "offset": bytes already on disk}.
    // Replies with the raw image bytes; X-Upstream-Status is the extension's status (200 or 206).
    private fun imageCall(ex: HttpExchange, module: String) {
        if (store.get(module) == null) return send(ex, 404, err("not installed: $module"))
        val body = runCatching { Json.parseToJsonElement(ex.requestBody.readBytes().toString(StandardCharsets.UTF_8)).jsonObject }
            .getOrNull() ?: return send(ex, 400, err("body must be JSON"))
        // Some extensions give only image_url (page url is empty); either is enough.
        val url = body["url"]?.jsonPrimitive?.content.orEmpty()
        val imageUrl = body["image_url"]?.jsonPrimitive?.content?.takeIf { it.isNotBlank() }
        if (url.isBlank() && imageUrl == null) return send(ex, 400, err("body needs url or image_url"))
        val index = body["index"]?.jsonPrimitive?.intOrNull ?: 0
        val offset = body["offset"]?.jsonPrimitive?.longOrNull ?: 0L
        try {
            val img = runBlocking { withTimeout(120_000) { browse.image(module, url, imageUrl, index, offset) } }
            ex.responseHeaders.add("Content-Type", img.contentType ?: "application/octet-stream")
            ex.responseHeaders.add("X-Upstream-Status", img.status.toString())
            ex.sendResponseHeaders(200, img.bytes.size.toLong())
            ex.responseBody.use { it.write(img.bytes) }
        } catch (t: Throwable) {
            val root = generateSequence(t) { it.cause }.last()
            send(ex, 502, buildJsonObject {
                put("error", "${root.javaClass.name}: ${root.message}".take(300))
                put("error_class", Probe.classify(root))
            })
        }
    }

    private fun urlFrom(ex: HttpExchange): String? {
        val body = ex.requestBody.readBytes().toString(StandardCharsets.UTF_8)
        if (body.isBlank()) return null
        return runCatching { Json.parseToJsonElement(body).jsonObject["url"]?.jsonPrimitive?.content }
            .getOrNull()?.takeIf { it.isNotBlank() }
    }

    private fun catalogJson(): JsonObject = buildJsonObject {
        putJsonObject("modules") {
            catalog.modules().values.sortedBy { it.module }.forEach { m -> put(m.module, moduleJson(m)) }
        }
    }

    private fun upstreamJson(): JsonObject? {
        val up = upstream.catalog() ?: return null
        val installed = store.all().map { it.module }.toSet()
        // Match by package name: a source dir can build a package with a different name (e.g. hivescans -> en.infernalvoidscans).
        val localByPackage = catalog.modules().values.mapNotNull { m -> m.latest?.packageName?.let { it to m.module } }.toMap()
        return buildJsonObject {
            put("name", up.name)
            put("fetched_at", up.fetchedAt)
            up.signingKeyFingerprint?.let { put("signing_key_fingerprint", it) }
            put("extensions", buildJsonArray {
                up.extensions.forEach { e ->
                    add(buildJsonObject {
                        put("package", e.packageName)
                        e.module?.let { put("module", it) }
                        put("name", e.name)
                        put("version_code", e.versionCode)
                        put("version_name", e.versionName)
                        put("content_warning", e.contentWarning)
                        e.jarUrl?.let { put("jar_url", it) }
                        put("sources", buildJsonArray { e.sourceNames.forEach { add(JsonPrimitive(it)) } })
                        val local = localByPackage[e.packageName]
                        put("installable", e.jarUrl != null)
                        put("in_local_build", local != null)
                        local?.let { put("local_module", it) }
                        put("installed", local != null && local in installed)
                    })
                }
            })
        }
    }

    private fun installedJson(): JsonObject = buildJsonObject {
        putJsonObject("extensions") {
            store.all().forEach { i -> put(i.module, installedOne(i, catalog.module(i.module))) }
        }
    }

    private fun installedOne(i: Installed, m: ModuleEntry?): JsonObject = buildJsonObject {
        put("module", i.module)
        i.versionCode?.let { put("version_code", it) }
        put("hash", i.hash)
        put("enabled", i.enabled)
        put("source", i.source)
        i.packageName?.let { put("package", it) }
        put("installed_at", i.installedAt)
        i.health?.let { put("health", healthJson(it)) }
        if (i.source == "upstream") {
            upstream.catalog()?.extensions?.firstOrNull { it.module == i.module }?.let { up ->
                put("latest_version_code", up.versionCode)
                put("update_available", up.versionCode > (i.versionCode ?: 0))
            }
        } else {
            m?.latest?.let { latest ->
                put("latest_version_code", latest.versionCode ?: 0)
                put("update_available", latest.hash != i.hash)
            }
        }
    }

    private fun moduleJson(m: ModuleEntry): JsonObject = buildJsonObject {
        put("module", m.module)
        m.latest?.packageName?.let { put("package", it) }
        m.theme?.let { put("theme", it) }
        m.latest?.let { put("latest_version_code", it.versionCode ?: 0) }
        put("versions", buildJsonArray {
            m.versions.forEach { v ->
                add(buildJsonObject {
                    put("version_code", v.versionCode ?: 0)
                    put("hash", v.hash)
                    put("built_at", v.builtAt)
                    put("built_from", v.builtFrom)
                })
            }
        })
        put("sources", buildJsonArray {
            m.latest?.sources?.forEach { s ->
                add(buildJsonObject {
                    put("name", s.name); put("lang", s.lang); put("id", s.id); put("baseUrl", s.baseUrl)
                })
            }
        })
    }

    private fun healthJson(h: Health): JsonObject = buildJsonObject {
        put("checked_at", h.checkedAt)
        put("ok", h.ok)
        h.errorClass?.let { put("error_class", it) }
        h.message?.let { put("message", it) }
        putJsonObject("steps") { h.steps.forEach { (k, v) -> put(k, v) } }
    }

    private fun authorized(ex: HttpExchange): Boolean =
        ex.requestHeaders.getFirst("Authorization") == "Bearer ${config.token}"

    private fun err(msg: String): JsonObject = buildJsonObject { put("error", msg) }

    private fun send(ex: HttpExchange, status: Int, body: JsonElement) {
        val bytes = body.toString().toByteArray(StandardCharsets.UTF_8)
        ex.responseHeaders.add("Content-Type", "application/json")
        ex.sendResponseHeaders(status, bytes.size.toLong())
        ex.responseBody.use { it.write(bytes) }
    }

    private fun parseQuery(raw: String?): Map<String, String> {
        if (raw.isNullOrEmpty()) return emptyMap()
        return raw.split('&').mapNotNull { kv ->
            val i = kv.indexOf('=')
            if (i <= 0) null else URLDecoder.decode(kv.substring(0, i), StandardCharsets.UTF_8) to
                URLDecoder.decode(kv.substring(i + 1), StandardCharsets.UTF_8)
        }.toMap()
    }

    companion object {
        private val ACTIONS = setOf("install", "enable", "disable", "test", "health", "search", "details", "pages", "image", "import")
    }
}
