<template>
  <div class="provider-preferences">
    <div class="mb-6">
      <h3
        class="text-lg font-medium leading-6 text-gray-900 dark:text-white mb-2"
      >
        Provider Preferences
      </h3>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Manage your preferred manga providers. Favorite providers will be
        searched first and can be reordered by priority.
      </p>

      <!-- Search Field -->
      <div class="mt-4">
        <div class="relative">
          <div
            class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
          >
            <svg
              class="h-5 w-5 text-gray-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <input
            v-model="searchQuery"
            type="text"
            class="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md leading-5 bg-white dark:bg-dark-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            placeholder="Search providers..."
          />
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-8">
      <div
        class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"
      ></div>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 mb-4"
    >
      <div class="flex">
        <div class="flex-shrink-0">
          <svg
            class="h-5 w-5 text-red-400"
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
            Error loading provider preferences
          </h3>
          <div class="mt-2 text-sm text-red-700 dark:text-red-300">
            {{ error }}
          </div>
        </div>
      </div>
    </div>

    <!-- Provider List -->
    <div v-else class="space-y-4">
      <!-- Favorite Providers Section -->
      <div v-if="favoriteProviders.length > 0">
        <h4
          class="text-md font-medium text-gray-900 dark:text-white mb-3 flex items-center"
        >
          <svg
            class="h-5 w-5 text-yellow-500 mr-2"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
            />
          </svg>
          Favorite Providers ({{ favoriteProviders.length }})
        </h4>
        <!-- Scrollable container for favorite providers (max 10 items visible) -->
        <div
          class="overflow-y-auto border border-gray-200 dark:border-dark-600 rounded-lg p-3 bg-gray-50 dark:bg-dark-800 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent"
          style="max-height: 800px"
        >
          <draggable
            v-model="favoriteProviders"
            group="providers"
            @change="onFavoritesReorder"
            item-key="id"
            class="space-y-2"
          >
            <template #item="{ element: provider }">
              <ProviderCard
                :provider="provider"
                :is-favorite="true"
                @toggle-favorite="toggleFavorite"
                @toggle-enabled="toggleEnabled"
                :draggable="true"
              />
            </template>
          </draggable>
        </div>
      </div>

      <!-- Regular Providers Section -->
      <div>
        <h4 class="text-md font-medium text-gray-900 dark:text-white mb-3">
          Available Providers ({{ regularProviders.length }})
        </h4>
        <!-- Scrollable container for available providers (max 5 items visible) -->
        <div
          class="overflow-y-auto border border-gray-200 dark:border-dark-600 rounded-lg p-3 bg-gray-50 dark:bg-dark-800 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent"
          style="max-height: 400px"
        >
          <div class="space-y-2">
            <ProviderCard
              v-for="provider in regularProviders"
              :key="provider.id"
              :provider="provider"
              :is-favorite="false"
              @toggle-favorite="toggleFavorite"
              @toggle-enabled="toggleEnabled"
            />
          </div>
        </div>
      </div>

      <!-- Save Button -->
      <div class="pt-4 border-t border-gray-200 dark:border-dark-600">
        <button
          @click="savePreferences"
          :disabled="saving || !hasChanges"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg
            v-if="saving"
            class="animate-spin -ml-1 mr-3 h-4 w-4 text-white"
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
          {{ saving ? "Saving..." : "Save Preferences" }}
        </button>
        <p
          v-if="hasChanges"
          class="mt-2 text-sm text-gray-500 dark:text-gray-400"
        >
          You have unsaved changes
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import draggable from "vuedraggable";
import ProviderCard from "./ProviderCard.vue";
import api from "../services/api";

// State
const loading = ref(true);
const saving = ref(false);
const error = ref(null);
const providers = ref([]);
const originalProviders = ref([]);
const hasChanges = ref(false);
const searchQuery = ref("");

// Computed
const favoriteProviders = computed(() =>
  providers.value
    .filter((p) => p.is_favorite)
    .filter(
      (p) =>
        searchQuery.value === "" ||
        p.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
    )
    .sort((a, b) => (a.priority_order || 999) - (b.priority_order || 999)),
);

const regularProviders = computed(() =>
  providers.value
    .filter((p) => !p.is_favorite)
    .filter(
      (p) =>
        searchQuery.value === "" ||
        p.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
    )
    .sort((a, b) => a.name.localeCompare(b.name)),
);

// Methods
const fetchProviderPreferences = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await api.get("/v1/users/me/provider-preferences/");
    providers.value = response.data.providers;
    originalProviders.value = JSON.parse(
      JSON.stringify(response.data.providers),
    );
    hasChanges.value = false;
  } catch (err) {
    if (err.response?.status === 401 || err.response?.status === 403) {
      error.value = "Please log in to manage provider preferences";
    } else {
      error.value =
        err.response?.data?.detail || "Failed to load provider preferences";
    }
    console.error("Error fetching provider preferences:", err);
  } finally {
    loading.value = false;
  }
};

const toggleFavorite = (providerId) => {
  const provider = providers.value.find((p) => p.id === providerId);
  if (provider) {
    provider.is_favorite = !provider.is_favorite;

    if (provider.is_favorite) {
      // Set priority order for new favorite
      const maxPriority = Math.max(
        ...providers.value
          .filter((p) => p.is_favorite && p.id !== providerId)
          .map((p) => p.priority_order || 0),
        0,
      );
      provider.priority_order = maxPriority + 1;
    } else {
      // Remove priority order when unfavoriting
      provider.priority_order = null;
    }

    checkForChanges();
  }
};

const toggleEnabled = (providerId) => {
  const provider = providers.value.find((p) => p.id === providerId);
  if (provider) {
    provider.user_enabled = !provider.user_enabled;
    checkForChanges();
  }
};

const onFavoritesReorder = () => {
  // Update priority order based on new position
  favoriteProviders.value.forEach((provider, index) => {
    provider.priority_order = index + 1;
  });
  checkForChanges();
};

const checkForChanges = () => {
  hasChanges.value =
    JSON.stringify(providers.value) !== JSON.stringify(originalProviders.value);
};

const savePreferences = async () => {
  saving.value = true;
  error.value = null;

  try {
    const preferences = providers.value.map((provider) => ({
      provider_id: provider.id,
      is_favorite: provider.is_favorite,
      priority_order: provider.priority_order,
      is_enabled: provider.user_enabled,
    }));

    await api.post("/v1/users/me/provider-preferences/bulk", {
      preferences,
    });

    originalProviders.value = JSON.parse(JSON.stringify(providers.value));
    hasChanges.value = false;

    // Show success message (you might want to use a toast notification here)
    console.log("Provider preferences saved successfully");
  } catch (err) {
    error.value =
      err.response?.data?.detail || "Failed to save provider preferences";
    console.error("Error saving provider preferences:", err);
  } finally {
    saving.value = false;
  }
};

// Lifecycle
onMounted(() => {
  // Only fetch if we're in an authenticated context (Settings page)
  fetchProviderPreferences();
});
</script>

<style scoped>
.provider-preferences {
  /* Add any custom styles here */
}

/* Custom scrollbar styles */
.scrollbar-thin {
  scrollbar-width: thin;
}

.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: rgba(156, 163, 175, 0.8);
}

/* Dark mode scrollbar */
.dark .scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: rgba(75, 85, 99, 0.5);
}

.dark .scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: rgba(75, 85, 99, 0.8);
}
</style>
