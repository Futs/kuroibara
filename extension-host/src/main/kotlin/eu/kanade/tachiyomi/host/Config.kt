package eu.kanade.tachiyomi.host

import java.io.File

// Runtime settings. All come from the environment so the container can set them.
data class Config(
    val port: Int,
    val token: String,
    val dataDir: File,
    val githubApi: String = "https://api.github.com",
    val defaultCatalogUrl: String = DEFAULT_CATALOG_URL,
    val allowHttpCatalog: Boolean = false,
) {
    val jarsDir: File get() = File(dataDir, "jars")
    val indexFile: File get() = File(jarsDir, "index.json")
    val stateFile: File get() = File(dataDir, "state.json")
    val settingsFile: File get() = File(dataDir, "settings.json")
    val importsDir: File get() = File(jarsDir, "imported")

    companion object {
        const val DEFAULT_CATALOG_URL = "https://raw.githubusercontent.com/keiyoushi/extensions/repo/index.json"

        fun fromEnv(): Config {
            val token = System.getenv("HOST_TOKEN")?.takeIf { it.isNotBlank() }
                ?: error("HOST_TOKEN must be set")
            return Config(
                port = System.getenv("HOST_PORT")?.toIntOrNull() ?: 8800,
                token = token,
                dataDir = File(System.getenv("HOST_DATA_DIR") ?: "data"),
                githubApi = System.getenv("HOST_GITHUB_API")?.takeIf { it.isNotBlank() } ?: "https://api.github.com",
                defaultCatalogUrl = System.getenv("HOST_DEFAULT_CATALOG_URL")?.takeIf { it.isNotBlank() } ?: DEFAULT_CATALOG_URL,
                allowHttpCatalog = System.getenv("HOST_ALLOW_HTTP_CATALOG") == "1",
            )
        }
    }
}
