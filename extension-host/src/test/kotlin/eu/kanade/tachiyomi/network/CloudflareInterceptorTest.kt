package eu.kanade.tachiyomi.network

import android.webkit.CookieManager
import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpServer
import eu.kanade.tachiyomi.network.interceptor.CloudflareInterceptor
import java.net.InetSocketAddress
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue
import okhttp3.OkHttpClient
import okhttp3.Request

// Offline test of the challenge path. The target answers 403 with a Cloudflare challenge until the request carries
// cf_clearance and the solver's user agent. The fake solver returns those, the way FlareSolverr does.
class CloudflareInterceptorTest {
    private lateinit var target: HttpServer
    private lateinit var solver: HttpServer
    private var solverCalls = 0

    @BeforeTest
    fun setUp() {
        CookieManager.getInstance().removeAllCookies(null)
        target = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        target.createContext("/page") { ex ->
            val cookie = ex.requestHeaders.getFirst("Cookie") ?: ""
            val ua = ex.requestHeaders.getFirst("User-Agent") ?: ""
            if (cookie.contains("cf_clearance=ok") && ua == SOLVED_UA) {
                reply(ex, 200, "content")
            } else {
                ex.responseHeaders.add("cf-mitigated", "challenge")
                ex.responseHeaders.add("Server", "cloudflare")
                reply(ex, 403, "challenge")
            }
        }
        target.start()
        solver = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        solver.createContext("/v1") { ex ->
            solverCalls++
            ex.requestBody.readBytes()
            reply(
                ex,
                200,
                """{"status":"ok","solution":{"userAgent":"$SOLVED_UA","cookies":[{"name":"cf_clearance","value":"ok"}]}}""",
            )
        }
        solver.start()
    }

    @AfterTest
    fun tearDown() {
        target.stop(0)
        solver.stop(0)
        CookieManager.getInstance().removeAllCookies(null)
    }

    private fun reply(ex: HttpExchange, status: Int, body: String) {
        val bytes = body.toByteArray()
        ex.sendResponseHeaders(status, bytes.size.toLong())
        ex.responseBody.use { it.write(bytes) }
    }

    private fun url() = "http://127.0.0.1:${target.address.port}/page"

    @Test
    fun solvesTheChallengeStoresTheCookieAndRetries() {
        val client = OkHttpClient.Builder()
            .addInterceptor(CloudflareInterceptor("http://127.0.0.1:${solver.address.port}"))
            .build()
        client.newCall(Request.Builder().url(url()).build()).execute().use { r ->
            assertEquals(200, r.code)
            assertEquals("content", r.body.string())
        }
        assertEquals(1, solverCalls)
        assertTrue(CookieManager.getInstance().getCookie(url())!!.contains("cf_clearance=ok"))
    }

    @Test
    fun laterRequestsUseTheStoredClearanceWithoutSolvingAgain() {
        val client = OkHttpClient.Builder()
            .addInterceptor(CloudflareInterceptor("http://127.0.0.1:${solver.address.port}"))
            .build()
        client.newCall(Request.Builder().url(url()).build()).execute().close()
        client.newCall(Request.Builder().url(url()).build()).execute().use { r ->
            assertEquals(200, r.code)
        }
        assertEquals(1, solverCalls)
    }

    @Test
    fun withoutASolverTheChallengeComesBackAsAnError() {
        val client = OkHttpClient.Builder().addInterceptor(CloudflareInterceptor(null)).build()
        client.newCall(Request.Builder().url(url()).build()).execute().use { r ->
            assertEquals(403, r.code)
        }
        assertEquals(0, solverCalls)
    }

    @Test
    fun cookieManagerMatchesHostAndParentDomains() {
        val cm = CookieManager.getInstance()
        cm.setCookie("https://example.test/a", "session=abc; Path=/; Secure")
        assertEquals("session=abc", cm.getCookie("https://example.test/b"))
        assertEquals("session=abc", cm.getCookie("https://www.example.test/"))
        assertNull(cm.getCookie("https://other.test/"))
        cm.removeAllCookies(null)
        assertNull(cm.getCookie("https://example.test/"))
    }

    companion object {
        private const val SOLVED_UA = "Solved/1.0"
    }
}
