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
import kotlin.test.assertFalse
import kotlin.test.assertTrue

// Contract tests for the HTTP API. They use a fake index and empty JAR files, so no network is needed.
// The install path only checks that the JAR exists; the probe is covered by the integration test.
class ServerContractTest {
    private lateinit var dir: File
    private lateinit var server: Server
    private lateinit var base: String
    private val token = "test-token"
    private val client = HttpClient.newHttpClient()

    @BeforeTest
    fun setUp() {
        dir = Files.createTempDirectory("host-test").toFile()
        val jars = File(dir, "jars").apply { mkdirs() }
        File(jars, "en_fake@1-aaaa1111.jar").writeText("")
        File(jars, "en_fake@2-bbbb2222.jar").writeText("")
        File(jars, "index.json").writeText(INDEX)
        File(dir, "upstream").mkdirs()
        File(dir, "upstream/index.json").writeText(UPSTREAM)
        startServer()
    }

    @AfterTest
    fun tearDown() {
        server.stop()
        dir.deleteRecursively()
    }

    private fun startServer() {
        server = Server(Config(port = 0, token = token, dataDir = dir))
        server.start()
        base = "http://127.0.0.1:${server.port}"
    }

    private fun call(method: String, path: String, auth: Boolean = true): Pair<Int, String> {
        val b = HttpRequest.newBuilder(URI.create(base + path))
            .method(method, HttpRequest.BodyPublishers.noBody())
        if (auth) b.header("Authorization", "Bearer $token")
        val r = client.send(b.build(), HttpResponse.BodyHandlers.ofString())
        return r.statusCode() to r.body()
    }

    @Test
    fun healthNeedsNoToken() {
        assertEquals(200, call("GET", "/health", auth = false).first)
    }

    @Test
    fun everyOtherRouteNeedsTheToken() {
        assertEquals(401, call("GET", "/catalog", auth = false).first)
        val wrong = HttpRequest.newBuilder(URI.create("$base/catalog")).header("Authorization", "Bearer nope").build()
        assertEquals(401, client.send(wrong, HttpResponse.BodyHandlers.ofString()).statusCode())
    }

    @Test
    fun catalogListsVersionsAndSources() {
        val (status, body) = call("GET", "/catalog")
        assertEquals(200, status)
        assertTrue(body.contains("\"latest_version_code\":2"), body)
        assertTrue(body.contains("\"version_code\":1") && body.contains("\"version_code\":2"), body)
        assertTrue(body.contains("\"name\":\"Fake\""), body)
    }

    @Test
    fun installLatestThenEnableDisable() {
        assertEquals(200, call("POST", "/extensions/en/fake/install?source=local").first)
        val (_, list) = call("GET", "/extensions")
        assertTrue(list.contains("\"enabled\":true") && list.contains("\"version_code\":2"), list)
        assertEquals(200, call("POST", "/extensions/en/fake/disable").first)
        assertTrue(call("GET", "/extensions").second.contains("\"enabled\":false"))
        assertEquals(200, call("POST", "/extensions/en/fake/enable").first)
        assertTrue(call("GET", "/extensions").second.contains("\"enabled\":true"))
    }

    @Test
    fun installPinnedOlderVersion() {
        assertEquals(200, call("POST", "/extensions/en/fake/install?source=local&version_code=1&hash=aaaa").first)
        val list = call("GET", "/extensions").second
        assertTrue(list.contains("\"version_code\":1"), list)
        assertTrue(list.contains("\"update_available\":true"), list)
    }

    @Test
    fun unknownModuleAndVersionAre404() {
        assertEquals(404, call("POST", "/extensions/en/nope/install?source=local").first)
        assertEquals(404, call("POST", "/extensions/en/fake/install?source=local&version_code=99").first)
    }

    @Test
    fun missingJarIsAnError() {
        File(dir, "jars/en_fake@2-bbbb2222.jar").delete()
        assertEquals(500, call("POST", "/extensions/en/fake/install?source=local").first)
    }

    @Test
    fun installStatePersistsAcrossRestart() {
        call("POST", "/extensions/en/fake/install?source=local")
        call("POST", "/extensions/en/fake/disable")
        server.stop()
        startServer()
        assertTrue(call("GET", "/extensions").second.contains("\"enabled\":false"))
    }

