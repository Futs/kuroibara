<template>
  <div class="system-health-overview">
    <!-- Health Status Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <!-- Overall Status -->
      <div class="bg-white dark:bg-dark-800 rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center"
              :class="overallStatusColor"
            >
              <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">Overall Status</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 capitalize">{{ healthData.status || 'Loading...' }}</p>
          </div>
        </div>
      </div>

      <!-- Database Status -->
      <div class="bg-white dark:bg-dark-800 rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center"
              :class="databaseStatusColor"
            >
              <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">Database</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              {{ healthData.components?.database?.status || 'Unknown' }}
              <span v-if="healthData.components?.database?.response_time_ms" class="text-xs">
                ({{ healthData.components.database.response_time_ms }}ms)
              </span>
            </p>
          </div>
        </div>
      </div>

      <!-- Indexers Status -->
      <div class="bg-white dark:bg-dark-800 rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center"
              :class="indexersStatusColor"
            >
              <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">Indexers</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              {{ healthData.components?.indexers?.healthy_count || 0 }}/{{ healthData.components?.indexers?.total_count || 0 }} healthy
            </p>
          </div>
        </div>
      </div>

      <!-- Providers Status -->
      <div class="bg-white dark:bg-dark-800 rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center"
              :class="providersStatusColor"
            >
              <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">Providers</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              {{ healthData.components?.providers?.enabled_count || 0 }}/{{ healthData.components?.providers?.total_count || 0 }} enabled
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Detailed Health Information -->
    <div class="bg-white dark:bg-dark-800 rounded-lg shadow">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-dark-700">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">System Details</h3>
      </div>
      <div class="p-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Performance Metrics -->
          <div>
            <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Performance</h4>
            <dl class="space-y-2">
              <div class="flex justify-between">
                <dt class="text-sm text-gray-600 dark:text-gray-400">Response Time</dt>
                <dd class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ healthData.summary?.response_time_ms || 0 }}ms
                </dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-sm text-gray-600 dark:text-gray-400">Health Percentage</dt>
                <dd class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ healthData.summary?.health_percentage || 0 }}%
                </dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-sm text-gray-600 dark:text-gray-400">Last Updated</dt>
                <dd class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ formatTimestamp(healthData.timestamp) }}
                </dd>
              </div>
            </dl>
          </div>

          <!-- Component Status -->
          <div>
            <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Components</h4>
            <div class="space-y-2">
              <div v-for="(component, name) in healthData.components" :key="name" class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400 capitalize">{{ name }}</span>
                <span 
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                  :class="getComponentStatusClass(component.status)"
                >
                  {{ component.status }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import api from '../services/api';

export default {
  name: 'SystemHealthOverview',
  props: {
    autoRefresh: {
      type: Boolean,
      default: false
    }
  },
  
  setup(props) {
    const healthData = ref({});
    const loading = ref(false);
    let refreshInterval = null;

    const overallStatusColor = computed(() => {
      const status = healthData.value.status;
      if (status === 'healthy') return 'bg-green-500';
      if (status === 'degraded') return 'bg-yellow-500';
      return 'bg-red-500';
    });

    const databaseStatusColor = computed(() => {
      const status = healthData.value.components?.database?.status;
      if (status === 'healthy') return 'bg-green-500';
      return 'bg-red-500';
    });

    const indexersStatusColor = computed(() => {
      const status = healthData.value.components?.indexers?.status;
      if (status === 'healthy') return 'bg-green-500';
      if (status === 'degraded') return 'bg-yellow-500';
      return 'bg-red-500';
    });

    const providersStatusColor = computed(() => {
      const status = healthData.value.components?.providers?.status;
      if (status === 'healthy') return 'bg-green-500';
      return 'bg-red-500';
    });

    const fetchHealthData = async () => {
      if (loading.value) return;
      
      loading.value = true;
      try {
        const response = await api.get('/health/');
        healthData.value = response.data;
      } catch (error) {
        console.error('Error fetching health data:', error);
        healthData.value = { status: 'unhealthy', components: {} };
      } finally {
        loading.value = false;
      }
    };

    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'Never';
      return new Date(timestamp * 1000).toLocaleString();
    };

    const getComponentStatusClass = (status) => {
      if (status === 'healthy') return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      if (status === 'degraded') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    };

    const startAutoRefresh = () => {
      if (refreshInterval) return;
      refreshInterval = setInterval(fetchHealthData, 30000); // 30 seconds
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
      fetchHealthData();
      if (props.autoRefresh) {
        startAutoRefresh();
      }
    });

    onUnmounted(() => {
      stopAutoRefresh();
    });

    return {
      healthData,
      loading,
      overallStatusColor,
      databaseStatusColor,
      indexersStatusColor,
      providersStatusColor,
      formatTimestamp,
      getComponentStatusClass
    };
  }
};
</script>

<style scoped>
.system-health-overview {
  /* Component-specific styles */
}
</style>
