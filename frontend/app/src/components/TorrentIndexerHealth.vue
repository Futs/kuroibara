<template>
  <div class="torrent-indexer-health">
    <!-- Health Overview Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      <!-- Overall Status -->
      <div class="bg-white dark:bg-dark-800 rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center"
              :class="overallStatusColor"
            >
              <svg
                class="w-5 h-5 text-white"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              Torrent Indexers
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 capitalize">
              {{ healthData.status || "Loading..." }}
            </p>
          </div>
        </div>
      </div>

      <!-- Healthy Count -->
      <div class="bg-white dark:bg-dark-800 rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div
              class="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center"
            >
              <svg
                class="w-5 h-5 text-white"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              Healthy
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              {{ healthData.healthy_count || 0 }}/{{
                healthData.total_count || 0
              }}
            </p>
          </div>
        </div>
      </div>

      <!-- Test All Button -->
      <div class="bg-white dark:bg-dark-800 rounded-lg shadow p-6">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              Actions
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Test all indexers
            </p>
          </div>
          <button
            @click="testAllIndexers"
            :disabled="testing"
            class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            <svg
              v-if="testing"
              class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            {{ testing ? "Testing..." : "Test All" }}
          </button>
        </div>
      </div>
    </div>

    <!-- Individual Indexer Status -->
    <div class="bg-white dark:bg-dark-800 rounded-lg shadow">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-dark-700">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          Indexer Status
        </h3>
      </div>
      <div class="p-6">
        <div v-if="loading" class="text-center py-8">
          <div class="inline-flex items-center">
            <svg
              class="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-500"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            Loading indexer status...
          </div>
        </div>

        <div
          v-else-if="Object.keys(healthData.indexers || {}).length === 0"
          class="text-center py-8"
        >
          <p class="text-gray-500 dark:text-gray-400">
            No torrent indexers configured
          </p>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="(status, indexerName) in healthData.indexers"
            :key="indexerName"
            class="flex items-center justify-between p-4 border border-gray-200 dark:border-dark-700 rounded-lg"
          >
            <div class="flex items-center">
              <div
                class="w-3 h-3 rounded-full mr-3"
                :class="getStatusColor(status[0])"
              ></div>
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ formatIndexerName(indexerName) }}
                </h4>
                <p class="text-sm text-gray-600 dark:text-gray-400">
                  {{ status[1] }}
                </p>
              </div>
            </div>

            <div class="flex items-center space-x-2">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="getStatusBadgeClass(status[0])"
              >
                {{ status[0] ? "Healthy" : "Unhealthy" }}
              </span>

              <button
                @click="testIndexer(indexerName)"
                :disabled="testingIndexers.has(indexerName)"
                class="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 disabled:opacity-50"
              >
                <svg
                  v-if="testingIndexers.has(indexerName)"
                  class="animate-spin -ml-1 mr-1 h-3 w-3"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="4"
                  ></circle>
                  <path
                    class="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                {{ testingIndexers.has(indexerName) ? "Testing..." : "Test" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import torrentService from "../services/torrentService";

export default {
  name: "TorrentIndexerHealth",
  props: {
    autoRefresh: {
      type: Boolean,
      default: false,
    },
  },

  setup(props) {
    const healthData = ref({});
    const loading = ref(false);
    const testing = ref(false);
    const testingIndexers = ref(new Set());
    let refreshInterval = null;

    const overallStatusColor = computed(() => {
      const status = healthData.value.status;
      if (status === "healthy") return "bg-green-500";
      if (status === "degraded") return "bg-yellow-500";
      return "bg-red-500";
    });

    const fetchHealthData = async () => {
      if (loading.value) return;

      loading.value = true;
      try {
        const response = await torrentService.checkIndexerHealth();
        healthData.value = response;
      } catch (error) {
        console.error("Error fetching torrent indexer health:", error);
        healthData.value = { status: "unhealthy", indexers: {} };
      } finally {
        loading.value = false;
      }
    };

    const testAllIndexers = async () => {
      testing.value = true;
      try {
        // Refresh health data after testing
        await fetchHealthData();
      } catch (error) {
        console.error("Error testing all indexers:", error);
      } finally {
        testing.value = false;
      }
    };

    const testIndexer = async (indexerName) => {
      testingIndexers.value.add(indexerName);

      try {
        await torrentService.testIndexer(indexerName);
        // Refresh health data after test
        await fetchHealthData();
      } catch (error) {
        console.error(`Error testing indexer ${indexerName}:`, error);
      } finally {
        testingIndexers.value.delete(indexerName);
      }
    };

    const formatIndexerName = (name) => {
      const nameMap = {
        nyaa: "Nyaa.si",
        "1337x": "1337x",
        thepiratebay: "The Pirate Bay",
      };
      return nameMap[name.toLowerCase()] || name;
    };

    const getStatusColor = (isHealthy) => {
      return isHealthy ? "bg-green-500" : "bg-red-500";
    };

    const getStatusBadgeClass = (isHealthy) => {
      return isHealthy
        ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
        : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
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

    watch(
      () => props.autoRefresh,
      (newValue) => {
        if (newValue) {
          startAutoRefresh();
        } else {
          stopAutoRefresh();
        }
      },
    );

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
      testing,
      testingIndexers,
      overallStatusColor,
      testAllIndexers,
      testIndexer,
      formatIndexerName,
      getStatusColor,
      getStatusBadgeClass,
    };
  },
};
</script>

<style scoped>
.torrent-indexer-health {
  /* Component-specific styles */
}
</style>
