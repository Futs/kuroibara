<template>
  <div class="providers">
    <div class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">
      <div class="px-4 py-5 sm:px-6">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Providers
        </h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Manage your manga providers and their configurations
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="px-4 py-5 sm:p-6">
        <div class="flex justify-center">
          <svg
            class="animate-spin h-8 w-8 text-primary-600"
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
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="px-4 py-5 sm:p-6">
        <div class="rounded-md bg-red-50 dark:bg-red-900 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg
                class="h-5 w-5 text-red-400 dark:text-red-300"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
                {{ error }}
              </h3>
              <div class="mt-2 text-sm text-red-700 dark:text-red-300">
                <button
                  @click="fetchProviders"
                  class="font-medium underline hover:text-red-600 dark:hover:text-red-400"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="providers.length === 0" class="px-4 py-5 sm:p-6">
        <div class="text-center">
          <svg
            class="mx-auto h-12 w-12 text-gray-400"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            No providers available
          </h3>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Provider management functionality will be available in future updates.
          </p>
        </div>
      </div>

      <!-- Providers List -->
      <div v-else class="px-4 py-5 sm:p-6">
        <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="provider in providers"
            :key="provider.id"
            class="col-span-1 bg-white dark:bg-dark-700 rounded-lg shadow divide-y divide-gray-200 dark:divide-dark-600"
          >
            <div class="w-full flex items-center justify-between p-6 space-x-6">
              <div class="flex-1 truncate">
                <div class="flex items-center space-x-3">
                  <h3 class="text-gray-900 dark:text-white text-sm font-medium truncate">
                    {{ provider.name }}
                  </h3>
                  <span
                    v-if="provider.enabled"
                    class="flex-shrink-0 inline-block px-2 py-0.5 text-green-800 dark:text-green-200 text-xs font-medium bg-green-100 dark:bg-green-900 rounded-full"
                  >
                    Enabled
                  </span>
                  <span
                    v-else
                    class="flex-shrink-0 inline-block px-2 py-0.5 text-red-800 dark:text-red-200 text-xs font-medium bg-red-100 dark:bg-red-900 rounded-full"
                  >
                    Disabled
                  </span>
                </div>
                <p class="mt-1 text-gray-500 dark:text-gray-400 text-sm truncate">
                  {{ provider.description || 'No description available' }}
                </p>
              </div>
            </div>
            <div>
              <div class="-mt-px flex divide-x divide-gray-200 dark:divide-dark-600">
                <div class="w-0 flex-1 flex">
                  <button
                    @click="toggleProvider(provider)"
                    class="relative -mr-px w-0 flex-1 inline-flex items-center justify-center py-4 text-sm text-gray-700 dark:text-gray-300 font-medium border border-transparent rounded-bl-lg hover:text-gray-500 dark:hover:text-gray-400"
                  >
                    <svg
                      v-if="provider.enabled"
                      class="w-5 h-5 text-red-400"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <svg
                      v-else
                      class="w-5 h-5 text-green-400"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <span class="ml-3">{{ provider.enabled ? 'Disable' : 'Enable' }}</span>
                  </button>
                </div>
                <div class="-ml-px w-0 flex-1 flex">
                  <button
                    @click="configureProvider(provider)"
                    class="relative w-0 flex-1 inline-flex items-center justify-center py-4 text-sm text-gray-700 dark:text-gray-300 font-medium border border-transparent rounded-br-lg hover:text-gray-500 dark:hover:text-gray-400"
                  >
                    <svg
                      class="w-5 h-5 text-gray-400"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                      />
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                    <span class="ml-3">Configure</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/services/api.js";

const providers = ref([]);
const loading = ref(true);
const error = ref(null);

const fetchProviders = async () => {
  loading.value = true;
  error.value = null;

  try {
    console.log("Fetching providers...");
    const response = await api.get("/v1/providers");
    console.log("Providers response:", response);
    providers.value = response.data;
    console.log("Providers loaded:", providers.value.length);
  } catch (err) {
    console.error("Error fetching providers:", err);
    console.error("Error response:", err.response);
    console.error("Error status:", err.response?.status);
    console.error("Error data:", err.response?.data);
    
    if (err.response?.status === 401) {
      error.value = "Authentication required. Please log in again.";
    } else if (err.response?.status === 403) {
      error.value = "Access denied. You don't have permission to view providers.";
    } else {
      error.value = err.response?.data?.detail || "Failed to load providers";
    }
  } finally {
    loading.value = false;
  }
};

const toggleProvider = (provider) => {
  console.log("Toggle provider:", provider.name);
  // TODO: Implement provider toggle functionality
};

const configureProvider = (provider) => {
  console.log("Configure provider:", provider.name);
  // TODO: Implement provider configuration functionality
};

onMounted(() => {
  fetchProviders();
});
</script>
