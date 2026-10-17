package eu.kanade.tachiyomi.host.loader

import java.io.File
import java.net.URLClassLoader

// One loader per extension. The host runtime (source API, network, Injekt) is the parent,
// so every extension shares one copy of it. The extension, its multisrc theme and its
// resources load here, child-first, so two extensions can each have a class with the same name.
class ExtensionClassLoader(
    id: String,
    entries: List<File>,
    parent: ClassLoader,
) : URLClassLoader(
    entries.map { it.toURI().toURL() }.toTypedArray(),
    parent,
) {
    val id: String = id

    override fun loadClass(name: String, resolve: Boolean): Class<*> {
        synchronized(getClassLoadingLock(name)) {
            findLoadedClass(name)?.let { return it }
            // Host API classes always come from the parent so casts to Source etc. work.
            if (name.startsWith("eu.kanade.tachiyomi.source.") || name.startsWith("eu.kanade.tachiyomi.network.") ||
                name.startsWith("android.") || name.startsWith("kotlin.") || name.startsWith("kotlinx.") ||
                name.startsWith("java.") || name.startsWith("okhttp3.") || name.startsWith("okio.") ||
                name.startsWith("uy.kohesive.") || name.startsWith("eu.kanade.tachiyomi.host.") ||
                name.startsWith("keiyoushi.network.") || name.startsWith("keiyoushi.utils.") ||
                name.startsWith("keiyoushi.annotation.") || name.startsWith("keiyoushi.zip.")
            ) {
                return super.loadClass(name, resolve)
            }
            return try {
                findClass(name)
            } catch (e: ClassNotFoundException) {
                super.loadClass(name, resolve)
            }
        }
    }
}
