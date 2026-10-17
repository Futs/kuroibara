package eu.kanade.tachiyomi.host

import eu.kanade.tachiyomi.source.model.Page
import eu.kanade.tachiyomi.source.online.HttpSource
import eu.kanade.tachiyomi.source.model.SChapter
import eu.kanade.tachiyomi.source.model.SManga
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

// Browse operations on an installed, enabled extension: search, details with chapters, and page list.
// Results are plain JSON for the Kuroibara backend. Callers handle timeouts and error classes.
class Browse(private val probe: Probe) {

    suspend fun search(module: String, query: String, page: Int): JsonObject {
        val src = probe.source(module)
        val result = src.getSearchManga(page, query, src.getFilterList())
        return buildJsonObject {
            put("source", src.name)
            put("lang", src.lang)
            put("has_next", result.hasNextPage)
            put("mangas", buildJsonArray { result.mangas.forEach { add(mangaJson(it)) } })
        }
    }

    suspend fun details(module: String, url: String): JsonObject {
        val src = probe.source(module)
        val manga = SManga.create().apply { this.url = url }
        val update = src.getMangaUpdate(manga, emptyList(), fetchDetails = true, fetchChapters = true)
        return buildJsonObject {
            put("manga", mangaJson(update.manga, fallbackUrl = url))
            put("chapters", buildJsonArray { update.chapters.forEach { add(chapterJson(it)) } })
        }
    }

    suspend fun pages(module: String, chapterUrl: String): JsonArray {
        val src = probe.source(module)
        val chapter = SChapter.create().apply { url = chapterUrl }
        val pages = src.getPageList(chapter)
        return buildJsonArray {
            pages.forEach { p ->
                add(buildJsonObject {
                    put("index", p.index)
                    put("url", p.url)
                    p.imageUrl?.let { put("image_url", it) }
                })
            }
        }
    }

    // One page image, as the extension fetches it (its headers, referer and rate limit apply).
    // offset > 0 asks for the rest of a partial download (HTTP Range); the status tells the caller if it was honoured.
    suspend fun image(module: String, pageUrl: String, imageUrl: String?, index: Int, offset: Long): ImageResult {
        val src = probe.source(module) as? HttpSource ?: error("source has no HTTP image support")
        val page = Page(index, pageUrl, imageUrl, null)
        if (page.imageUrl.isNullOrEmpty()) page.imageUrl = src.getImageUrl(page)
        return src.getImage(page, offset).use { resp ->
            ImageResult(
                status = resp.code,
                contentType = resp.header("Content-Type"),
                bytes = resp.body.bytes(),
            )
        }
    }

    data class ImageResult(val status: Int, val contentType: String?, val bytes: ByteArray)

    // Some extensions return an SManga whose lateinit fields were never set. Read them safely.
    private fun mangaJson(m: SManga, fallbackUrl: String? = null): JsonObject = buildJsonObject {
        put("url", runCatching { m.url }.getOrNull() ?: fallbackUrl ?: "")
        put("title", runCatching { m.title }.getOrNull() ?: "")
        m.thumbnail_url?.let { put("thumbnail_url", it) }
        m.author?.let { put("author", it) }
        m.artist?.let { put("artist", it) }
        m.description?.let { put("description", it) }
        m.genre?.let { put("genre", it) }
        put("status", m.status)
    }

    private fun chapterJson(c: SChapter): JsonObject = buildJsonObject {
        put("url", c.url)
        put("name", c.name)
        put("chapter_number", c.chapter_number.toDouble())
        c.scanlator?.let { put("scanlator", it) }
        put("date_upload", c.date_upload)
    }
}
