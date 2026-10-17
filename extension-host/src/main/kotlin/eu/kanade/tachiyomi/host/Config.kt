package eu.kanade.tachiyomi.host

import java.io.File

// Runtime settings. All come from the environment so the container can set them.
data class Config(
    val port: Int,
    val token: String,
    val dataDir: File,
    val githubApi: String = "https://api.github.com",
) {
    val jarsDir: File get() = File(dataDir, "jars")
    val indexFile: File get() = File(jarsDir, "index.json")
    val stateFile: File get() = File(dataDir, "state.json")

    companion object {
        fun fromEnv(): Config {
            val token = System.getenv("HOST_TOKEN")?.takeIf { it.isNotBlank() }
                ?: error("HOST_TOKEN must be set")
            return Config(
                port = System.getenv("HOST_PORT")?.toIntOrNull() ?: 8800,
                token = token,
                dataDir = File(System.getenv("HOST_DATA_DIR") ?: "data"),
                githubApi = System.getenv("HOST_GITHUB_API")?.takeIf { it.isNotBlank() } ?: "https://api.github.com",
            )
        }
    }
}
