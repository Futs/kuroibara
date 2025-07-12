<template>
  <div class="chapter-filters bg-gray-50 dark:bg-dark-700 p-4 rounded-lg border border-gray-200 dark:border-dark-600">
    <div class="flex flex-wrap items-center gap-4">
      <!-- Language Filter -->
      <div class="flex items-center space-x-2">
        <label for="language-filter" class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Language:
        </label>
        <select
          id="language-filter"
          v-model="localFilters.language"
          @change="updateFilters"
          class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white"
        >
          <option value="">All Languages</option>
          <option v-for="lang in availableLanguages" :key="lang" :value="lang">
            {{ formatLanguage(lang) }}
          </option>
        </select>
      </div>

      <!-- Volume Filter -->
      <div class="flex items-center space-x-2">
        <label for="volume-filter" class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Volume:
        </label>
        <select
          id="volume-filter"
          v-model="localFilters.volume"
          @change="updateFilters"
          class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white"
        >
          <option value="">All Volumes</option>
          <option v-for="volume in availableVolumes" :key="volume" :value="volume">
            Volume {{ volume }}
          </option>
        </select>
      </div>

      <!-- Download Status Filter -->
      <div class="flex items-center space-x-2">
        <label for="download-filter" class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Status:
        </label>
        <select
          id="download-filter"
          v-model="localFilters.downloadStatus"
          @change="updateFilters"
          class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white"
        >
          <option value="">All Chapters</option>
          <option value="downloaded">Downloaded Only</option>
          <option value="not_downloaded">Not Downloaded</option>
          <option value="error">Failed Downloads</option>
        </select>
      </div>

      <!-- Reading Status Filter -->
      <div class="flex items-center space-x-2">
        <label for="reading-filter" class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Reading:
        </label>
        <select
          id="reading-filter"
          v-model="localFilters.readingStatus"
          @change="updateFilters"
          class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white"
        >
          <option value="">All</option>
          <option value="unread">Unread</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      <!-- Clear Filters Button -->
      <button
        v-if="hasActiveFilters"
        @click="clearFilters"
        class="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium"
      >
        Clear Filters
      </button>
    </div>

    <!-- Active Filters Summary -->
    <div v-if="hasActiveFilters" class="mt-3 flex flex-wrap gap-2">
      <span class="text-sm text-gray-600 dark:text-gray-400">Active filters:</span>
      
      <span
        v-if="localFilters.language"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-300"
      >
        Language: {{ formatLanguage(localFilters.language) }}
        <button @click="clearFilter('language')" class="ml-1 text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200">
          ×
        </button>
      </span>
      
      <span
        v-if="localFilters.volume"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-300"
      >
        Volume: {{ localFilters.volume }}
        <button @click="clearFilter('volume')" class="ml-1 text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200">
          ×
        </button>
      </span>
      
      <span
        v-if="localFilters.downloadStatus"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-300"
      >
        Status: {{ formatDownloadStatus(localFilters.downloadStatus) }}
        <button @click="clearFilter('downloadStatus')" class="ml-1 text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200">
          ×
        </button>
      </span>
      
      <span
        v-if="localFilters.readingStatus"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-300"
      >
        Reading: {{ formatReadingStatus(localFilters.readingStatus) }}
        <button @click="clearFilter('readingStatus')" class="ml-1 text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200">
          ×
        </button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";

const props = defineProps({
  availableLanguages: {
    type: Array,
    default: () => [],
  },
  availableVolumes: {
    type: Array,
    default: () => [],
  },
  filters: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(["update-filters"]);

const localFilters = ref({
  language: props.filters.language || "",
  volume: props.filters.volume || "",
  downloadStatus: props.filters.downloadStatus || "",
  readingStatus: props.filters.readingStatus || "",
});

const hasActiveFilters = computed(() => {
  return Object.values(localFilters.value).some(value => value !== "");
});

const updateFilters = () => {
  emit("update-filters", { ...localFilters.value });
};

const clearFilters = () => {
  localFilters.value = {
    language: "",
    volume: "",
    downloadStatus: "",
    readingStatus: "",
  };
  updateFilters();
};

const clearFilter = (filterKey) => {
  localFilters.value[filterKey] = "";
  updateFilters();
};

const formatLanguage = (lang) => {
  const languageMap = {
    en: "English",
    es: "Spanish",
    fr: "French",
    de: "German",
    it: "Italian",
    pt: "Portuguese",
    pb: "Portuguese (Brazil)",
    ru: "Russian",
    ja: "Japanese",
    ko: "Korean",
    zh: "Chinese",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
  };
  
  return languageMap[lang] || lang.toUpperCase();
};

const formatDownloadStatus = (status) => {
  const statusMap = {
    downloaded: "Downloaded",
    not_downloaded: "Not Downloaded",
    error: "Failed Downloads",
  };
  
  return statusMap[status] || status;
};

const formatReadingStatus = (status) => {
  const statusMap = {
    unread: "Unread",
    in_progress: "In Progress",
    completed: "Completed",
  };
  
  return statusMap[status] || status;
};

// Watch for external filter changes
watch(() => props.filters, (newFilters) => {
  localFilters.value = {
    language: newFilters.language || "",
    volume: newFilters.volume || "",
    downloadStatus: newFilters.downloadStatus || "",
    readingStatus: newFilters.readingStatus || "",
  };
}, { deep: true });
</script>

<style scoped>
.chapter-filters {
  transition: all 0.2s ease-in-out;
}
</style>
