<template>
  <div
    class="search-status-bar bg-white dark:bg-dark-800 border-b border-gray-200 dark:border-dark-600 px-4 py-3"
  >
    <div
      class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
    >
      <!-- Search Results Info -->
      <div class="flex items-center gap-4">
        <!-- Results Count -->
        <div class="text-sm text-gray-600 dark:text-gray-400">
          <span v-if="searchStore.loading" class="flex items-center gap-2">
            <svg
              class="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
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
            Searching...
          </span>
          <span v-else-if="searchStore.results.length > 0">
            {{ searchStore.results.length }} of
            {{ searchStore.pagination.total }} results
            <span v-if="searchStore.pagination.page > 1">
              (page {{ searchStore.pagination.page }})
            </span>
          </span>
          <span v-else-if="searchStore.query && !searchStore.loading">
            No results found
          </span>
        </div>

        <!-- Performance Info -->
        <div
          v-if="searchStore.performance.response_time_ms"
          class="text-xs text-gray-500 dark:text-gray-500"
        >
          {{ searchStore.performance.response_time_ms }}ms
          <span v-if="searchStore.performance.cached" class="text-green-600"
            >(cached)</span
          >
          <span v-if="searchStore.performance.fallback" class="text-yellow-600"
            >(fallback)</span
          >
        </div>
      </div>

      <!-- Source Information and Controls -->
      <div class="flex items-center gap-4">
        <!-- Source Indicators -->
        <div
          v-if="searchStore.sources.length > 0"
          class="flex items-center gap-2"
        >
          <span class="text-xs text-gray-500 dark:text-gray-500">Sources:</span>
          <div class="flex gap-1">
            <div
              v-for="source in searchStore.sources"
              :key="source.name"
              class="flex items-center gap-1 px-2 py-1 rounded-full text-xs"
              :class="getSourceStatusClass(source)"
              :title="`${source.name} (${source.tier}): ${source.count} results`"
            >
              <div
                class="w-2 h-2 rounded-full"
                :class="getSourceTierColor(source.tier)"
              ></div>
              {{ formatSourceName(source.name) }}
              <span class="text-xs opacity-75">({{ source.count }})</span>
            </div>
          </div>
        </div>

        <!-- Enhanced Search Toggle -->
        <div class="flex items-center gap-2">
          <label class="text-xs text-gray-600 dark:text-gray-400"
            >Enhanced:</label
          >
          <button
            @click="toggleEnhancedSearch"
            class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            :class="
              searchStore.useEnhancedSearch
                ? 'bg-primary-600'
                : 'bg-gray-200 dark:bg-gray-700'
            "
          >
            <span
              class="inline-block h-3 w-3 transform rounded-full bg-white transition-transform"
              :class="
                searchStore.useEnhancedSearch
                  ? 'translate-x-5'
                  : 'translate-x-1'
              "
            ></span>
          </button>
        </div>

        <!-- Indexer Health Indicator -->
        <div class="flex items-center gap-2">
          <button
            @click="toggleHealthDetails"
            class="flex items-center gap-1 text-xs px-2 py-1 rounded"
            :class="getHealthStatusClass()"
            :title="getHealthTooltip()"
          >
            <div
              class="w-2 h-2 rounded-full"
              :class="getHealthIndicatorColor()"
            ></div>
            <span>{{ getHealthStatusText() }}</span>
            <svg
              class="w-3 h-3 transition-transform"
              :class="{ 'rotate-180': showHealthDetails }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Health Details Panel -->
    <div
      v-if="showHealthDetails"
      class="mt-3 pt-3 border-t border-gray-200 dark:border-dark-600"
    >
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div
          v-for="(indexer, name) in indexerDetails"
          :key="name"
          class="flex items-center justify-between p-2 rounded bg-gray-50 dark:bg-dark-700"
        >
          <div class="flex items-center gap-2">
            <div
              class="w-3 h-3 rounded-full"
              :class="
                indexer.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
              "
            ></div>
            <span class="text-sm font-medium">{{
              formatSourceName(name)
            }}</span>
            <span class="text-xs text-gray-500">({{ indexer.tier }})</span>
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            {{ indexer.message }}
          </div>
        </div>
      </div>

      <!-- Refresh Health Button -->
      <div class="mt-2 flex justify-end">
        <button
          @click="refreshHealth"
          :disabled="refreshingHealth"
          class="text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 disabled:opacity-50"
        >
          <span v-if="refreshingHealth" class="flex items-center gap-1">
            <svg
              class="animate-spin h-3 w-3"
              xmlns="http://www.w3.org/2000/svg"
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
            Refreshing...
          </span>
          <span v-else>Refresh Health</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { useSearchStore } from "../stores/search.js";

