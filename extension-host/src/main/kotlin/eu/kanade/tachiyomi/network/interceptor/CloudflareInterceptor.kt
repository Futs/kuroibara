package eu.kanade.tachiyomi.network.interceptor

import android.webkit.CookieManager
import eu.kanade.tachiyomi.host.HostRegistry
import java.io.IOException
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response

/**
 * On a Cloudflare challenge, asks FlareSolverr for clearance cookies and user agent for the host,
 * then retries the original request with them. Disabled when [solverUrl] is null.
 * GET only: POST challenges are not solved yet.
 */
class CloudflareInterceptor(
    private val solverUrl: String? = System.getenv("FLARESOLVERR_URL")?.takeIf { it.isNotBlank() },
) : Interceptor {

    // The solver's user agent per host. Cookies live in the shared CookieManager, so extensions can read them too.
    private val userAgents = ConcurrentHashMap<String, String>()

    // No interceptors here: the solver call must not recurse into this interceptor.
    private val solverClient = OkHttpClient.Builder()
        .callTimeout(120, TimeUnit.SECONDS)
        .build()

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = withStoredClearance(chain.request())
        val host = request.url.host

        val response = chain.proceed(request)
        if (solverUrl == null || !isChallenge(response)) return response
        response.close()

        val userAgent = solve(solverUrl, request.url.toString())
            ?: throw IOException("Cloudflare challenge not solved for $host")
        userAgents[host] = userAgent
        return chain.proceed(withStoredClearance(request))
    }

    private fun isChallenge(response: Response): Boolean {
        if (response.header("cf-mitigated") == "challenge") return true
        return response.code in setOf(403, 503) && response.header("server")?.startsWith("cloudflare") == true
    }

    // Adds the stored cookies for this URL (if the request has none) and the solver's user agent for this host.
    private fun withStoredClearance(request: Request): Request {
        val builder = request.newBuilder()
        if (request.header("Cookie") == null) {
            CookieManager.getInstance().getCookie(request.url.toString())?.let { builder.header("Cookie", it) }
        }
        userAgents[request.url.host]?.let { builder.header("User-Agent", it) }
        return builder.build()
    }

    // Stores the solver's cookies in CookieManager for the page's URL. Returns the user agent, or null if unsolved.
    private fun solve(solverUrl: String, url: String): String? {
        val payload = """{"cmd":"request.get","url":${jsonString(url)},"maxTimeout":60000}"""
        val body = payload.toRequestBody("application/json".toMediaType())
        val req = Request.Builder().url("${solverUrl.trimEnd('/')}/v1").post(body).build()
        solverClient.newCall(req).execute().use { resp ->
            if (!resp.isSuccessful) return null
            val root = HostRegistry.json.parseToJsonElement(resp.body.string()).jsonObject
            if (root["status"]?.jsonPrimitive?.content != "ok") return null
            val solution = root["solution"]?.jsonObject ?: return null
            val userAgent = solution["userAgent"]?.jsonPrimitive?.content ?: return null
            // Solver may report "Challenge not detected" with no cookies. Keep its user agent anyway.
            solution["cookies"]?.jsonArray.orEmpty().forEach { c ->
                val o = c.jsonObject
                CookieManager.getInstance().setCookie(
                    url,
                    "${o["name"]!!.jsonPrimitive.content}=${o["value"]!!.jsonPrimitive.content}",
                )
            }
            return userAgent
        }
    }

    private fun jsonString(s: String): String = buildString {
        append('"')
        for (ch in s) when (ch) {
            '"' -> append("\\\"")
            '\\' -> append("\\\\")
            else -> append(ch)
        }
        append('"')
    }
}
