<template>
  <div class="volume-download-card bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg p-4">
    <div class="flex items-center justify-between">
      <!-- Volume Info -->
      <div class="flex-1">
        <h4 class="text-lg font-medium text-gray-900 dark:text-white">
          Volume {{ volume.number }}
        </h4>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ volume.chapters.length }} chapters
          <span v-if="volume.language" class="ml-2">• {{ formatLanguage(volume.language) }}</span>
        </p>
        
        <!-- Download Progress -->
        <div class="mt-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-400">
              {{ downloadedCount }}/{{ volume.chapters.length }} downloaded
            </span>
            <span class="text-gray-600 dark:text-gray-400">
              {{ downloadProgress }}%
            </span>
          </div>
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-1">
            <div
              class="bg-primary-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${downloadProgress}%` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Download Actions -->
      <div class="flex items-center space-x-2 ml-4">
        <!-- Download Status Icon -->
        <div class="flex-shrink-0">
          <div
            v-if="isFullyDownloaded"
            class="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 dark:bg-green-900"
            title="Fully Downloaded"
          >
            <svg class="w-4 h-4 text-green-600 dark:text-green-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <div
            v-else-if="hasErrors"
            class="flex items-center justify-center w-8 h-8 rounded-full bg-red-100 dark:bg-red-900"
            title="Some Downloads Failed"
          >
            <svg class="w-4 h-4 text-red-600 dark:text-red-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          
          <div
            v-else-if="isPartiallyDownloaded"
            class="flex items-center justify-center w-8 h-8 rounded-full bg-yellow-100 dark:bg-yellow-900"
            title="Partially Downloaded"
          >
            <svg class="w-4 h-4 text-yellow-600 dark:text-yellow-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          
          <div
            v-else
            class="flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700"
            title="Not Downloaded"
          >
            <svg class="w-4 h-4 text-gray-600 dark:text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
            </svg>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex space-x-2">
          <!-- Download Missing Button -->
          <button
            v-if="!isFullyDownloaded"
            @click="downloadMissing"
            :disabled="downloading"
            class="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-dark-600 text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              v-if="downloading"
              class="animate-spin -ml-1 mr-1 h-3 w-3 text-current"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg
              v-else
              class="h-3 w-3 mr-1"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {{ downloading ? 'Downloading...' : (isPartiallyDownloaded ? 'Download Missing' : 'Download Volume') }}
          </button>

          <!-- Retry Failed Button -->
          <button
            v-if="hasErrors"
            @click="retryFailed"
            :disabled="downloading"
            class="inline-flex items-center px-3 py-1 border border-red-300 dark:border-red-600 text-sm leading-4 font-medium rounded-md text-red-700 dark:text-red-200 bg-red-50 dark:bg-red-900 hover:bg-red-100 dark:hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg class="h-3 w-3 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Retry Failed
          </button>
        </div>
      </div>
    </div>

    <!-- Chapter List (collapsible) -->
    <div v-if="showChapters" class="mt-4 border-t border-gray-200 dark:border-dark-600 pt-4">
      <div class="space-y-2">
        <div
          v-for="chapter in volume.chapters"
          :key="chapter.id"
          class="flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 dark:hover:bg-dark-700"
        >
          <div class="flex items-center space-x-3">
            <!-- Chapter Status Icon -->
            <div class="flex-shrink-0">
              <div
                v-if="chapter.download_status === 'downloaded'"
                class="w-4 h-4 rounded-full bg-green-500"
                title="Downloaded"
              ></div>
              <div
                v-else-if="chapter.download_status === 'error'"
                class="w-4 h-4 rounded-full bg-red-500"
                title="Download Error"
              ></div>
              <div
                v-else
                class="w-4 h-4 rounded-full bg-gray-300 dark:bg-gray-600"
                title="Not Downloaded"
              ></div>
            </div>
            
            <span class="text-sm text-gray-900 dark:text-white">
              Chapter {{ chapter.number }}{{ chapter.title ? `: ${chapter.title}` : '' }}
            </span>
          </div>
          
          <button
            v-if="chapter.download_status !== 'downloaded'"
            @click="$emit('download-chapter', chapter)"
            class="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
          >
            Download
          </button>
        </div>
      </div>
    </div>

    <!-- Toggle Chapters Button -->
    <button
      @click="showChapters = !showChapters"
      class="mt-3 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 flex items-center"
    >
      <svg
        :class="['h-4 w-4 mr-1 transition-transform', showChapters ? 'rotate-90' : '']"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
      {{ showChapters ? 'Hide' : 'Show' }} Chapters ({{ volume.chapters.length }})
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  volume: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["download-volume", "download-chapter", "retry-failed"]);

const downloading = ref(false);
const showChapters = ref(false);

const downloadedCount = computed(() => {
  return props.volume.chapters.filter(chapter => chapter.download_status === 'downloaded').length;
});

const downloadProgress = computed(() => {
  if (props.volume.chapters.length === 0) return 0;
  return Math.round((downloadedCount.value / props.volume.chapters.length) * 100);
});

const isFullyDownloaded = computed(() => {
  return downloadedCount.value === props.volume.chapters.length;
});

const isPartiallyDownloaded = computed(() => {
  return downloadedCount.value > 0 && downloadedCount.value < props.volume.chapters.length;
});

const hasErrors = computed(() => {
  return props.volume.chapters.some(chapter => chapter.download_status === 'error');
});

const downloadMissing = async () => {
  downloading.value = true;
  try {
    const missingChapters = props.volume.chapters.filter(
      chapter => chapter.download_status !== 'downloaded'
    );
    
    emit("download-volume", {
      volume: props.volume,
      chapters: missingChapters,
    });
  } finally {
    downloading.value = false;
  }
};

const retryFailed = async () => {
  downloading.value = true;
  try {
    const failedChapters = props.volume.chapters.filter(
      chapter => chapter.download_status === 'error'
    );
    
    emit("retry-failed", {
      volume: props.volume,
      chapters: failedChapters,
    });
  } finally {
    downloading.value = false;
  }
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
</script>

<style scoped>
.volume-download-card {
  transition: all 0.2s ease-in-out;
}

.volume-download-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
</style>
