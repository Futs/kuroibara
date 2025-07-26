<template>
  <div class="providers">
    <!-- Header -->
    <div
      class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden mb-6"
    >
      <div class="px-4 py-5 sm:px-6">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Provider Explorer
        </h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Browse and explore manga from different providers
        </p>
      </div>
    </div>

    <!-- Provider Selection -->
    <div
      class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden mb-6"
    >
      <div class="px-4 py-5 sm:px-6">
        <h2 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Select a Provider
        </h2>

        <!-- Loading State -->
        <div
          v-if="providersStore.isLoading && !providersStore.getProviders.length"
          class="flex justify-center py-8"
        >
          <div
            class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"
          ></div>
        </div>

        <!-- Error State -->
        <div
          v-else-if="providersStore.getError"
          class="rounded-md bg-red-50 dark:bg-red-900 p-4"
        >
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
                {{ providersStore.getError }}
              </h3>
              <div class="mt-2 text-sm text-red-700 dark:text-red-300">
                <button
                  @click="providersStore.fetchProviders"
                  class="font-medium underline hover:text-red-600 dark:hover:text-red-400"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Provider Grid -->
        <div v-else-if="providersStore.getProviders.length" class="relative">
          <!-- Header with provider count -->
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              Available Providers ({{ providersStore.getProviders.length }})
            </h3>
            <div class="text-sm text-gray-500 dark:text-gray-400">
              Scroll to see more providers
            </div>
          </div>

          <!-- Fixed height container with scroll -->
          <div
            class="h-96 overflow-y-auto border border-gray-200 dark:border-dark-600 rounded-lg bg-gray-50 dark:bg-dark-800 p-4 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent"
          >
            <div class="grid grid-cols-4 gap-4 auto-rows-fr min-h-full">
              <button
                v-for="provider in providersStore.getProviders"
                :key="provider.id"
                @click="selectProvider(provider.id)"
                :class="[
                  'relative rounded-lg border-2 p-3 text-left transition-all duration-200 h-full flex flex-col',
                  selectedProviderId === provider.id
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900'
                    : 'border-gray-200 dark:border-dark-600 hover:border-gray-300 dark:hover:border-dark-500 bg-white dark:bg-dark-700',
                ]"
              >
                <!-- Provider Icon and Title -->
                <div class="flex items-center space-x-2 mb-2">
                  <div class="flex-shrink-0">
                    <div
                      class="h-8 w-8 rounded-lg bg-primary-100 dark:bg-primary-900 flex items-center justify-center"
                    >
                      <svg
                        class="h-4 w-4 text-primary-600 dark:text-primary-400"
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
                    </div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p
                      class="text-sm font-medium text-gray-900 dark:text-white truncate"
                    >
                      {{ provider.name }}
                    </p>
                  </div>
                </div>

                <!-- Provider URL -->
                <div class="mb-2 flex-1">
                  <p class="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {{ provider.url }}
                  </p>
                </div>

                <!-- Status Badges -->
                <div class="flex flex-col space-y-1 mt-auto">
                  <!-- Cloudflare Indicator -->
                  <span
                    v-if="provider.requires_flaresolverr"
                    class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300"
                    title="This provider requires Cloudflare protection bypass"
                  >
                    <svg
                      class="w-3 h-3 mr-1"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                        clip-rule="evenodd"
                      />
                    </svg>
                    Cloudflare
                  </span>

                  <!-- Health Status -->
                  <span
                    :class="[
                      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                      provider.is_healthy
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
                    ]"
                  >
                    {{ provider.is_healthy ? "Healthy" : "Unhealthy" }}
                  </span>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-8">
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
            No manga providers are currently configured.
          </p>
        </div>
      </div>
    </div>

    <!-- Provider Summary Card -->
    <div v-if="providersStore.getSelectedProvider" class="mb-6">
      <ProviderSummaryCard
        :provider="providersStore.getSelectedProvider"
        @test-provider="testProvider"
      />
    </div>

    <!-- Provider Manga List -->
    <div
      v-if="providersStore.getSelectedProvider"
      class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden"
    >
      <div
        class="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-dark-600"
      >
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-medium text-gray-900 dark:text-white">
              Available Manga from {{ providersStore.getSelectedProvider.name }}
            </h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Browse and add manga to your library
            </p>
          </div>
          <button @click="clearProvider" class="btn btn-secondary btn-sm">
            Clear Selection
          </button>
        </div>
      </div>

      <!-- Manga Filters -->
      <div class="px-4 py-4">
        <ProviderMangaFilters
          :filters="providersStore.getFilters"
          :available-genres="availableGenres"
          :available-years="availableYears"
          @update-filters="handleUpdateFilters"
          @clear-filters="handleClearFilters"
        />
      </div>

      <!-- Manga Loading State -->
      <div v-if="providersStore.isLoading" class="px-4 py-8 text-center">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"
        ></div>
        <p class="mt-4 text-gray-500 dark:text-gray-400">Loading manga...</p>
      </div>

      <!-- Manga Error State -->
      <div v-else-if="providersStore.getError" class="px-4 py-8">
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
                {{ providersStore.getError }}
              </h3>
            </div>
          </div>
        </div>
      </div>

      <!-- Manga List -->
      <div
        v-else-if="providersStore.getProviderManga.length"
        class="bg-white dark:bg-dark-800 border-t border-gray-200 dark:border-dark-600"
      >
        <div class="divide-y divide-gray-200 dark:divide-dark-600">
          <ProviderMangaCard
            v-for="manga in providersStore.getProviderManga"
            :key="manga.id"
            :manga="manga"
            :provider-id="providersStore.getSelectedProvider.id"
            @add-to-library="addToLibrary"
            @view-details="viewMangaDetails"
          />
        </div>

        <!-- Load More Button -->
        <div
          v-if="providersStore.getPagination.hasMore"
          class="mt-6 text-center"
        >
          <button
            @click="loadMoreManga"
            class="btn btn-secondary"
            :disabled="providersStore.isLoading"
          >
            <svg
              v-if="providersStore.isLoading"
              class="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
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
            {{ providersStore.isLoading ? "Loading..." : "Load More" }}
          </button>
        </div>
      </div>

      <!-- Empty Manga State -->
      <div v-else class="px-4 py-8 text-center">
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
            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
          />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
          No manga found
        </h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          This provider doesn't have any manga available at the moment.
        </p>
      </div>
    </div>

    <!-- Manga Details Modal -->
    <ProviderMangaDetailsModal
      :is-open="showMangaDetails"
      :manga-details="selectedMangaDetails"
      :loading="mangaDetailsLoading"
      :error="mangaDetailsError"
      @close="closeMangaDetails"
      @add-to-library="addToLibrary"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useProvidersStore } from "../stores/providers";
