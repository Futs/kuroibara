<template>
  <div
    class="provider-analytics bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6"
  >
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
        Provider Analytics
      </h2>
      <div class="flex items-center space-x-4">
        <select
          v-model="timeRange"
          class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
        >
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
        </select>
        <button
          @click="refreshData"
          :disabled="loading"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {{ loading ? "Loading..." : "Refresh" }}
        </button>
        <button
          @click="exportAnalytics"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
        >
          Export
        </button>
      </div>
    </div>

    <!-- Overview Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg">
        <div class="flex items-center">
          <div class="text-blue-600 dark:text-blue-400 text-3xl mr-4">📊</div>
          <div>
            <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {{ formatNumber(overviewStats.totalRequests) }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">
              Total Requests
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ getChangeIndicator(overviewStats.requestsChange) }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-green-50 dark:bg-green-900/20 p-6 rounded-lg">
        <div class="flex items-center">
          <div class="text-green-600 dark:text-green-400 text-3xl mr-4">✅</div>
          <div>
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">
              {{ overviewStats.successRate }}%
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">
              Success Rate
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ getChangeIndicator(overviewStats.successRateChange) }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-yellow-50 dark:bg-yellow-900/20 p-6 rounded-lg">
        <div class="flex items-center">
          <div class="text-yellow-600 dark:text-yellow-400 text-3xl mr-4">
            ⚡
          </div>
          <div>
            <div
              class="text-2xl font-bold text-yellow-600 dark:text-yellow-400"
            >
              {{ overviewStats.avgResponseTime }}ms
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">
              Avg Response Time
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ getChangeIndicator(overviewStats.responseTimeChange, true) }}
            </div>
          </div>
        </div>
      </div>

      <div class="bg-purple-50 dark:bg-purple-900/20 p-6 rounded-lg">
        <div class="flex items-center">
          <div class="text-purple-600 dark:text-purple-400 text-3xl mr-4">
            🔥
          </div>
          <div>
            <div
              class="text-2xl font-bold text-purple-600 dark:text-purple-400"
            >
              {{ overviewStats.activeProviders }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">
              Active Providers
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ overviewStats.totalProviders }} total
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
      <!-- Request Volume Chart -->
      <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Request Volume
        </h3>
        <div class="h-64 flex items-center justify-center">
          <canvas ref="requestVolumeChart" class="w-full h-full"></canvas>
        </div>
      </div>

      <!-- Response Time Chart -->
      <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Response Time Trends
        </h3>
        <div class="h-64 flex items-center justify-center">
          <canvas ref="responseTimeChart" class="w-full h-full"></canvas>
        </div>
      </div>
    </div>

    <!-- Provider Performance Table -->
    <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg mb-8">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Provider Performance
        </h3>
        <div class="flex items-center space-x-2">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search providers..."
            class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
          />
          <select
            v-model="sortBy"
            class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
          >
            <option value="requests">Requests</option>
            <option value="success_rate">Success Rate</option>
            <option value="response_time">Response Time</option>
            <option value="error_rate">Error Rate</option>
            <option value="popularity">Popularity</option>
          </select>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 dark:border-dark-600">
              <th
                class="text-left py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                Provider
              </th>
              <th
                class="text-right py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                Requests
              </th>
              <th
                class="text-right py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                Success Rate
              </th>
              <th
                class="text-right py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                Avg Response
              </th>
              <th
                class="text-right py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                Error Rate
              </th>
              <th
                class="text-right py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                Popularity
              </th>
              <th
                class="text-right py-3 px-4 font-medium text-gray-900 dark:text-white"
              >
                Last Used
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="provider in filteredProviders"
              :key="provider.id"
              class="border-b border-gray-100 dark:border-dark-600 hover:bg-gray-100 dark:hover:bg-dark-600"
            >
              <td class="py-3 px-4">
                <div class="flex items-center space-x-3">
                  <div
                    class="w-3 h-3 rounded-full"
                    :class="provider.is_healthy ? 'bg-green-500' : 'bg-red-500'"
                  ></div>
                  <span class="font-medium text-gray-900 dark:text-white">{{
                    provider.name
                  }}</span>
                </div>
              </td>
              <td class="py-3 px-4 text-right text-gray-600 dark:text-gray-300">
                {{ formatNumber(provider.analytics.totalRequests) }}
              </td>
              <td class="py-3 px-4 text-right">
                <span
                  class="font-medium"
                  :class="getSuccessRateColor(provider.analytics.successRate)"
                >
                  {{ provider.analytics.successRate }}%
                </span>
              </td>
              <td class="py-3 px-4 text-right">
                <span
                  class="font-medium"
                  :class="
                    getResponseTimeColor(provider.analytics.averageResponseTime)
                  "
                >
                  {{ provider.analytics.averageResponseTime }}ms
                </span>
              </td>
              <td class="py-3 px-4 text-right">
                <span
                  class="font-medium"
                  :class="getErrorRateColor(provider.analytics.errorRate)"
                >
                  {{ provider.analytics.errorRate }}%
                </span>
              </td>
              <td class="py-3 px-4 text-right">
                <div class="flex items-center justify-end">
                  <div
                    class="w-16 bg-gray-200 dark:bg-dark-600 rounded-full h-2 mr-2"
                  >
                    <div
                      class="bg-blue-500 h-2 rounded-full"
                      :style="{
                        width: `${Math.min((provider.analytics.popularityScore / 100) * 100, 100)}%`,
                      }"
                    ></div>
                  </div>
                  <span class="text-gray-600 dark:text-gray-300">{{
                    provider.analytics.popularityScore
                  }}</span>
                </div>
              </td>
              <td class="py-3 px-4 text-right text-gray-600 dark:text-gray-300">
                {{ formatLastUsed(provider.analytics.lastUsed) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Error Analysis -->
    <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Error Analysis
      </h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Error Types -->
        <div>
          <h4 class="text-md font-medium text-gray-900 dark:text-white mb-3">
            Error Types
          </h4>
          <div class="space-y-2">
            <div
              v-for="error in errorTypes"
              :key="error.type"
              class="flex items-center justify-between p-3 bg-white dark:bg-dark-800 rounded border"
            >
              <div>
                <div class="font-medium text-gray-900 dark:text-white">
                  {{ error.type }}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">
                  {{ error.description }}
                </div>
              </div>
              <div class="text-right">
                <div class="font-bold text-red-600 dark:text-red-400">
                  {{ error.count }}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">
                  {{ error.percentage }}%
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Errors -->
        <div>
          <h4 class="text-md font-medium text-gray-900 dark:text-white mb-3">
            Recent Errors
          </h4>
          <div class="space-y-2 max-h-64 overflow-y-auto">
            <div
              v-for="error in recentErrors"
              :key="error.id"
              class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="font-medium text-red-800 dark:text-red-200">{{
                  error.provider
                }}</span>
                <span class="text-xs text-red-600 dark:text-red-400">{{
                  formatTime(error.timestamp)
                }}</span>
              </div>
              <div class="text-sm text-red-700 dark:text-red-300">
                {{ error.message }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { useProvidersStore } from "../stores/providers";

const providersStore = useProvidersStore();

// Local state
const loading = ref(false);
const timeRange = ref("24h");
const searchQuery = ref("");
const sortBy = ref("requests");

// Chart refs
const requestVolumeChart = ref(null);
const responseTimeChart = ref(null);

// Mock data (would come from API)
const overviewStats = ref({
  totalRequests: 15420,
  requestsChange: 12.5,
  successRate: 94.2,
  successRateChange: 2.1,
  avgResponseTime: 847,
  responseTimeChange: -8.3,
  activeProviders: 12,
  totalProviders: 15,
});

const errorTypes = ref([
  {
    type: "Timeout",
    description: "Request timeout errors",
    count: 45,
    percentage: 35.2,
  },
  {
    type: "Rate Limited",
    description: "Rate limiting errors",
    count: 32,
    percentage: 25.0,
  },
  { type: "Not Found", description: "404 errors", count: 28, percentage: 21.9 },
  {
    type: "Server Error",
    description: "5xx server errors",
    count: 23,
    percentage: 18.0,
  },
]);

const recentErrors = ref([
  {
    id: 1,
    provider: "MangaDex",
    message: "Request timeout after 30 seconds",
    timestamp: new Date(Date.now() - 300000),
  },
  {
    id: 2,
    provider: "MangaKakalot",
    message: "Rate limit exceeded: 429 Too Many Requests",
    timestamp: new Date(Date.now() - 600000),
  },
  {
    id: 3,
    provider: "Mangahere",
    message: "Server error: 503 Service Unavailable",
    timestamp: new Date(Date.now() - 900000),
  },
]);

// Computed properties
const filteredProviders = computed(() => {
  let providers = [...providersStore.getProviders];

  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    providers = providers.filter((p) => p.name.toLowerCase().includes(query));
  }

  // Apply sorting
  providers.sort((a, b) => {
    let aVal, bVal;

    switch (sortBy.value) {
      case "requests":
        aVal = a.analytics?.totalRequests || 0;
        bVal = b.analytics?.totalRequests || 0;
        break;
      case "success_rate":
        aVal = a.analytics?.successRate || 0;
        bVal = b.analytics?.successRate || 0;
        break;
      case "response_time":
        aVal = a.analytics?.averageResponseTime || 9999;
        bVal = b.analytics?.averageResponseTime || 9999;
        break;
      case "error_rate":
        aVal = a.analytics?.errorRate || 0;
        bVal = b.analytics?.errorRate || 0;
        break;
      case "popularity":
        aVal = a.analytics?.popularityScore || 0;
        bVal = b.analytics?.popularityScore || 0;
        break;
      default:
        return 0;
    }

    return bVal - aVal; // Descending order
  });

  return providers;
});

// Methods
const formatNumber = (num) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toString();
};

const getChangeIndicator = (change, inverse = false) => {
  if (!change) return "";
  const isPositive = inverse ? change < 0 : change > 0;
  const symbol = isPositive ? "↗" : "↘";
  const color = isPositive ? "text-green-500" : "text-red-500";
  return `${symbol} ${Math.abs(change)}%`;
};

const getSuccessRateColor = (rate) => {
  if (rate >= 95) return "text-green-600 dark:text-green-400";
  if (rate >= 90) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
};

const getResponseTimeColor = (time) => {
  if (time <= 500) return "text-green-600 dark:text-green-400";
  if (time <= 1000) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
};

const getErrorRateColor = (rate) => {
  if (rate <= 2) return "text-green-600 dark:text-green-400";
  if (rate <= 5) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
};

const formatLastUsed = (timestamp) => {
  if (!timestamp) return "Never";
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return "Just now";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return `${Math.floor(diff / 86400000)}d ago`;
};

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString();
};