    @Test
    fun uninstallRemovesTheInstall() {
        call("POST", "/extensions/en/fake/install?source=local")
        assertEquals(200, call("DELETE", "/extensions/en/fake").first)
        assertEquals(404, call("DELETE", "/extensions/en/fake").first)
        assertFalse(call("GET", "/extensions").second.contains("en/fake"))
    }

    @Test
    fun actionsOnUninstalledModuleAre404() {
        assertEquals(404, call("POST", "/extensions/en/fake/enable").first)
        assertEquals(404, call("POST", "/extensions/en/fake/test").first)
        assertEquals(404, call("GET", "/extensions/en/fake/health").first)
    }

    @Test
    fun upstreamListsExtensionsWithLocalAndInstalledFlags() {
        assertEquals(200, call("POST", "/extensions/en/fake/install?source=local").first)
        val (status, body) = call("GET", "/upstream")
        assertEquals(200, status)
        assertTrue(body.contains("\"package\":\"eu.kanade.tachiyomi.extension.en.fake\""), body)
        assertTrue(body.contains("\"module\":\"en/fake\",\"name\":\"Fake\",\"version_code\":5"), body)
        assertTrue(body.contains("\"in_local_build\":true"), body)
        assertTrue(body.contains("\"installed\":true"), body)
        assertTrue(body.contains("\"in_local_build\":false"), body)
    }

    @Test
    fun browseRoutesValidateInputAndInstallState() {
        assertEquals(404, call("POST", "/extensions/en/fake/search?q=x").first)
        assertEquals(400, call("POST", "/extensions/en/fake/search").first)
        assertEquals(400, call("POST", "/extensions/en/fake/details").first) // body is checked before install state
        call("POST", "/extensions/en/fake/install?source=local")
        assertEquals(400, call("POST", "/extensions/en/fake/details").first)
        assertEquals(400, call("POST", "/extensions/en/fake/pages").first)
    }

    @Test
    fun imageRouteValidatesInput() {
        assertEquals(404, call("POST", "/extensions/en/fake/image").first)
        call("POST", "/extensions/en/fake/install?source=local")
        assertEquals(400, call("POST", "/extensions/en/fake/image").first)
    }

    @Test
    fun upstreamMissingIsA404() {
        File(dir, "upstream/index.json").delete()
        assertEquals(404, call("GET", "/upstream").first)
    }

    companion object {
        private val UPSTREAM = """
            {"name": "Keiyoushi", "fetched_at": "2026-01-01T00:00:00+00:00", "signing_key_fingerprint": "abc",
             "extensions": [
              {"package": "eu.kanade.tachiyomi.extension.en.fake", "module": "en/fake", "name": "Fake",
               "version_code": 5, "version_name": "1.5", "content_warning": "CONTENT_WARNING_SAFE",
               "jar_url": "https://example.test/fake.jar", "apk_url": null,
               "sources": [{"id": 1, "name": "Fake", "language": "en", "home_url": "https://example.test"}]},
              {"package": "eu.kanade.tachiyomi.extension.en.other", "module": "en/other", "name": "Other",
               "version_code": 2, "version_name": "1.2", "content_warning": "CONTENT_WARNING_NSFW",
               "jar_url": null, "apk_url": "https://example.test/other.apk",
               "sources": [{"id": 2, "name": "Other", "language": "en", "home_url": "https://example.test/o"}]}
             ]}
        """.trimIndent()

        private val INDEX = """
            {"modules": {"en/fake": {"theme": null, "versions": [
              {"version_code": 1, "hash": "aaaa1111", "jar": "en_fake@1-aaaa1111.jar", "package": "eu.kanade.tachiyomi.extension.en.fake",
               "sources": [{"name": "Fake", "lang": "en", "id": 1, "baseUrl": "https://example.test"}],
               "built_at": "2026-01-01T00:00:00+00:00", "built_from": "abc"},
              {"version_code": 2, "hash": "bbbb2222", "jar": "en_fake@2-bbbb2222.jar", "package": "eu.kanade.tachiyomi.extension.en.fake",
               "sources": [{"name": "Fake", "lang": "en", "id": 1, "baseUrl": "https://example.test"}],
               "built_at": "2026-02-01T00:00:00+00:00", "built_from": "def"}
            ]}}}
        """.trimIndent()
    }
}
