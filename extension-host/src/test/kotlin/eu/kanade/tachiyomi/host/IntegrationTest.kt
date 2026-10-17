package eu.kanade.tachiyomi.host

import eu.kanade.tachiyomi.host.api.Server
import java.io.File
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
import org.junit.jupiter.api.Assumptions.assumeTrue

// Runs real extensions against real sites. Skipped unless HOST_IT=1 and a built index exists.
// HOST_DATA_DIR points at the build output (default: ./data). The test works on a copy,
// so state.json and the real install list are never touched.
//
// Sources that fail from this network are expected to report an error class, not a crash.
// Results are checked for shape, not for an "ok" that depends on the site being reachable (D6).
class IntegrationTest {
    private lateinit var work: File
    private lateinit var server: Server
    private lateinit var base: String
    private val token = "it-token"
    private val client = HttpClient.newHttpClient()

    @BeforeTest
    fun setUp() {
        assumeTrue(System.getenv("HOST_IT") == "1", "set HOST_IT=1 to run integration tests")
        val source = File(System.getenv("HOST_DATA_DIR") ?: "data")
        assumeTrue(File(source, "upstream/index.json").exists(), "no upstream catalog at ${source.path}; run tools/fetch-upstream.py")
        work = Files.createTempDirectory("host-it").toFile()
        File(source, "jars").copyRecursively(File(work, "jars"))
        File(source, "upstream").takeIf { it.exists() }?.copyRecursively(File(work, "upstream"))
        server = Server(Config(port = 0, token = token, dataDir = work))
        server.start()
        base = "http://127.0.0.1:${server.port}"
    }

    @AfterTest
    fun tearDown() {
        if (this::server.isInitialized) server.stop()
        if (this::work.isInitialized) work.deleteRecursively()
    }

    private fun post(path: String, body: String? = null): String {
        val req = HttpRequest.newBuilder(URI.create(base + path))
            .header("Authorization", "Bearer $token")
            .POST(body?.let { HttpRequest.BodyPublishers.ofString(it) } ?: HttpRequest.BodyPublishers.noBody()).build()
        val r = client.send(req, HttpResponse.BodyHandlers.ofString())
        assertEquals(200, r.statusCode(), r.body())
        return r.body()
    }

    private fun testOf(module: String): String {
        post("/extensions/$module/install")
        return post("/extensions/$module/test?q=one")
    }

    @Test
    fun mangaKatana_fullFlow() {
        val body = testOf("en/mangakatana")
        assertTrue(body.contains("\"ok\":true"), body)
        assertTrue(body.contains("\"pages\":\"ok"), body)
    }

    @Test
    fun toonily_madaraTheme_fullFlow() {
        val body = testOf("en/toonily")
        assertTrue(body.contains("\"ok\":true"), body)
        assertTrue(body.contains("\"pages\":\"ok"), body)
    }

    @Test
    fun mangaFire_multiSource_fullFlow() {
        val body = testOf("all/mangafire")
        assertTrue(body.contains("\"ok\":true"), body)
    }

    @Test
    fun allManga_reportsWebViewNeeded() {
        // Search and details work; pages need a WebView. Expected until Phase 4.
        val body = testOf("en/allanime")
        assertTrue(body.contains("\"ok\":false"), body)
        assertTrue(body.contains("\"error_class\":\"webview-needed\""), body)
    }

    @Test
    fun mangaKatana_pageImage_isAJpegAndResumeOffsetIsReported() {
        post("/extensions/en/mangakatana/install")
        val details = post("/extensions/en/mangakatana/details", """{"url": "/manga/one-piece.49"}""")
        val chapterUrl = Regex("\"chapters\":\\[\\{\"url\":\"([^\"]+)\"").find(details)!!.groupValues[1]
        val pages = post("/extensions/en/mangakatana/pages", """{"url": "$chapterUrl"}""")
        val imageUrl = Regex("\"image_url\":\"([^\"]+)\"").find(pages)!!.groupValues[1]
        val req = HttpRequest.newBuilder(URI.create(base + "/extensions/en/mangakatana/image"))
            .header("Authorization", "Bearer $token")
            .POST(HttpRequest.BodyPublishers.ofString("""{"image_url": "$imageUrl", "index": 0, "offset": 0}"""))
            .build()
        val r = client.send(req, HttpResponse.BodyHandlers.ofByteArray())
        assertEquals(200, r.statusCode())
        val bytes = r.body()
        assertTrue(bytes.size > 1000, "image too small: ${bytes.size}")
        assertEquals(0xFF.toByte(), bytes[0])
        assertEquals(0xD8.toByte(), bytes[1])
    }

    @Test
    fun blockedOrUnreachableSource_isRecordedNotHidden() {
        // Whatever this network does to a source, the install stays and the health is recorded.
        post("/extensions/en/mangakakalot/install")
        val body = post("/extensions/en/mangakakalot/test?q=one")
        assertTrue(body.contains("\"health\""), body)
        assertTrue(body.contains("\"enabled\":true"), body)
    }
}
