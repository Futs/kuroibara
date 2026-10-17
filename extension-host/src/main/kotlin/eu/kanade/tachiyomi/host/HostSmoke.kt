package eu.kanade.tachiyomi.host

import eu.kanade.tachiyomi.host.loader.ExtensionLoader
import eu.kanade.tachiyomi.source.model.SChapter
import java.io.File
import kotlinx.coroutines.runBlocking

// Dev harness: each argument is one extension, given as comma-separated entries (classes dirs / jars).
// Loads all of them into one JVM and runs search, details, chapters and pages on each.
fun main(args: Array<String>) = runBlocking {
    val query = System.getenv("SMOKE_QUERY") ?: "one"
    for (arg in args) {
        val id = arg.substringBefore('=')
        val entries = arg.substringAfter('=').split(',').map { File(it) }
        try {
            val loaded = ExtensionLoader.load(id, entries)
            val src = loaded.sources.first()
            val page = src.getSearchManga(1, query, src.getFilterList())
            val first = page.mangas.firstOrNull()
            if (first == null) { println("$id: search n=0"); continue }
            val update = src.getMangaUpdate(first, emptyList(), fetchDetails = true, fetchChapters = true)
            val chapters: List<SChapter> = update.chapters
            val pages = if (chapters.isNotEmpty()) src.getPageList(chapters.last()).size else -1
            println("$id: ${src.name} search=${page.mangas.size} title=${update.manga.title} chapters=${chapters.size} pages=$pages")
        } catch (t: Throwable) {
            println("$id: ERR ${t.javaClass.name}: ${t.message}")
        }
    }
}
