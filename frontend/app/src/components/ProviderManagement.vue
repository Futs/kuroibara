<template>
  <div
    class="provider-management bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6"
  >
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
        Provider Management
      </h2>
      <div class="flex items-center space-x-4">
        <button
          @click="showCreateProvider = true"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
        >
          Create Provider
        </button>
        <button
          @click="showImportExport = true"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Import/Export
        </button>
        <button
          @click="refreshProviders"
          :disabled="loading"
          class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 transition-colors"
        >
          {{ loading ? "Loading..." : "Refresh" }}
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 dark:border-dark-600 mb-6">
      <nav class="-mb-px flex space-x-8">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'py-2 px-1 border-b-2 font-medium text-sm',
            activeTab === tab.id
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300',
          ]"
        >
          {{ tab.name }}
          <span
            v-if="tab.count !== undefined"
            class="ml-2 bg-gray-100 dark:bg-dark-600 text-gray-600 dark:text-gray-300 py-0.5 px-2 rounded-full text-xs"
          >
            {{ tab.count }}
          </span>
        </button>
      </nav>
    </div>

    <!-- Provider List Tab -->
    <div v-if="activeTab === 'providers'" class="space-y-6">
      <!-- Filters and Controls -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search providers..."
            class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
          />
          <select
            v-model="statusFilter"
            class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
          >
            <option value="all">All Status</option>
            <option value="enabled">Enabled</option>
            <option value="disabled">Disabled</option>
            <option value="healthy">Healthy</option>
            <option value="unhealthy">Unhealthy</option>
          </select>
          <select
            v-model="typeFilter"
            class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
          >
            <option value="all">All Types</option>
            <option value="official">Official</option>
            <option value="community">Community</option>
            <option value="custom">Custom</option>
          </select>
        </div>

        <div class="flex items-center space-x-2">
          <button
            @click="toggleBulkMode"
            class="px-3 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
          >
            {{ bulkMode ? "Exit Bulk" : "Bulk Actions" }}
          </button>
          <div
            v-if="bulkMode && selectedProviders.size > 0"
            class="flex items-center space-x-2"
          >
            <button
              @click="bulkEnable"
              class="px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            >
              Enable ({{ selectedProviders.size }})
            </button>
            <button
              @click="bulkDisable"
              class="px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Disable ({{ selectedProviders.size }})
            </button>
          </div>
        </div>
      </div>

      <!-- Provider Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="provider in filteredProviders"
          :key="provider.id"
          class="border border-gray-200 dark:border-dark-600 rounded-lg p-4 hover:shadow-md transition-shadow"
          :class="{
            'ring-2 ring-blue-500':
              bulkMode && selectedProviders.has(provider.id),
          }"
        >
          <!-- Provider Header -->
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-3">
              <input
                v-if="bulkMode"
                type="checkbox"
                :checked="selectedProviders.has(provider.id)"
                @change="toggleProviderSelection(provider.id)"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div class="flex items-center space-x-2">
                <div
                  class="w-3 h-3 rounded-full"
                  :class="getProviderStatusColor(provider)"
                ></div>
                <span class="font-medium text-gray-900 dark:text-white">{{
                  provider.name
                }}</span>
                <span
                  class="px-2 py-1 text-xs rounded-full"
                  :class="getProviderTypeClass(provider.type)"
                >
                  {{ provider.type }}
                </span>
              </div>
            </div>

            <div class="flex items-center space-x-1">
              <button
                @click="toggleProvider(provider)"
                class="p-1 rounded hover:bg-gray-100 dark:hover:bg-dark-600"
                :title="provider.is_enabled ? 'Disable' : 'Enable'"
              >
                <svg
                  class="w-4 h-4"
                  :class="
                    provider.is_enabled ? 'text-green-600' : 'text-gray-400'
                  "
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clip-rule="evenodd"
                  />
                </svg>
              </button>
              <button
                @click="showProviderSettings(provider)"
                class="p-1 rounded hover:bg-gray-100 dark:hover:bg-dark-600"
                title="Settings"
              >
                <svg
                  class="w-4 h-4 text-gray-600 dark:text-gray-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                    clip-rule="evenodd"
                  />
                </svg>
              </button>
              <button
                @click="showProviderMenu(provider)"
                class="p-1 rounded hover:bg-gray-100 dark:hover:bg-dark-600"
                title="More options"
              >
                <svg
                  class="w-4 h-4 text-gray-600 dark:text-gray-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"
                  />
                </svg>
              </button>
            </div>
          </div>

          <!-- Provider Info -->
          <div class="space-y-2 text-sm">
            <div class="text-gray-600 dark:text-gray-400">
              {{ provider.description || "No description available" }}
            </div>

            <div class="flex items-center justify-between">
              <span class="text-gray-500 dark:text-gray-400">Language:</span>
              <span class="font-medium">{{
                provider.language || "Unknown"
              }}</span>
            </div>

            <div class="flex items-center justify-between">
              <span class="text-gray-500 dark:text-gray-400">Priority:</span>
              <span class="font-medium">{{ provider.priority || 0 }}</span>
            </div>

            <div class="flex items-center justify-between">
              <span class="text-gray-500 dark:text-gray-400"
                >Response Time:</span
              >
              <span
                class="font-medium"
                :class="getResponseTimeColor(provider.response_time)"
              >
                {{ formatResponseTime(provider.response_time) }}
              </span>
            </div>

            <div class="flex items-center justify-between">
              <span class="text-gray-500 dark:text-gray-400"
                >Success Rate:</span
              >
              <span
                class="font-medium"
                :class="getSuccessRateColor(provider.success_rate)"
              >
                {{ provider.success_rate || 0 }}%
              </span>
            </div>
          </div>

          <!-- Provider Actions -->
          <div class="mt-4 flex items-center space-x-2">
            <button
              @click="testProvider(provider)"
              :disabled="testingProviders.has(provider.id)"
              class="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {{ testingProviders.has(provider.id) ? "Testing..." : "Test" }}
            </button>
            <button
              @click="viewProviderAnalytics(provider)"
              class="flex-1 px-3 py-2 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
            >
              Analytics
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Health Monitor Tab -->
    <div v-if="activeTab === 'health'">
      <ProviderHealthMonitor />
    </div>

    <!-- Analytics Tab -->
    <div v-if="activeTab === 'analytics'">
      <ProviderAnalytics />
    </div>

    <!-- Settings Tab -->
    <div v-if="activeTab === 'settings'" class="space-y-6">
      <!-- Global Settings -->
      <div class="bg-gray-50 dark:bg-dark-700 p-6 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Global Settings
        </h3>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              Default Timeout (seconds)
            </label>
            <input
              v-model.number="globalSettings.defaultTimeout"
              type="number"
              min="5"
              max="120"
              class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
            />
          </div>

          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              Max Retries
            </label>
            <input
              v-model.number="globalSettings.maxRetries"
              type="number"
              min="0"
              max="10"
              class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
            />
          </div>

          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              Health Check Interval (minutes)
            </label>
            <input
              v-model.number="globalSettings.healthCheckInterval"
              type="number"
              min="1"
              max="60"
              class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
            />
          </div>

          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              Rate Limit (requests/minute)
            </label>
            <input
              v-model.number="globalSettings.defaultRateLimit"
              type="number"
              min="1"
              max="1000"
              class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
            />
          </div>
        </div>

        <div class="mt-6 space-y-4">
          <div class="flex items-center">
            <input
              v-model="globalSettings.enableAutoFailover"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label class="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Enable automatic failover
            </label>
          </div>

          <div class="flex items-center">
            <input
              v-model="globalSettings.enableAnalytics"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label class="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Enable analytics collection
            </label>
          </div>

          <div class="flex items-center">
            <input
              v-model="globalSettings.enableRateLimiting"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label class="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Enable rate limiting
            </label>
          </div>
        </div>

        <div class="mt-6">
          <button
            @click="saveGlobalSettings"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>

    <!-- Create Provider Modal -->
    <div
      v-if="showCreateProvider"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showCreateProvider = false"
    >
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
      >
        <div
          class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
        ></div>

        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full"
        >
          <CustomProviderBuilder @close="showCreateProvider = false" />
        </div>
      </div>
    </div>

    <!-- Import/Export Modal -->
    <div
      v-if="showImportExport"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showImportExport = false"
    >
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
      >
        <div
          class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
        ></div>

        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6"
        >
          <div>
            <h3
              class="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4"
            >
              Import/Export Providers
            </h3>

            <div class="space-y-4">
              <div>
                <button
                  @click="exportProviders"
                  class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Export Provider Settings
                </button>
              </div>

              <div>
                <label
                  class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Import Provider Settings
                </label>
                <input
                  ref="importFile"
                  type="file"
                  accept=".json"
                  @change="importProviders"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                />
              </div>
            </div>
          </div>

          <div class="mt-5 sm:mt-6">
            <button
              @click="showImportExport = false"
              class="w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-700 text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useProvidersStore } from "../stores/providers";
