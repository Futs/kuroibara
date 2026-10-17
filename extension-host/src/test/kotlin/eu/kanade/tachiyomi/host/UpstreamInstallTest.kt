package eu.kanade.tachiyomi.host

import com.sun.net.httpserver.HttpServer
import eu.kanade.tachiyomi.host.api.Server
import eu.kanade.tachiyomi.host.upstream.UpstreamInstaller
import java.io.File
import java.net.InetSocketAddress
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.file.Files
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

// Offline tests for upstream installs. A local HTTP server plays GitHub: the release lookup (with a
// digest) and the release asset. Covers a good digest, a wrong digest, and a missing digest.
class UpstreamInstallTest {
    private lateinit var dir: File
    private lateinit var fake: HttpServer
    private lateinit var server: Server
    private lateinit var base: String
    private val token = "u-token"
    private val client = HttpClient.newHttpClient()
    private val jarBytes = "pretend this is a jar".toByteArray()
    private val tag = "abc1234"
    private val asset = "tachiyomi-en.fake-v5.jar"
    private var digest: String? = null

    @BeforeTest
    fun setUp() {
        dir = Files.createTempDirectory("host-upstream").toFile()
        digest = UpstreamInstaller.sha256(File(dir, "x").apply { writeBytes(jarBytes) })
        fake = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        fake.createContext("/repos/keiyoushi/extensions/releases/tags/$tag") { ex ->
            val d = digest
            val assets = if (d == null) """[{"name": "$asset"}]""" else """[{"name": "$asset", "digest": "sha256:$d"}]"""
            respond(ex, 200, """{"assets": $assets}""".toByteArray())
        }
        fake.createContext("/releases/download/$tag/$asset") { ex -> respond(ex, 200, jarBytes) }
        fake.start()
        val fakeBase = "http://127.0.0.1:${fake.address.port}"
        File(dir, "upstream").mkdirs()
        File(dir, "upstream/index.json").writeText(
            """
            {"name": "Keiyoushi", "fetched_at": "x", "extensions": [
              {"package": "eu.kanade.tachiyomi.extension.en.fake", "module": "en/fake", "name": "Fake",
               "version_code": 5, "version_name": "1.5", "content_warning": "CONTENT_WARNING_SAFE",
               "jar_url": "$fakeBase/releases/download/$tag/$asset", "apk_url": null,
               "sources": [{"id": 1, "name": "Fake", "language": "en", "home_url": "https://example.test"}]}
            ]}
            """.trimIndent(),
        )
        server = Server(Config(port = 0, token = token, dataDir = dir, githubApi = fakeBase))
        server.start()
        base = "http://127.0.0.1:${server.port}"
    }

    @AfterTest
    fun tearDown() {
        server.stop()
        fake.stop(0)
        dir.deleteRecursively()
    }

    private fun respond(ex: com.sun.net.httpserver.HttpExchange, status: Int, body: ByteArray) {
        ex.sendResponseHeaders(status, body.size.toLong())
        ex.responseBody.use { it.write(body) }
    }

    private fun post(path: String): Pair<Int, String> {
        val req = HttpRequest.newBuilder(URI.create(base + path))
            .header("Authorization", "Bearer $token")
            .POST(HttpRequest.BodyPublishers.noBody()).build()
        val r = client.send(req, HttpResponse.BodyHandlers.ofString())
        return r.statusCode() to r.body()
    }

    @Test
    fun installFromUpstreamVerifiesDigestAndRecordsSource() {
        val (status, body) = post("/extensions/en/fake/install")
        assertEquals(200, status, body)
        assertTrue(body.contains("\"source\":\"upstream\""), body)
        assertTrue(body.contains("\"package\":\"eu.kanade.tachiyomi.extension.en.fake\""), body)
        val stored = File(dir, "jars/upstream").listFiles()!!.single()
        assertEquals(digest, UpstreamInstaller.sha256(stored))
    }

    @Test
    fun wrongDigestRefusesTheInstall() {
        digest = "0".repeat(64)
        val (status, body) = post("/extensions/en/fake/install")
        assertEquals(502, status, body)
        assertTrue(body.contains("sha256 mismatch"), body)
        assertEquals(0, File(dir, "jars/upstream").listFiles()?.size ?: 0)
        val req = HttpRequest.newBuilder(URI.create("$base/extensions")).header("Authorization", "Bearer $token").GET().build()
        assertTrue(client.send(req, HttpResponse.BodyHandlers.ofString()).body().contains("\"extensions\":{}"))
    }

    @Test
    fun missingDigestRefusesTheInstall() {
        digest = null
        val (status, body) = post("/extensions/en/fake/install")
        assertEquals(502, status, body)
        assertTrue(body.contains("no sha256 digest"), body)
    }

    @Test
    fun reinstallReusesTheVerifiedFile() {
        assertEquals(200, post("/extensions/en/fake/install").first)
        assertEquals(200, post("/extensions/en/fake/install").first)
        assertEquals(1, File(dir, "jars/upstream").listFiles()!!.size)
    }

    @Test
    fun localSourceStillInstallsFromOwnBuild() {
        assertEquals(404, post("/extensions/en/fake/install?source=local").first)
        assertEquals(400, post("/extensions/en/fake/install?source=nope").first)
    }
}
