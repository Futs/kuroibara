package eu.kanade.tachiyomi.host

import java.util.concurrent.CompletableFuture
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException

// Keeps one extension from taking the host down with it, as far as a JVM allows:
// - every call runs on its own thread, and the caller gives up after a deadline (the thread is abandoned, not waited for);
// - at most `maxConcurrentPerModule` calls per extension run at once, so a hung extension cannot exhaust the host;
// - after `failuresToOpen` failures in a row the extension is short-circuited for `cooldownMs`, then tried again.
// It cannot stop an extension that exits the JVM (System.exit), or one that exhausts memory for the whole process.
// Those need process isolation, which is a later step (see the TODO, Phase 1 step 4).
// Nothing here removes an extension. The state is reported, and the next call after the cooldown tries again.
class Isolation(
    private val clock: () -> Long = System::currentTimeMillis,
    private val maxConcurrentPerModule: Int = 2,
    private val acquireTimeoutMs: Long = 5_000,
    private val failuresToOpen: Int = 5,
    private val cooldownMs: Long = 60_000,
) {
    class Unavailable(message: String) : RuntimeException(message)
    class Timed(message: String) : RuntimeException(message)

    private val slots = ConcurrentHashMap<String, Semaphore>()
    private val failures = ConcurrentHashMap<String, Int>()
    private val openUntil = ConcurrentHashMap<String, Long>()
    private val executor = Executors.newCachedThreadPool { r -> Thread(r, "ext-call").apply { isDaemon = true } }

    fun <T> run(module: String, timeoutMs: Long, block: () -> T): T {
        openUntil[module]?.let { until ->
            if (clock() < until) {
                throw Unavailable("$module is paused after repeated failures; it will be tried again in ${(until - clock()) / 1000}s")
            }
            openUntil.remove(module)
        }
        val slot = slots.computeIfAbsent(module) { Semaphore(maxConcurrentPerModule, true) }
        if (!slot.tryAcquire(acquireTimeoutMs, TimeUnit.MILLISECONDS)) {
            throw Unavailable("$module is busy: too many calls are already running")
        }
        val future = CompletableFuture.supplyAsync({ block() }, executor)
        try {
            val value = future.get(timeoutMs, TimeUnit.MILLISECONDS)
            failures.remove(module)
            return value
        } catch (e: TimeoutException) {
            future.cancel(true)
            recordFailure(module)
            throw Timed("$module did not answer within ${timeoutMs / 1000}s")
        } catch (e: ExecutionException) {
            recordFailure(module)
            throw e.cause ?: e
        } finally {
            slot.release()
        }
    }

    private fun recordFailure(module: String) {
        val n = (failures[module] ?: 0) + 1
        if (n >= failuresToOpen) {
            openUntil[module] = clock() + cooldownMs
            failures.remove(module)
        } else {
            failures[module] = n
        }
    }

    // For the health view: whether calls are currently being short-circuited, and until when.
    fun pausedUntil(module: String): Long? = openUntil[module]?.takeIf { clock() < it }
}
