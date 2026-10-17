package eu.kanade.tachiyomi.host

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

// The isolation layer, with a fake clock. The "extensions" here are plain blocks that succeed, fail or hang.
class IsolationTest {
    private var now = 1_000_000L

    private fun isolation(max: Int = 2, acquire: Long = 50, failures: Int = 3, cooldown: Long = 60_000) =
        Isolation(clock = { now }, maxConcurrentPerModule = max, acquireTimeoutMs = acquire,
            failuresToOpen = failures, cooldownMs = cooldown)

    @Test
    fun successReturnsTheValue() {
        assertEquals(42, isolation().run("en/x", 1_000) { 42 })
    }

    @Test
    fun a_hanging_call_is_abandoned_at_the_deadline_and_the_host_carries_on() {
        val iso = isolation()
        val release = CountDownLatch(1)
        val started = System.currentTimeMillis()
        assertFailsWith<Isolation.Timed> {
            iso.run("en/x", 200) { release.await(30, TimeUnit.SECONDS); "late" }
        }
        assertTrue(System.currentTimeMillis() - started < 5_000, "caller must not wait for the hung call")
        release.countDown()
        assertEquals("ok", iso.run("en/x", 1_000) { "ok" })
    }

    @Test
    fun an_exception_from_the_extension_comes_back_as_itself() {
        val boom = IllegalStateException("boom")
        val thrown = assertFailsWith<IllegalStateException> { isolation().run("en/x", 1_000) { throw boom } }
        assertEquals("boom", thrown.message)
    }

    @Test
    fun repeated_failures_pause_the_extension_then_it_is_tried_again() {
        val iso = isolation(failures = 3, cooldown = 60_000)
        repeat(3) { assertFailsWith<IllegalStateException> { iso.run("en/x", 1_000) { throw IllegalStateException() } } }
        var ran = false
        assertFailsWith<Isolation.Unavailable> { iso.run("en/x", 1_000) { ran = true; 1 } }
        assertTrue(!ran, "a paused extension must not run")
        assertTrue(iso.pausedUntil("en/x") != null)

        now += 61_000
        assertEquals(7, iso.run("en/x", 1_000) { 7 })
        assertEquals(null, iso.pausedUntil("en/x"))
    }

    @Test
    fun a_success_resets_the_failure_count() {
        val iso = isolation(failures = 3)
        repeat(2) { assertFailsWith<IllegalStateException> { iso.run("en/x", 1_000) { throw IllegalStateException() } } }
        assertEquals(1, iso.run("en/x", 1_000) { 1 })
        repeat(2) { assertFailsWith<IllegalStateException> { iso.run("en/x", 1_000) { throw IllegalStateException() } } }
        assertEquals(2, iso.run("en/x", 1_000) { 2 }, "two failures after a success do not open the circuit")
    }

    @Test
    fun one_extension_pausing_does_not_pause_another() {
        val iso = isolation(failures = 1)
        assertFailsWith<IllegalStateException> { iso.run("en/bad", 1_000) { throw IllegalStateException() } }
        assertEquals("fine", iso.run("en/good", 1_000) { "fine" })
    }

    @Test
    fun too_many_concurrent_calls_for_one_extension_are_refused_not_queued_forever() {
        val iso = isolation(max = 1, acquire = 50)
        val hold = CountDownLatch(1)
        val first = Thread { iso.run("en/x", 5_000) { hold.await(10, TimeUnit.SECONDS); 1 } }
        first.start()
        Thread.sleep(100)
        assertFailsWith<Isolation.Unavailable> { iso.run("en/x", 1_000) { 2 } }
        hold.countDown()
        first.join(5_000)
    }
}
