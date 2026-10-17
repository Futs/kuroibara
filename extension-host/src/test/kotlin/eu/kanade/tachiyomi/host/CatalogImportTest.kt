package eu.kanade.tachiyomi.host

import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpServer
import eu.kanade.tachiyomi.host.api.Server
import java.io.ByteArrayOutputStream
import java.io.File
import java.net.InetSocketAddress
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.file.Files
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

// Catalog settings and refresh (against a local HTTP catalog), and JAR import checks. Offline.
class CatalogImportTest {
    private lateinit var dir: File
    private lateinit var catalog: HttpServer
    private lateinit var server: Server
    private lateinit var base: String
    private var catalogBody = CATALOG
    private var catalogStatus = 200
    private val token = "c-token"
    private val client = HttpClient.newHttpClient()

    @BeforeTest
    fun setUp() {
        dir = Files.createTempDirectory("host-catalog").toFile()
        catalog = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        catalog.createContext("/index.json") { ex ->
            reply(ex, catalogStatus, catalogBody.toByteArray())
        }
        catalog.start()
        val catalogUrl = "http://127.0.0.1:${catalog.address.port}/index.json"
        startServer(Config(port = 0, token = token, dataDir = dir, defaultCatalogUrl = catalogUrl, allowHttpCatalog = true))
    }

    @AfterTest
    fun tearDown() {
        server.stop()
        catalog.stop(0)
        dir.deleteRecursively()
    }

    private fun startServer(config: Config) {
        server = Server(config)
        server.start()
        base = "http://127.0.0.1:${server.port}"
    }

    private fun reply(ex: HttpExchange, status: Int, body: ByteArray) {
        ex.sendResponseHeaders(status, body.size.toLong())
        ex.responseBody.use { it.write(body) }
    }

    private fun call(method: String, path: String, body: ByteArray? = null, type: String? = null): Pair<Int, String> {
        val b = HttpRequest.newBuilder(URI.create(base + path)).header("Authorization", "Bearer $token")
        type?.let { b.header("Content-Type", it) }
        b.method(method, body?.let { HttpRequest.BodyPublishers.ofByteArray(it) } ?: HttpRequest.BodyPublishers.noBody())
        val r = client.send(b.build(), HttpResponse.BodyHandlers.ofString())
        return r.statusCode() to r.body()
    }

    @Test
    fun settingsDefaultToTheBuiltInCatalogAndCanBeChanged() {
        val (_, first) = call("GET", "/catalog/settings")
        assertTrue(first.contains("\"is_default\":true"), first)
        val (status, put) = call("PUT", "/catalog/settings", """{"url": "https://example.test/index.json"}""".toByteArray(), "application/json")
        assertEquals(200, status, put)
        assertTrue(call("GET", "/catalog/settings").second.contains("example.test"))
        call("PUT", "/catalog/settings", """{"url": null}""".toByteArray(), "application/json")
        assertTrue(call("GET", "/catalog/settings").second.contains("\"is_default\":true"))
    }

    @Test
    fun plainHttpCatalogIsRefusedUnlessAllowed() {
        val (status, body) = call("PUT", "/catalog/settings", """{"url": "ftp://x/y"}""".toByteArray(), "application/json")
        assertEquals(422, status, body)
        assertTrue(body.contains("https"), body)
        val strict = Config(port = 0, token = token, dataDir = File(dir, "strict").apply { mkdirs() })
        server.stop()
        startServer(strict)
        assertEquals(422, call("PUT", "/catalog/settings", """{"url": "http://x/y"}""".toByteArray(), "application/json").first)
    }

    @Test
    fun refreshWritesTheIndexWithModuleKeysAndJarUrls() {
        val (status, body) = call("POST", "/catalog/refresh")
        assertEquals(200, status, body)
        assertTrue(body.contains("\"extensions\":2"), body)
        val index = File(dir, "upstream/index.json").readText()
        assertTrue(index.contains("\"module\":\"en/mangakatana\""), index)
        assertTrue(index.contains("\"jar_url\":\"https://example.test/mk.jar\""), index)
        assertTrue(index.contains("\"module\":null"), index)  // a package in another shape has no module key
    }

    @Test
    fun badCatalogsAreReportedAndLeaveTheIndexAlone() {
        catalogBody = "not json"
        assertEquals(502, call("POST", "/catalog/refresh").first)
        catalogBody = """{"name": "x"}"""
        assertEquals(502, call("POST", "/catalog/refresh").first)
        catalogStatus = 500
        catalogBody = CATALOG
        assertEquals(502, call("POST", "/catalog/refresh").first)
        assertFalse(File(dir, "upstream/index.json").exists())
    }

    @Test
    fun importRefusesWhatIsNotAnExtensionJar() {
        assertEquals(422, call("POST", "/extensions/en/x/import", "hello".toByteArray(), "application/octet-stream").first)
        assertEquals(422, call("POST", "/extensions/en/x/import", ByteArray(0), "application/octet-stream").first)
        val zipWithoutEntry = zipOf("readme.txt" to "nothing here")
        val (status, body) = call("POST", "/extensions/en/x/import", zipWithoutEntry, "application/octet-stream")
        assertEquals(422, status, body)
        assertTrue(body.contains("Generated.class"), body)
    }

    @Test
    fun importChecksTheModuleName() {
        val zip = zipOf("keiyoushi/source/Generated.class" to "x")
        val (status, body) = call("POST", "/extensions/../import", zip, "application/octet-stream")
        assertTrue(status == 422 || status == 404 || status == 400, "$status $body")
        val (s2, b2) = call("POST", "/extensions/Bad_Module/x/import", zip, "application/octet-stream")
        assertTrue(s2 == 422 || s2 == 404, "$s2 $b2")
    }

    companion object {
        private val CATALOG = """
            {"name": "Keiyoushi", "extensionList": {"extensions": [
              {"name": "MangaKatana", "packageName": "eu.kanade.tachiyomi.extension.en.mangakatana",
               "versionCode": 7, "versionName": "1.0.7", "contentWarning": "CONTENT_WARNING_SAFE",
               "resources": {"jarUrl": "https://example.test/mk.jar", "apkUrl": "https://example.test/mk.apk"},
               "sources": [{"id": 1, "name": "MangaKatana", "language": "en", "homeUrl": "https://mk.test"}]},
              {"name": "Odd", "packageName": "com.example.odd", "versionCode": 1, "versionName": "1",
               "contentWarning": "", "resources": {}, "sources": []}
            ]}}
        """.trimIndent()

        private fun zipOf(vararg entries: Pair<String, String>): ByteArray {
            val out = ByteArrayOutputStream()
            ZipOutputStream(out).use { z ->
                for ((name, body) in entries) {
                    z.putNextEntry(ZipEntry(name))
                    z.write(body.toByteArray())
                    z.closeEntry()
                }
            }
            return out.toByteArray()
        }
    }
}
