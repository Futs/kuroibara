package eu.kanade.tachiyomi.host

import eu.kanade.tachiyomi.host.api.Server

fun main() {
    HostRuntime.init()
    val config = Config.fromEnv()
    Server(config).start()
    println("extension-host listening on :${config.port} (data: ${config.dataDir.absolutePath})")
}
