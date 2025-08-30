<template>
  <div class="indexer-health-monitor">
    <!-- Indexer Status Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      <div 
        v-for="(indexer, name) in indexerData.indexers" 
        :key="name"
        class="bg-white dark:bg-dark-800 rounded-lg shadow p-6"
      >
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center">
            <div 
              class="w-3 h-3 rounded-full mr-3"
              :class="getStatusColor(indexer.status)"
            ></div>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              {{ formatIndexerName(name) }}
            </h3>
          </div>
          <span 
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
            :class="getTierClass(indexer.tier)"
          >
            {{ indexer.tier }}
          </span>
        </div>

        <div class="space-y-2">
          <div class="flex justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">Status</span>
            <span 
              class="text-sm font-medium capitalize"
              :class="getStatusTextColor(indexer.status)"
            >
              {{ indexer.status }}
            </span>
          </div>
          
          <div v-if="indexer.response_time_ms" class="flex justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">Response Time</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">
              {{ indexer.response_time_ms }}ms
            </span>
          </div>

          <div v-if="indexer.message" class="mt-3">
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ indexer.message }}
            </p>
          </div>
        </div>

        <!-- Test Button -->
        <div class="mt-4">
          <button
            @click="testIndexer(name)"
            :disabled="testingIndexers.has(name)"
            class="w-full inline-flex justify-center items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            <svg 
              v-if="testingIndexers.has(name)"
              class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" 
              fill="none" 
              viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ testingIndexers.has(name) ? 'Testing...' : 'Test Connection' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Summary Statistics -->
    <div class="bg-white dark:bg-dark-800 rounded-lg shadow">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-dark-700">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">Indexer Summary</h3>
      </div>
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="text-center">
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">
              {{ indexerData.summary?.healthy_count || 0 }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Healthy</div>
          </div>
          
          <div class="text-center">
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ indexerData.summary?.total_count || 0 }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Total</div>
          </div>
          
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {{ indexerData.summary?.health_percentage || 0 }}%
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Health Rate</div>
          </div>
          
          <div class="text-center">
            <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {{ indexerData.response_time_ms || 0 }}ms
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Avg Response</div>
          </div>
        </div>

        <!-- Last Updated -->
        <div class="mt-6 text-center">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Last updated: {{ formatTimestamp(indexerData.timestamp) }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import api from '../services/api';

export default {
  name: 'IndexerHealthMonitor',
  props: {
    autoRefresh: {
      type: Boolean,
      default: false
    }
  },
  
  setup(props) {
    const indexerData = ref({ indexers: {}, summary: {} });
    const loading = ref(false);
    const testingIndexers = ref(new Set());
    let refreshInterval = null;

    const fetchIndexerHealth = async () => {
      if (loading.value) return;
      
      loading.value = true;
      try {
        const response = await api.get('/api/v1/health/indexers');
        indexerData.value = response.data;
      } catch (error) {
        console.error('Error fetching indexer health:', error);
        indexerData.value = { indexers: {}, summary: {} };
      } finally {
        loading.value = false;
      }
    };

    const testIndexer = async (indexerName) => {
      testingIndexers.value.add(indexerName);
      
      try {
        // Test specific indexer
        const response = await api.post(`/search/enhanced/test-indexer`, {
          indexer: indexerName.toLowerCase()
        });
        
        // Refresh data after test
        await fetchIndexerHealth();
        
        // Show success message
        console.log(`${indexerName} test completed:`, response.data);
      } catch (error) {
        console.error(`Error testing ${indexerName}:`, error);
      } finally {
        testingIndexers.value.delete(indexerName);
      }
    };

    const formatIndexerName = (name) => {
      const nameMap = {
        'mangaupdates': 'MangaUpdates',
        'madaradex': 'MadaraDex',
        'mangadx': 'MangaDx'
      };
      return nameMap[name.toLowerCase()] || name;
    };

    const getStatusColor = (status) => {
      if (status === 'healthy') return 'bg-green-500';
      if (status === 'degraded') return 'bg-yellow-500';
      return 'bg-red-500';
    };

    const getStatusTextColor = (status) => {
      if (status === 'healthy') return 'text-green-600 dark:text-green-400';
      if (status === 'degraded') return 'text-yellow-600 dark:text-yellow-400';
      return 'text-red-600 dark:text-red-400';
    };

    const getTierClass = (tier) => {
      if (tier === 'primary') return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      if (tier === 'secondary') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    };

    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'Never';
      return new Date(timestamp * 1000).toLocaleString();
    };

    const startAutoRefresh = () => {
      if (refreshInterval) return;
      refreshInterval = setInterval(fetchIndexerHealth, 30000); // 30 seconds
    };

    const stopAutoRefresh = () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
      }
    };

    watch(() => props.autoRefresh, (newValue) => {
      if (newValue) {
        startAutoRefresh();
      } else {
        stopAutoRefresh();
      }
    });

    onMounted(() => {
      fetchIndexerHealth();
      if (props.autoRefresh) {
        startAutoRefresh();
      }
    });

    onUnmounted(() => {
      stopAutoRefresh();
    });

    return {
      indexerData,
      loading,
      testingIndexers,
      testIndexer,
      formatIndexerName,
      getStatusColor,
      getStatusTextColor,
      getTierClass,
      formatTimestamp
    };
  }
};
</script>

<style scoped>
.indexer-health-monitor {
  /* Component-specific styles */
}
</style>
