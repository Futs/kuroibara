<template>
  <div class="search">
    <div class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">
      <div class="px-4 py-5 sm:p-6">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Search Manga
        </h1>

        <div class="mt-4">
          <form @submit.prevent="search" class="space-y-4">
            <div class="flex flex-col sm:flex-row sm:space-x-4">
              <div class="flex-grow">
                <label for="query" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Search Query
                </label>
                <div class="mt-1 relative rounded-md shadow-sm">
                  <input
                    id="query"
                    v-model="searchQuery"
                    type="text"
                    class="focus:ring-primary-500 focus:border-primary-500 block w-full pl-4 pr-12 sm:text-sm border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                    placeholder="Enter manga title, author, or keywords"
                  />
                  <div class="absolute inset-y-0 right-0 flex items-center">
                    <button
                      type="button"
                      @click="searchQuery = ''"
                      v-if="searchQuery"
                      class="p-1 focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
                    >
                      <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              <div class="mt-4 sm:mt-0 sm:w-1/4 flex space-x-2">
                <div class="flex-1">
                  <label for="provider" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Provider
                  </label>
                  <select
                    id="provider"
                    v-model="provider"
                    class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-dark-600 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm rounded-md"
                  >
                    <option value="all">All Providers</option>
                    <option v-for="p in enhancedProviders" :key="p.id" :value="p.id">
                      {{ getProviderDisplayName(p) }}
                    </option>
                  </select>
                </div>

                <!-- Quick favorite toggle for selected provider -->
                <div v-if="provider !== 'all'" class="flex flex-col justify-end">
                  <button
                    @click="toggleProviderFavorite"
                    class="mt-1 p-2 rounded-md border border-gray-300 dark:border-dark-600 hover:bg-gray-50 dark:hover:bg-dark-600 transition-colors"
                    :class="{
                      'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700': isCurrentProviderFavorite,
                      'text-gray-400 hover:text-gray-500': !isCurrentProviderFavorite
                    }"
                    :title="isCurrentProviderFavorite ? 'Remove from favorites' : 'Add to favorites'"
                  >
                    <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" :fill="isCurrentProviderFavorite ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <div class="flex flex-col sm:flex-row sm:space-x-4">
              <div class="sm:w-1/3">
                <label for="status" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Status
                </label>
                <select
                  id="status"
                  v-model="filters.status"
                  class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-dark-600 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm rounded-md"
                >
                  <option value="">Any Status</option>
                  <option value="ongoing">Ongoing</option>
                  <option value="completed">Completed</option>
                  <option value="hiatus">Hiatus</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              <div class="mt-4 sm:mt-0 sm:w-1/3">
                <label for="genre" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Genre
                </label>
                <select
                  id="genre"
                  v-model="filters.genre"
                  class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-dark-600 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm rounded-md"
                >
                  <option value="">Any Genre</option>
                  <option v-for="genre in genres" :key="genre" :value="genre">
                    {{ genre }}
                  </option>
                </select>
              </div>

              <div class="mt-4 sm:mt-0 sm:w-1/3 flex items-end">
                <button
                  type="submit"
                  :disabled="loading || !searchQuery"
                  class="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <svg v-else class="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Search
                </button>
              </div>
            </div>
          </form>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="mt-8 flex justify-center">
          <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="mt-8">
          <div class="rounded-md bg-red-50 dark:bg-red-900 p-4">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-red-400 dark:text-red-300" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="ml-3">
                <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
                  {{ error }}
                </h3>
                <div class="mt-2 text-sm text-red-700 dark:text-red-300">
                  <button
                    @click="search"
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
        <div v-else-if="hasSearched && results.length === 0" class="mt-8 text-center">
          <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No results found</h3>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Try adjusting your search or filter criteria.
          </p>
        </div>

        <!-- Results -->
        <div v-else-if="results.length > 0" class="mt-8">
          <h2 class="text-lg font-medium text-gray-900 dark:text-white">
            Search Results
          </h2>

          <div class="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
            <SearchResultCard
              v-for="result in results"
              :key="result.id"
              :manga="result"
              @add-to-library="addToLibrary"
            />
          </div>

          <!-- Pagination -->
          <div v-if="totalPages > 1" class="mt-6 flex justify-center">
            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
              <button
                @click="prevPage"
                :disabled="currentPage === 1"
                class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span class="sr-only">Previous</span>
                <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              </button>

              <button
                v-for="page in paginationRange"
                :key="page"
                @click="goToPage(page)"
                :class="[
                  page === currentPage
                    ? 'z-10 bg-primary-50 dark:bg-primary-900 border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'bg-white dark:bg-dark-800 border-gray-300 dark:border-dark-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-700',
                  'relative inline-flex items-center px-4 py-2 border text-sm font-medium'
                ]"
              >
                {{ page }}
              </button>

              <button
                @click="nextPage"
                :disabled="currentPage === totalPages"
                class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span class="sr-only">Next</span>
                <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                </svg>
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useSearchStore } from '../stores/search';
import { useLibraryStore } from '../stores/library';
import { useProviderPreferencesStore } from '../stores/providerPreferences';
import SearchResultCard from '../components/SearchResultCard.vue';
import axios from 'axios';