export default {
  name: "SearchStatusBar",

  data() {
    return {
      showHealthDetails: false,
      refreshingHealth: false,
    };
  },

  setup() {
    const searchStore = useSearchStore();
    return { searchStore };
  },

  computed: {
    indexerDetails() {
      return this.searchStore.indexerHealth?.indexers || {};
    },
  },

  mounted() {
    // Check indexer health on component mount
    this.searchStore.checkIndexerHealth();
  },

  methods: {
    toggleEnhancedSearch() {
      this.searchStore.setEnhancedSearch(!this.searchStore.useEnhancedSearch);
      // Re-search with new mode if there's a query
      if (this.searchStore.query) {
        this.searchStore.search();
      }
    },

    toggleHealthDetails() {
      this.showHealthDetails = !this.showHealthDetails;
    },

    async refreshHealth() {
      this.refreshingHealth = true;
      try {
        await this.searchStore.checkIndexerHealth();
      } finally {
        this.refreshingHealth = false;
      }
    },

    formatSourceName(name) {
      const nameMap = {
        mangaupdates: "MangaUpdates",
        madaradex: "MadaraDex",
        mangadex: "MangaDx",
      };
      return nameMap[name.toLowerCase()] || name;
    },

    getSourceTierColor(tier) {
      const colorMap = {
        primary: "bg-green-400",
        secondary: "bg-yellow-400",
        tertiary: "bg-blue-400",
        unknown: "bg-gray-400",
      };
      return colorMap[tier] || "bg-gray-400";
    },

    getSourceStatusClass(source) {
      return "bg-gray-100 dark:bg-dark-600 text-gray-700 dark:text-gray-300";
    },

    getHealthStatusClass() {
      const status = this.searchStore.indexerHealth?.status || "unknown";
      const baseClass = "hover:bg-opacity-80 transition-colors";

      switch (status) {
        case "healthy":
          return `bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 ${baseClass}`;
        case "degraded":
          return `bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 ${baseClass}`;
        case "unhealthy":
          return `bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 ${baseClass}`;
        default:
          return `bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 ${baseClass}`;
      }
    },

    getHealthIndicatorColor() {
      const status = this.searchStore.indexerHealth?.status || "unknown";
      switch (status) {
        case "healthy":
          return "bg-green-400";
        case "degraded":
          return "bg-yellow-400";
        case "unhealthy":
          return "bg-red-400";
        default:
          return "bg-gray-400";
      }
    },

    getHealthStatusText() {
      const status = this.searchStore.indexerHealth?.status || "unknown";
      const summary = this.searchStore.indexerHealth?.summary;

      if (summary) {
        return `${summary.healthy_count}/${summary.total_count}`;
      }

      return status.charAt(0).toUpperCase() + status.slice(1);
    },

    getHealthTooltip() {
      const health = this.searchStore.indexerHealth;
      if (!health) return "Health status unknown";

      const summary = health.summary;
      if (summary) {
        return `Indexer Health: ${summary.healthy_count}/${summary.total_count} healthy (${summary.health_percentage}%)`;
      }

      return `Indexer Health: ${health.status}`;
    },
  },
};
</script>

<style scoped>
.rotate-180 {
  transform: rotate(180deg);
}
</style>
