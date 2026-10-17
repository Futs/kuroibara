package eu.kanade.tachiyomi.host

import eu.kanade.tachiyomi.host.catalog.VersionRecord
import eu.kanade.tachiyomi.host.loader.ExtensionLoader
import eu.kanade.tachiyomi.host.loader.LoadedExtension
import eu.kanade.tachiyomi.network.HttpException
import eu.kanade.tachiyomi.source.Source
import java.io.File
import java.util.concurrent.ConcurrentHashMap
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import eu.kanade.tachiyomi.host.state.Health
import eu.kanade.tachiyomi.host.state.InstallStore

// Runs search, details, chapters and pages once against an installed extension and records the result.
// Loaded extensions are cached per JAR. Health is recorded per install, never used to hide a source (D6).
class Probe(private val jarsDir: File, private val store: InstallStore) {
    private val loaded = ConcurrentHashMap<String, LoadedExtension>()

    fun test(module: String, query: String): Health {
        val entry = store.get(module) ?: error("not installed: $module")
        val jar = File(jarsDir, entry.jar)
        val steps = LinkedHashMap<String, String>()
        var errorClass: String? = null
        var message: String? = null
        try {
            val ext = loaded.getOrPut(entry.jar) { ExtensionLoader.load(entry.jar, listOf(jar)) }
            val src = ext.sources.firstOrNull { it.lang == "en" } ?: ext.sources.first()
            runBlocking {
                withTimeout(120_000) {
                    val mangas = src.getSearchManga(1, query, src.getFilterList()).mangas
                    steps["search"] = "ok n=${mangas.size}"
                    val first = mangas.firstOrNull() ?: return@withTimeout
                    val update = src.getMangaUpdate(first, emptyList(), fetchDetails = true, fetchChapters = true)
                    steps["details"] = "ok"
                    steps["chapters"] = "ok n=${update.chapters.size}"
                    val last = update.chapters.lastOrNull() ?: return@withTimeout
                    steps["pages"] = "ok n=${src.getPageList(last).size}"
                }
            }
        } catch (t: Throwable) {
            val root = generateSequence(t) { it.cause }.last()
            errorClass = classify(root)
            message = "${root.javaClass.name}: ${root.message}".take(300)
            steps["error"] = errorClass
        }
        val ok = errorClass == null && steps["search"]?.startsWith("ok") == true
        return Health(
            checkedAt = InstallStore.now(),
            ok = ok,
            errorClass = errorClass,
            message = message,
            steps = steps,
        )
    }

    // Loaded source for an enabled install. English sources are preferred for multi-source extensions.
    fun source(module: String): Source {
        val entry = store.get(module) ?: error("not installed: $module")
        if (!entry.enabled) error("disabled: $module")
        val ext = loaded.getOrPut(entry.jar) { ExtensionLoader.load(entry.jar, listOf(File(jarsDir, entry.jar))) }
        return ext.sources.firstOrNull { it.lang == "en" } ?: ext.sources.first()
    }

    fun forget(jarName: String) {
        loaded.remove(jarName)
    }

    companion object {
        // Buckets from the Phase 0b run. Used for display only; nothing is excluded because of them.
        fun classify(t: Throwable): String = when {
            t is HttpException && t.code == 401 -> "auth-401"
            t is HttpException && (t.code == 403 || t.code == 503) -> "blocked"
            t is NoClassDefFoundError && t.message?.contains("android/webkit") == true -> "webview-needed"
            t is ClassNotFoundException && t.message?.contains("android.webkit") == true -> "webview-needed"
            t is NoClassDefFoundError || t is NoSuchMethodError || t is NoSuchFieldError || t is AbstractMethodError -> "shim-gap"
            t is ClassNotFoundException -> "shim-gap"
            t is java.net.SocketTimeoutException || t is kotlinx.coroutines.TimeoutCancellationException -> "timeout"
            t is java.io.IOException && t.message?.contains("timeout", ignoreCase = true) == true -> "timeout"
            t is java.io.IOException && t.message?.contains("Socket closed", ignoreCase = true) == true -> "timeout"
            else -> "error"
        }
    }
}
