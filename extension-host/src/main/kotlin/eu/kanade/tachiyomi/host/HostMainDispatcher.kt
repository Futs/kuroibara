@file:OptIn(kotlinx.coroutines.InternalCoroutinesApi::class)

package eu.kanade.tachiyomi.host

import kotlin.coroutines.CoroutineContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.MainCoroutineDispatcher
import kotlinx.coroutines.internal.MainDispatcherFactory

// No Android Looper on the JVM. Extensions that touch Dispatchers.Main run on the default pool instead.
class HostMainDispatcher : MainCoroutineDispatcher() {
    override val immediate: MainCoroutineDispatcher get() = this
    override fun dispatch(context: CoroutineContext, block: Runnable) = Dispatchers.Default.dispatch(context, block)
    override fun toString() = "HostMain"
}

class HostMainDispatcherFactory : MainDispatcherFactory {
    override fun createDispatcher(allFactories: List<MainDispatcherFactory>) = HostMainDispatcher()
    override fun hintOnError(): String? = null
    override val loadPriority: Int get() = 0
}
