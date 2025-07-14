<template>
  <div class="provider-health-monitor bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Provider Health Monitor</h2>
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 rounded-full" :class="monitoringStatus.color"></div>
          <span class="text-sm text-gray-600 dark:text-gray-400">{{ monitoringStatus.text }}</span>
        </div>
        <button
          @click="toggleMonitoring"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          {{ monitoringEnabled ? 'Stop Monitoring' : 'Start Monitoring' }}
        </button>
        <button
          @click="checkAllProviders"
          :disabled="checking"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          {{ checking ? 'Checking...' : 'Check All' }}
        </button>
      </div>
    </div>

    <!-- Health Overview -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-green-600 dark:text-green-400 text-2xl mr-3">✅</div>
          <div>
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">
              {{ healthStats.healthy }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Healthy</div>
          </div>
        </div>
      </div>
      
      <div class="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-red-600 dark:text-red-400 text-2xl mr-3">❌</div>
          <div>
            <div class="text-2xl font-bold text-red-600 dark:text-red-400">
              {{ healthStats.unhealthy }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Unhealthy</div>
          </div>
        </div>
      </div>
      
      <div class="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-yellow-600 dark:text-yellow-400 text-2xl mr-3">⚠️</div>
          <div>
            <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {{ healthStats.warning }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Warning</div>
          </div>
        </div>
      </div>
      
      <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-gray-600 dark:text-gray-400 text-2xl mr-3">⏸️</div>
          <div>
            <div class="text-2xl font-bold text-gray-600 dark:text-gray-400">
              {{ healthStats.disabled }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Disabled</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters and Controls -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-4">
        <select
          v-model="filterStatus"
          class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
        >
          <option value="all">All Providers</option>
          <option value="healthy">Healthy Only</option>
          <option value="unhealthy">Unhealthy Only</option>
          <option value="warning">Warning Only</option>
          <option value="disabled">Disabled Only</option>
        </select>
        
        <select
          v-model="sortBy"
          class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
        >
          <option value="name">Sort by Name</option>
          <option value="status">Sort by Status</option>
          <option value="uptime">Sort by Uptime</option>
          <option value="response_time">Sort by Response Time</option>
          <option value="last_check">Sort by Last Check</option>
        </select>
        
        <button
          @click="toggleSortOrder"
          class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md hover:bg-gray-50 dark:hover:bg-dark-700 transition-colors"
        >
          {{ sortOrder === 'asc' ? '↑' : '↓' }}
        </button>
      </div>
      
      <div class="flex items-center space-x-2">
        <button
          @click="exportHealthData"
          class="px-3 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
        >
          Export Data
        </button>
        <button
          @click="showSettings = true"
          class="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Settings
        </button>
      </div>
    </div>

    <!-- Provider List -->
    <div class="space-y-4">
      <div
        v-for="provider in filteredProviders"
        :key="provider.id"
        class="border border-gray-200 dark:border-dark-600 rounded-lg p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <!-- Status Indicator -->
            <div class="flex items-center space-x-2">
              <div 
                class="w-4 h-4 rounded-full"
                :class="getStatusColor(provider)"
              ></div>
              <span class="font-medium text-gray-900 dark:text-white">{{ provider.name }}</span>
            </div>
            
            <!-- Health Metrics -->
            <div class="flex items-center space-x-6 text-sm text-gray-600 dark:text-gray-400">
              <div class="flex items-center space-x-1">
                <span>Uptime:</span>
                <span class="font-medium">{{ provider.uptime_percentage || 0 }}%</span>
              </div>
              <div class="flex items-center space-x-1">
                <span>Response:</span>
                <span class="font-medium">{{ formatResponseTime(provider.response_time) }}</span>
              </div>
              <div class="flex items-center space-x-1">
                <span>Last Check:</span>
                <span class="font-medium">{{ formatLastCheck(provider.last_check) }}</span>
              </div>
              <div class="flex items-center space-x-1">
                <span>Failures:</span>
                <span class="font-medium">{{ provider.consecutive_failures || 0 }}</span>
              </div>
            </div>
          </div>
          
          <!-- Actions -->
          <div class="flex items-center space-x-2">
            <button
              @click="checkProviderHealth(provider.id)"
              :disabled="checkingProviders.has(provider.id)"
              class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {{ checkingProviders.has(provider.id) ? 'Checking...' : 'Check' }}
            </button>
            <button
              @click="toggleProvider(provider)"
              class="px-3 py-1 text-sm rounded transition-colors"
              :class="provider.is_enabled 
                ? 'bg-red-600 text-white hover:bg-red-700' 
                : 'bg-green-600 text-white hover:bg-green-700'"
            >
              {{ provider.is_enabled ? 'Disable' : 'Enable' }}
            </button>
            <button
              @click="showProviderDetails(provider)"
              class="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
            >
              Details
            </button>
          </div>
        </div>
        
        <!-- Error Message -->
        <div v-if="provider.error_message" class="mt-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
          {{ provider.error_message }}
        </div>
        
        <!-- Health History Chart -->
        <div v-if="showHealthHistory && getProviderHistory(provider.id).length > 0" class="mt-4">
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Health History (Last 24h)</div>
          <div class="flex items-end space-x-1 h-16">
            <div
              v-for="(point, index) in getProviderHistory(provider.id).slice(-48)"
              :key="index"
              class="flex-1 rounded-t"
              :class="point.isHealthy ? 'bg-green-500' : 'bg-red-500'"
              :style="{ height: `${point.responseTime ? Math.min((point.responseTime / 1000) * 100, 100) : (point.isHealthy ? 20 : 10)}%` }"
              :title="`${formatTime(point.timestamp)}: ${point.isHealthy ? 'Healthy' : 'Unhealthy'} (${point.responseTime || 'N/A'}ms)`"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Settings Modal -->
    <div
      v-if="showSettings"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showSettings = false"
    >
      <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
        
        <div class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div>
            <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4">
              Health Monitor Settings
            </h3>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Check Interval (minutes)
                </label>
                <input
                  v-model.number="settings.checkInterval"
                  type="number"
                  min="1"
                  max="60"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Request Timeout (seconds)
                </label>
                <input
                  v-model.number="settings.timeout"
                  type="number"
                  min="5"
                  max="120"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Max Consecutive Failures
                </label>
                <input
                  v-model.number="settings.maxFailures"
                  type="number"
                  min="1"
                  max="10"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                />
              </div>
              
              <div class="flex items-center">
                <input
                  v-model="settings.autoFailover"
                  type="checkbox"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Enable automatic failover
                </label>
              </div>
              
              <div class="flex items-center">
                <input
                  v-model="showHealthHistory"
                  type="checkbox"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Show health history charts
                </label>
              </div>
            </div>
          </div>
          
          <div class="mt-5 sm:mt-6 flex space-x-3">
            <button
              @click="saveSettings"
              class="flex-1 inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
            >
              Save
            </button>
            <button
              @click="showSettings = false"
              class="flex-1 inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-700 text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useProvidersStore } from '../stores/providers';

const providersStore = useProvidersStore();

// Local state
const monitoringEnabled = ref(true);
const checking = ref(false);
const checkingProviders = ref(new Set());
const filterStatus = ref('all');
const sortBy = ref('name');
const sortOrder = ref('asc');
const showSettings = ref(false);
const showHealthHistory = ref(true);

// Settings
const settings = ref({
  checkInterval: 5,
  timeout: 30,
  maxFailures: 3,
  autoFailover: true,
});

// Monitoring interval
let monitoringInterval = null;

// Computed properties
const monitoringStatus = computed(() => {
  if (monitoringEnabled.value) {
    return {
      color: 'bg-green-500',
      text: 'Monitoring Active'
    };
  } else {
    return {
      color: 'bg-gray-500',
      text: 'Monitoring Stopped'
    };
  }
});

const healthStats = computed(() => {
  const providers = providersStore.getProviders;
  return {
    healthy: providers.filter(p => p.is_healthy && p.is_enabled).length,
    unhealthy: providers.filter(p => !p.is_healthy && p.is_enabled).length,
    warning: providers.filter(p => p.consecutive_failures > 0 && p.consecutive_failures < 3).length,
    disabled: providers.filter(p => !p.is_enabled).length,
  };
});

const filteredProviders = computed(() => {
  let providers = [...providersStore.getProviders];
  
  // Apply status filter
  switch (filterStatus.value) {
    case 'healthy':
      providers = providers.filter(p => p.is_healthy && p.is_enabled);
      break;
    case 'unhealthy':
      providers = providers.filter(p => !p.is_healthy && p.is_enabled);
      break;
    case 'warning':
      providers = providers.filter(p => p.consecutive_failures > 0 && p.consecutive_failures < 3);
      break;
    case 'disabled':
      providers = providers.filter(p => !p.is_enabled);
      break;
  }
  
  // Apply sorting
  providers.sort((a, b) => {
    let aVal, bVal;
    
    switch (sortBy.value) {
      case 'name':
        aVal = a.name.toLowerCase();
        bVal = b.name.toLowerCase();
        break;
      case 'status':
        aVal = a.is_healthy ? 1 : 0;
        bVal = b.is_healthy ? 1 : 0;
        break;
      case 'uptime':
        aVal = a.uptime_percentage || 0;
        bVal = b.uptime_percentage || 0;
        break;
      case 'response_time':
        aVal = a.response_time || 9999;
        bVal = b.response_time || 9999;
        break;
      case 'last_check':
        aVal = new Date(a.last_check || 0);
        bVal = new Date(b.last_check || 0);
        break;
      default:
        return 0;
    }
    
    if (sortOrder.value === 'desc') {
      return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
    } else {
      return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
    }
  });
  
  return providers;
});

// Methods
const getStatusColor = (provider) => {
  if (!provider.is_enabled) return 'bg-gray-500';
  if (!provider.is_healthy) return 'bg-red-500';
  if (provider.consecutive_failures > 0) return 'bg-yellow-500';
  return 'bg-green-500';
};

const formatResponseTime = (time) => {
  if (!time) return 'N/A';
  return `${time}ms`;
};

const formatLastCheck = (timestamp) => {
  if (!timestamp) return 'Never';
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return `${Math.floor(diff / 86400000)}d ago`;
};

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString();
};

const getProviderHistory = (providerId) => {
  // This would come from the store's health history
  return providersStore.healthHistory.get(providerId) || [];
};

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
};

const toggleMonitoring = () => {
  monitoringEnabled.value = !monitoringEnabled.value;
  
  if (monitoringEnabled.value) {
    startMonitoring();
  } else {
    stopMonitoring();
  }
};

const startMonitoring = () => {
  if (monitoringInterval) return;
  
  monitoringInterval = setInterval(() => {
    checkAllProviders();
  }, settings.value.checkInterval * 60 * 1000);
};

const stopMonitoring = () => {
  if (monitoringInterval) {
    clearInterval(monitoringInterval);
    monitoringInterval = null;
  }
};

const checkAllProviders = async () => {
  checking.value = true;
  
  try {
    const providers = providersStore.getProviders.filter(p => p.is_enabled);
    const promises = providers.map(provider => checkProviderHealth(provider.id));
    await Promise.allSettled(promises);
  } finally {
    checking.value = false;
  }
};

const checkProviderHealth = async (providerId) => {
  checkingProviders.value.add(providerId);
  
  try {
    await providersStore.checkProviderHealth(providerId);
  } catch (error) {
    console.error(`Health check failed for provider ${providerId}:`, error);
  } finally {
    checkingProviders.value.delete(providerId);
  }
};

const toggleProvider = async (provider) => {
  try {
    await providersStore.updateProviderStatus(provider.id, !provider.is_enabled);
  } catch (error) {
    console.error('Error toggling provider:', error);
  }
};

const showProviderDetails = (provider) => {
  // Emit event or navigate to provider details
  console.log('Show details for provider:', provider);
};

const exportHealthData = () => {
  const data = {
    timestamp: new Date().toISOString(),
    providers: providersStore.getProviders.map(p => ({
      id: p.id,
      name: p.name,
      is_healthy: p.is_healthy,
      is_enabled: p.is_enabled,
      uptime_percentage: p.uptime_percentage,
      response_time: p.response_time,
      consecutive_failures: p.consecutive_failures,
      last_check: p.last_check,
      error_message: p.error_message,
    })),
    healthStats: healthStats.value,
  };
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `provider-health-${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
};

const saveSettings = () => {
  // Save settings to store or localStorage
  localStorage.setItem('providerHealthSettings', JSON.stringify(settings.value));
  showSettings.value = false;
  
  // Restart monitoring with new interval
  if (monitoringEnabled.value) {
    stopMonitoring();
    startMonitoring();
  }
};

// Lifecycle
onMounted(async () => {
  // Load settings
  const savedSettings = localStorage.getItem('providerHealthSettings');
  if (savedSettings) {
    settings.value = { ...settings.value, ...JSON.parse(savedSettings) };
  }
  
  // Fetch providers and start monitoring
  await providersStore.fetchProviders();
  
  if (monitoringEnabled.value) {
    startMonitoring();
  }
});

onUnmounted(() => {
  stopMonitoring();
});
</script>

<style scoped>
.provider-health-monitor {
  max-height: 80vh;
  overflow-y: auto;
}
</style>