import ProviderHealthMonitor from "./ProviderHealthMonitor.vue";
import ProviderAnalytics from "./ProviderAnalytics.vue";
import CustomProviderBuilder from "./CustomProviderBuilder.vue";

const providersStore = useProvidersStore();

// Local state
const loading = ref(false);
const activeTab = ref("providers");
const searchQuery = ref("");
const statusFilter = ref("all");
const typeFilter = ref("all");
const bulkMode = ref(false);
const selectedProviders = ref(new Set());
const testingProviders = ref(new Set());
const showCreateProvider = ref(false);
const showImportExport = ref(false);
const importFile = ref(null);

// Global settings
const globalSettings = ref({
  defaultTimeout: 30,
  maxRetries: 3,
  healthCheckInterval: 5,
  defaultRateLimit: 60,
  enableAutoFailover: true,
  enableAnalytics: true,
  enableRateLimiting: true,
});

// Tabs configuration
const tabs = computed(() => [
  {
    id: "providers",
    name: "Providers",
    count: providersStore.getProviders.length,
  },
  { id: "health", name: "Health Monitor" },
  { id: "analytics", name: "Analytics" },
  { id: "settings", name: "Settings" },
]);

// Computed properties
const filteredProviders = computed(() => {
  let providers = [...providersStore.getProviders];

  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    providers = providers.filter(
      (p) =>
        p.name.toLowerCase().includes(query) ||
        p.description?.toLowerCase().includes(query),
    );
  }

  // Apply status filter
  switch (statusFilter.value) {
    case "enabled":
      providers = providers.filter((p) => p.is_enabled);
      break;
    case "disabled":
      providers = providers.filter((p) => !p.is_enabled);
      break;
    case "healthy":
      providers = providers.filter((p) => p.is_healthy);
      break;
    case "unhealthy":
      providers = providers.filter((p) => !p.is_healthy);
      break;
  }

  // Apply type filter
  if (typeFilter.value !== "all") {
    providers = providers.filter((p) => p.type === typeFilter.value);
  }

  return providers;
});