const refreshData = async () => {
  loading.value = true;
  try {
    await providersStore.fetchProviders();
    // Fetch analytics data
    // await providersStore.fetchAnalytics(timeRange.value);
  } finally {
    loading.value = false;
  }
};

const exportAnalytics = () => {
  const data = {
    timestamp: new Date().toISOString(),
    timeRange: timeRange.value,
    overview: overviewStats.value,
    providers: filteredProviders.value.map((p) => ({
      name: p.name,
      analytics: p.analytics,
    })),
    errors: {
      types: errorTypes.value,
      recent: recentErrors.value,
    },
  };

  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `provider-analytics-${new Date().toISOString().split("T")[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
};

const initializeCharts = async () => {
  await nextTick();

  // Initialize charts here (using Chart.js or similar)
  // This is a placeholder for chart initialization
  if (requestVolumeChart.value) {
    const ctx = requestVolumeChart.value.getContext("2d");
    // Initialize request volume chart
  }

  if (responseTimeChart.value) {
    const ctx = responseTimeChart.value.getContext("2d");
    // Initialize response time chart
  }
};

// Lifecycle
onMounted(async () => {
  await refreshData();
  await initializeCharts();
});
</script>

<style scoped>
.provider-analytics {
  max-height: 90vh;
  overflow-y: auto;
}
</style>
