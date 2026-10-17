package eu.kanade.tachiyomi.network

import eu.kanade.tachiyomi.network.interceptor.CloudflareInterceptor
import eu.kanade.tachiyomi.network.interceptor.UncaughtExceptionInterceptor
import eu.kanade.tachiyomi.network.interceptor.UserAgentInterceptor
import okhttp3.OkHttpClient

// Phase 0 host: plain client, no Cloudflare WebView interceptor.
class NetworkHelper {
    val client: OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(UncaughtExceptionInterceptor())
        .addInterceptor(UserAgentInterceptor(::defaultUserAgentProvider))
        .addInterceptor(CloudflareInterceptor())
        .build()
    val cloudflareClient: OkHttpClient get() = client
    val nonCloudflareClient: OkHttpClient get() = client

    fun defaultUserAgentProvider(): String =
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}