// Methods
const getProviderStatusColor = (provider) => {
  if (!provider.is_enabled) return "bg-gray-500";
  if (!provider.is_healthy) return "bg-red-500";
  return "bg-green-500";
};

const getProviderTypeClass = (type) => {
  switch (type) {
    case "official":
      return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
    case "community":
      return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
    case "custom":
      return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200";
    default:
      return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
  }
};

const getResponseTimeColor = (time) => {
  if (!time) return "text-gray-500";
  if (time <= 500) return "text-green-600 dark:text-green-400";
  if (time <= 1000) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
};

const getSuccessRateColor = (rate) => {
  if (!rate) return "text-gray-500";
  if (rate >= 95) return "text-green-600 dark:text-green-400";
  if (rate >= 90) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-600 dark:text-red-400";
};

const formatResponseTime = (time) => {
  if (!time) return "N/A";
  return `${time}ms`;
};

const toggleBulkMode = () => {
  bulkMode.value = !bulkMode.value;
  if (!bulkMode.value) {
    selectedProviders.value.clear();
  }
};

const toggleProviderSelection = (providerId) => {
  if (selectedProviders.value.has(providerId)) {
    selectedProviders.value.delete(providerId);
  } else {
    selectedProviders.value.add(providerId);
  }
};

const toggleProvider = async (provider) => {
  try {
    await providersStore.updateProviderStatus(
      provider.id,
      !provider.is_enabled,
    );
  } catch (error) {
    console.error("Error toggling provider:", error);
  }
};

const testProvider = async (provider) => {
  testingProviders.value.add(provider.id);

  try {
    await providersStore.checkProviderHealth(provider.id);
  } catch (error) {
    console.error("Error testing provider:", error);
  } finally {
    testingProviders.value.delete(provider.id);
  }
};

const bulkEnable = async () => {
  const providerIds = Array.from(selectedProviders.value);
  await providersStore.enableProviders(providerIds);
  selectedProviders.value.clear();
};

const bulkDisable = async () => {
  const providerIds = Array.from(selectedProviders.value);
  await providersStore.disableProviders(providerIds);
  selectedProviders.value.clear();
};

const refreshProviders = async () => {
  loading.value = true;
  try {
    await providersStore.fetchProviders();
  } finally {
    loading.value = false;
  }
};

const saveGlobalSettings = async () => {
  try {
    // Save to store or API
    console.log("Saving global settings:", globalSettings.value);
  } catch (error) {
    console.error("Error saving settings:", error);
  }
};

const exportProviders = () => {
  const data = providersStore.exportProviderSettings();
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `provider-settings-${new Date().toISOString().split("T")[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
};

const importProviders = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const text = await file.text();
    const data = JSON.parse(text);
    await providersStore.importProviderSettings(data);
    showImportExport.value = false;
  } catch (error) {
    console.error("Error importing providers:", error);
  }
};

const showProviderSettings = (provider) => {
  console.log("Show settings for provider:", provider);
};

const showProviderMenu = (provider) => {
  console.log("Show menu for provider:", provider);
};

const viewProviderAnalytics = (provider) => {
  console.log("View analytics for provider:", provider);
};

// Lifecycle
onMounted(async () => {
  await refreshProviders();
});
</script>

<style scoped>
.provider-management {
  max-height: 90vh;
  overflow-y: auto;
}
</style>
