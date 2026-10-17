package eu.kanade.tachiyomi.host.upstream

import eu.kanade.tachiyomi.host.catalog.UpstreamExtension
import java.io.File
import java.io.IOException
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.security.MessageDigest
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// Downloads an upstream extension JAR and checks it against the SHA-256 that GitHub publishes for the
// release asset. Fails closed: no digest, or a digest mismatch, means no install.
class UpstreamInstaller(
    private val githubApi: String,
    private val jarsDir: File,
    private val githubToken: String? = System.getenv("GITHUB_TOKEN")?.takeIf { it.isNotBlank() },
) {
    private val client = HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NORMAL).build()

    class VerificationError(message: String) : IOException(message)

    data class Fetched(val file: File, val relativePath: String, val sha256: String)

    // Returns the verified JAR, stored under jars/upstream/. A file already present with the expected digest is reused.
    fun fetch(ext: UpstreamExtension): Fetched {
        val url = ext.jarUrl ?: throw VerificationError("no jar_url for ${ext.packageName}")
        val (tag, assetName) = parseReleaseUrl(url)
        val expected = expectedDigest(tag, assetName)
        val dir = File(jarsDir, "upstream").apply { mkdirs() }
        val target = File(dir, "${ext.packageName}@${ext.versionCode}-${expected.take(8)}.jar")
        val rel = "upstream/${target.name}"
        if (target.exists() && sha256(target) == expected) return Fetched(target, rel, expected)

        val tmp = File(dir, target.name + ".part")
        val req = HttpRequest.newBuilder(URI.create(url)).GET().build()
        val resp = client.send(req, HttpResponse.BodyHandlers.ofFile(tmp.toPath()))
        if (resp.statusCode() !in 200..299) {
            tmp.delete()
            throw IOException("download failed: HTTP ${resp.statusCode()} for $url")
        }
        val actual = sha256(tmp)
        if (actual != expected) {
            tmp.delete()
            throw VerificationError("sha256 mismatch for $assetName: expected $expected, got $actual")
        }
        Files.move(tmp.toPath(), target.toPath(), StandardCopyOption.REPLACE_EXISTING)
        return Fetched(target, rel, expected)
    }

    private fun expectedDigest(tag: String, assetName: String): String {
        val req = HttpRequest.newBuilder(URI.create("$githubApi/repos/keiyoushi/extensions/releases/tags/$tag"))
            .header("Accept", "application/vnd.github+json")
            .apply { githubToken?.let { header("Authorization", "Bearer $it") } }
            .GET().build()
        val resp = client.send(req, HttpResponse.BodyHandlers.ofString())
        if (resp.statusCode() !in 200..299) throw VerificationError("release lookup failed: HTTP ${resp.statusCode()} for tag $tag")
        val assets = Json.parseToJsonElement(resp.body()).jsonObject["assets"] as? JsonArray
            ?: throw VerificationError("release $tag has no assets list")
        val asset = assets.map { it.jsonObject }.firstOrNull { it["name"]?.jsonPrimitive?.content == assetName }
            ?: throw VerificationError("asset $assetName not in release $tag")
        val digest = asset["digest"]?.jsonPrimitive?.content?.takeIf { it.startsWith("sha256:") }
            ?: throw VerificationError("no sha256 digest for $assetName in release $tag")
        return digest.removePrefix("sha256:")
    }

    companion object {
        // https://github.com/keiyoushi/extensions/releases/download/<tag>/<asset>
        fun parseReleaseUrl(url: String): Pair<String, String> {
            val m = Regex("/releases/download/([^/]+)/([^/?#]+)$").find(url)
                ?: throw VerificationError("not a release asset URL: $url")
            return m.groupValues[1] to m.groupValues[2]
        }

        fun sha256(file: File): String {
            val md = MessageDigest.getInstance("SHA-256")
            file.inputStream().use { input ->
                val buf = ByteArray(64 * 1024)
                while (true) {
                    val n = input.read(buf)
                    if (n < 0) break
                    md.update(buf, 0, n)
                }
            }
            return md.digest().joinToString("") { "%02x".format(it) }
        }
    }
}