import { useLibraryStore } from "../stores/library";
import ProviderSummaryCard from "../components/ProviderSummaryCard.vue";
import ProviderMangaCard from "../components/ProviderMangaCard.vue";
import ProviderMangaDetailsModal from "../components/ProviderMangaDetailsModal.vue";
import ProviderMangaFilters from "../components/ProviderMangaFilters.vue";
import api from "../services/api";

const providersStore = useProvidersStore();
const libraryStore = useLibraryStore();

const selectedProviderId = ref(null);
const showMangaDetails = ref(false);
const selectedMangaDetails = ref(null);
const mangaDetailsLoading = ref(false);
const mangaDetailsError = ref(null);

// Computed property to extract unique genres from current manga list
const availableGenres = computed(() => {
  const genres = new Set();
  providersStore.getProviderManga.forEach((manga) => {
    if (
      manga.genres &&
      Array.isArray(manga.genres) &&
      manga.genres.length > 0
    ) {
      manga.genres.forEach((genre) => {
        if (genre && typeof genre === "string" && genre.trim()) {
          genres.add(genre.trim());
        }
      });
    }
  });
  return Array.from(genres).sort();
});

// Computed property to extract unique years from current manga list
const availableYears = computed(() => {
  const years = new Set();
  providersStore.getProviderManga.forEach((manga) => {
    if (manga.year && manga.year > 0) {
      years.add(manga.year);
    }
  });
  return Array.from(years).sort((a, b) => b - a); // Sort descending (newest first)
});

