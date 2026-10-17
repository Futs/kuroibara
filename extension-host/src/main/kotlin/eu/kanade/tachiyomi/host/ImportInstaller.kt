package eu.kanade.tachiyomi.host

import eu.kanade.tachiyomi.host.loader.ExtensionLoader
import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.security.MessageDigest
import java.util.zip.ZipFile

// Installs a JAR the user provides (for example one built with tools/build-jars.py). Checked before it is kept:
// it must be a zip with our entry class, and it must load and expose at least one source. Failed imports leave nothing behind.
class ImportInstaller(private val config: Config) {
    class ImportError(message: String) : IOException(message)

    data class Imported(val relativePath: String, val sha256: String, val packageName: String, val sourceNames: List<String>)

    fun import(module: String, bytes: ByteArray): Imported {
        if (!MODULE.matches(module)) throw ImportError("module must look like lang/name, for example en/myextension")
        if (bytes.isEmpty()) throw ImportError("the upload is empty")
        if (bytes.size > MAX_BYTES) throw ImportError("the JAR is larger than ${MAX_BYTES / 1_000_000} MB")
        if (bytes.size < 4 || bytes[0] != 'P'.code.toByte() || bytes[1] != 'K'.code.toByte()) {
            throw ImportError("not a JAR (zip) file")
        }

        config.importsDir.mkdirs()
        val tmp = File(config.importsDir, "${module.replace('/', '_')}.part")
        tmp.writeBytes(bytes)
        try {
            checkEntries(tmp)
            val sha = sha256(bytes)
            val name = "${module.replace('/', '_')}@${sha.take(8)}.jar"
            val target = File(config.importsDir, name)
            Files.move(tmp.toPath(), target.toPath(), StandardCopyOption.REPLACE_EXISTING)
            val sources = try {
                ExtensionLoader.load("import:$module", listOf(target)).sources
            } catch (e: Throwable) {
                target.delete()
                throw ImportError("the JAR does not load as an extension: ${e.javaClass.simpleName}: ${e.message}".take(300))
            }
            if (sources.isEmpty()) {
                target.delete()
                throw ImportError("the JAR loads but exposes no sources")
            }
            return Imported(
                relativePath = "imported/$name",
                sha256 = sha,
                packageName = "eu.kanade.tachiyomi.extension.${module.replace('/', '.')}",
                sourceNames = sources.map { it.name },
            )
        } finally {
            tmp.delete()
        }
    }

    private fun checkEntries(file: File) {
        val names = try {
            ZipFile(file).use { zip -> zip.entries().toList().map { it.name } }
        } catch (e: IOException) {
            throw ImportError("not a readable JAR (zip) file")
        }
        if ("keiyoushi/source/Generated.class" !in names) {
            throw ImportError("the JAR is missing keiyoushi/source/Generated.class; it is not a Keiyoushi extension")
        }
    }

    companion object {
        const val MAX_BYTES = 30_000_000
        private val MODULE = Regex("^[a-z0-9]+/[a-z0-9_]+$")

        fun sha256(bytes: ByteArray): String =
            MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
    }
}
