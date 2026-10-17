package eu.kanade.tachiyomi.host.loader

import eu.kanade.tachiyomi.source.Source
import java.io.File

class LoadedExtension(
    val id: String,
    val sources: List<Source>,
    val loader: ExtensionClassLoader,
)

// Loads an extension from its class directories or JARs, and instantiates its sources.
object ExtensionLoader {
    private const val ENTRY_CLASS = "keiyoushi.source.Generated"

    fun load(id: String, entries: List<File>): LoadedExtension {
        eu.kanade.tachiyomi.host.HostRuntime.init()
        val loader = ExtensionClassLoader(id, entries, ExtensionLoader::class.java.classLoader)
        val generated = loader.loadClass(ENTRY_CLASS)
        val ctor = generated.getDeclaredConstructor().apply { isAccessible = true }
        var instance: Any = ctor.newInstance()
        val createSources = runCatching { instance.javaClass.getMethod("createSources") }.getOrNull()
        val sources = if (createSources != null) {
            @Suppress("UNCHECKED_CAST")
            (createSources.invoke(instance) as List<Source>)
        } else {
            listOf(instance as Source)
        }
        return LoadedExtension(id, sources, loader)
    }
}
