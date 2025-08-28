<template>
  <div class="monitoring-dashboard min-h-screen bg-gray-50 dark:bg-dark-900">
    <!-- Header -->
    <div class="bg-white dark:bg-dark-800 shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
                System Monitoring
              </h1>
              <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                Real-time monitoring of providers, indexers, and system health
              </p>
            </div>
            <div class="flex items-center space-x-4">
              <!-- Auto-refresh toggle -->
              <div class="flex items-center space-x-2">
                <label class="text-sm text-gray-700 dark:text-gray-300">Auto-refresh</label>
                <button
                  @click="toggleAutoRefresh"
                  :class="[
                    'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                    autoRefresh ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'
                  ]"
                >
                  <span
                    :class="[
                      'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                      autoRefresh ? 'translate-x-5' : 'translate-x-0'
                    ]"
                  />
                </button>
              </div>
              
              <!-- Refresh button -->
              <button
                @click="refreshAll"
                :disabled="refreshing"
                class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                <svg 
                  v-if="refreshing"
                  class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" 
                  fill="none" 
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg 
                  v-else
                  class="-ml-1 mr-2 h-4 w-4" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {{ refreshing ? 'Refreshing...' : 'Refresh All' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- System Health Overview -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">System Health Overview</h2>
        <SystemHealthOverview :auto-refresh="autoRefresh" />
      </div>

      <!-- Indexer Health -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Indexer Health</h2>
        <IndexerHealthMonitor :auto-refresh="autoRefresh" />
      </div>

      <!-- Provider Health Monitor -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Provider Health</h2>
        <ProviderHealthMonitor />
      </div>

      <!-- Provider Analytics -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Provider Analytics</h2>
        <ProviderAnalytics />
      </div>

      <!-- Security Dashboard -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Security Status</h2>
        <SecurityDashboard />
      </div>

      <!-- Torrent Indexer Health -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Torrent Indexers</h2>
        <TorrentIndexerHealth :auto-refresh="autoRefresh" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue';
import ProviderHealthMonitor from '../components/ProviderHealthMonitor.vue';
import ProviderAnalytics from '../components/ProviderAnalytics.vue';
import SecurityDashboard from '../components/SecurityDashboard.vue';
import SystemHealthOverview from '../components/SystemHealthOverview.vue';
import IndexerHealthMonitor from '../components/IndexerHealthMonitor.vue';
import TorrentIndexerHealth from '../components/TorrentIndexerHealth.vue';

export default {
  name: 'Monitoring',
  components: {
    ProviderHealthMonitor,
    ProviderAnalytics,
    SecurityDashboard,
    SystemHealthOverview,
    IndexerHealthMonitor,
    TorrentIndexerHealth
  },
  
  setup() {
    const autoRefresh = ref(true);
    const refreshing = ref(false);
    let refreshInterval = null;

    const toggleAutoRefresh = () => {
      autoRefresh.value = !autoRefresh.value;
      
      if (autoRefresh.value) {
        startAutoRefresh();
      } else {
        stopAutoRefresh();
      }
    };

    const startAutoRefresh = () => {
      if (refreshInterval) return;
      
      refreshInterval = setInterval(() => {
        refreshAll();
      }, 30000); // Refresh every 30 seconds
    };

    const stopAutoRefresh = () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
      }
    };

    const refreshAll = async () => {
      refreshing.value = true;
      
      try {
        // Emit refresh events to child components
        // This will be handled by the individual components
        await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate refresh
      } catch (error) {
        console.error('Error refreshing monitoring data:', error);
      } finally {
        refreshing.value = false;
      }
    };

    onMounted(() => {
      if (autoRefresh.value) {
        startAutoRefresh();
      }
    });

    onUnmounted(() => {
      stopAutoRefresh();
    });

    return {
      autoRefresh,
      refreshing,
      toggleAutoRefresh,
      refreshAll
    };
  }
};
</script>

<style scoped>
.monitoring-dashboard {
  min-height: 100vh;
}
</style>