const selectProvider = async (providerId) => {
  selectedProviderId.value = providerId;
  await providersStore.selectProvider(providerId);
};

const clearProvider = () => {
  selectedProviderId.value = null;
  providersStore.clearSelectedProvider();
};

const loadMoreManga = async () => {
  await providersStore.loadMoreManga();
};

const testProvider = async () => {
  if (!providersStore.getSelectedProvider) return;

  try {
    await api.post(
      `/v1/providers/${providersStore.getSelectedProvider.id}/test`,
    );
    // Refresh provider data after test
    await providersStore.fetchProviders();
  } catch (error) {
    console.error("Error testing provider:", error);
  }
};

const handleUpdateFilters = async (filters) => {
  providersStore.updateFilters(filters);
  await providersStore.applyFilters();
};

const handleClearFilters = async () => {
  providersStore.clearFilters();
  await providersStore.applyFilters();
};

const addToLibrary = async (manga) => {
  try {
    console.log("Adding manga to library:", manga.title);

    // Use the from-external endpoint to create manga from provider data
    const response = await api.post(
      "/v1/manga/from-external",
      {},
      {
        params: {
          provider: providersStore.getSelectedProvider.id,
          external_id: manga.id,
        },
      }
    );

    const createdManga = response.data;
    console.log("Created manga record:", createdManga.id);

    // Add to library
    await libraryStore.addToLibrary(createdManga.id);

    console.log("Successfully added manga to library");
    alert(`Successfully added "${manga.title}" to your library!`);
  } catch (error) {
    console.error("Error adding manga to library:", error);
    const errorMessage = error.response?.data?.detail || error.message || "Unknown error";
    alert(`Failed to add "${manga.title}" to library: ${errorMessage}`);
  }
};

const viewMangaDetails = async (manga) => {
  showMangaDetails.value = true;
  mangaDetailsLoading.value = true;
  mangaDetailsError.value = null;

  try {
    if (!providersStore.getSelectedProvider) {
      throw new Error("No provider selected");
    }

    const details = await providersStore.fetchProviderMangaDetails(
      providersStore.getSelectedProvider.id,
      manga.id,
    );
    selectedMangaDetails.value = details;
  } catch (error) {
    mangaDetailsError.value = error.message || "Failed to load manga details";
  } finally {
    mangaDetailsLoading.value = false;
  }
};

const closeMangaDetails = () => {
  showMangaDetails.value = false;
  selectedMangaDetails.value = null;
  mangaDetailsError.value = null;
};

onMounted(async () => {
  try {
    await providersStore.fetchProviders();
  } catch (error) {
    console.error("Failed to load providers:", error);
    // The API interceptor will handle 401 redirects automatically
  }
});
</script>

<style scoped>
/* Custom scrollbar styling */
.scrollbar-thin {
  scrollbar-width: thin;
}

.scrollbar-thin::-webkit-scrollbar {
  width: 8px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 4px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: rgba(156, 163, 175, 0.7);
}

.dark .scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: rgba(75, 85, 99, 0.5);
}

.dark .scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: rgba(75, 85, 99, 0.7);
}

/* Ensure grid items have consistent height */
.auto-rows-fr {
  grid-auto-rows: 1fr;
}

/* Responsive grid adjustments for smaller screens */
@media (max-width: 1024px) {
  .grid-cols-4 {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .grid-cols-4 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .grid-cols-4 {
    grid-template-columns: repeat(1, 1fr);
  }
}
</style>