const searchStore = useSearchStore();
const libraryStore = useLibraryStore();
const providerPreferencesStore = useProviderPreferencesStore();

const searchQuery = ref('');
const provider = ref('all');
const providers = ref([]);
const genres = ref([]);
const hasSearched = ref(false);
const providersLoading = ref(false);

// Get data from store
const results = computed(() => searchStore.getResults);
const loading = computed(() => searchStore.loading);
const error = computed(() => searchStore.error);
const filters = computed(() => searchStore.getFilters);
const pagination = computed(() => searchStore.getPagination);

// Computed values for pagination
const currentPage = computed(() => pagination.value.page);
const totalPages = computed(() => Math.ceil(pagination.value.total / pagination.value.limit));
const paginationRange = computed(() => {
  const range = [];
  const maxVisiblePages = 5;

  let startPage = Math.max(1, currentPage.value - Math.floor(maxVisiblePages / 2));
  let endPage = Math.min(totalPages.value, startPage + maxVisiblePages - 1);

  if (endPage - startPage + 1 < maxVisiblePages) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1);
  }

  for (let i = startPage; i <= endPage; i++) {
    range.push(i);
  }

  return range;
});

// Enhanced providers with preference data
const enhancedProviders = computed(() => {
  return providers.value.map(provider => {
    const prefInfo = providerPreferencesStore.getProviderDisplayInfo(provider.id);
    return {
      ...provider,
      ...prefInfo,
    };
  }).sort((a, b) => {
    // Sort favorites first, then by name
    if (a.isFavorite && !b.isFavorite) return -1;
    if (!a.isFavorite && b.isFavorite) return 1;
    if (a.isFavorite && b.isFavorite) {
      return (a.priorityOrder || 999) - (b.priorityOrder || 999);
    }
    return a.name.localeCompare(b.name);
  });
});

// Check if current provider is favorite
const isCurrentProviderFavorite = computed(() => {
  if (provider.value === 'all') return false;
  return providerPreferencesStore.isProviderFavorite(provider.value);
});

// Watch for changes in the query and provider
watch([searchQuery, provider], () => {
  searchStore.setQuery(searchQuery.value);
  searchStore.setProvider(provider.value);
});

// Fetch providers
const fetchProviders = async () => {
  providersLoading.value = true;

  try {
    const response = await axios.get('/v1/search/providers');
    providers.value = response.data;
  } catch (error) {
    console.error('Failed to fetch providers:', error);
  } finally {
    providersLoading.value = false;
  }
};

// Fetch genres
const fetchGenres = async () => {
  try {
    const response = await axios.get('/v1/search/genres');
    genres.value = response.data;
  } catch (error) {
    console.error('Failed to fetch genres:', error);
  }
};

// Get provider display name with indicators
const getProviderDisplayName = (provider) => {
  let name = provider.name;

  if (provider.isFavorite) {
    name = `⭐ ${name}`;
    if (provider.priorityOrder) {
      name += ` (${provider.priorityOrder})`;
    }
  }

  if (!provider.isEnabled) {
    name += ' (Disabled)';
  } else if (provider.status === 'unhealthy') {
    name += ' (Unhealthy)';
  } else if (provider.status === 'degraded') {
    name += ' (Degraded)';
  }

  return name;
};

// Toggle favorite status of current provider
const toggleProviderFavorite = async () => {
  if (provider.value === 'all') return;

  const success = await providerPreferencesStore.toggleProviderFavorite(provider.value);
  if (!success) {
    console.error('Failed to toggle provider favorite status');
  }
};

// Search methods
const search = async () => {
  if (!searchQuery.value) return;

  hasSearched.value = true;
  await searchStore.search();
};

// Pagination methods
const prevPage = () => {
  if (currentPage.value > 1) {
    searchStore.setPage(currentPage.value - 1);
  }
};

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    searchStore.setPage(currentPage.value + 1);
  }
};

const goToPage = (page) => {
  searchStore.setPage(page);
};

// Add manga to library
const addToLibrary = async (mangaId) => {
  await libraryStore.addToLibrary(mangaId);
};

onMounted(() => {
  fetchProviders();
  fetchGenres();
  // Fetch provider preferences to show favorites and status
  providerPreferencesStore.fetchProviderPreferences();

  // Initialize from URL query params if present
  const urlParams = new URLSearchParams(window.location.search);
  const q = urlParams.get('q');
  const p = urlParams.get('provider');

  if (q) {
    searchQuery.value = q;
    searchStore.setQuery(q);

    if (p) {
      provider.value = p;
      searchStore.setProvider(p);
    }

    search();
  }
});
</script>
