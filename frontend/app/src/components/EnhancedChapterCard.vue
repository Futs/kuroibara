<template>
  <li class="enhanced-chapter-card border-b border-gray-200 dark:border-dark-600 last:border-b-0">
    <div class="px-4 py-4 hover:bg-gray-50 dark:hover:bg-dark-700 transition-colors duration-200">
      <div class="flex items-center justify-between">
        <!-- Chapter Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center space-x-3">
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                Chapter {{ chapter.number }}{{ chapter.title ? `: ${chapter.title}` : '' }}
              </p>
              <div class="flex items-center space-x-4 mt-1">
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ chapter.language }} • {{ chapter.pages_count || 'Unknown' }} pages
                </p>
                <p v-if="chapter.volume" class="text-xs text-gray-500 dark:text-gray-400">
                  Volume {{ chapter.volume }}
                </p>
                <p v-if="chapter.reading_progress" class="text-xs text-blue-600 dark:text-blue-400">
                  {{ chapter.reading_progress.is_completed ? 'Completed' : `Page ${chapter.reading_progress.page}` }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Download Status & Actions -->
        <div class="flex items-center space-x-3">
          <!-- Download Status Icon -->
          <div class="flex-shrink-0">
            <!-- Downloaded -->
            <div
              v-if="chapter.download_status === 'downloaded'"
              class="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 dark:bg-green-900"
              title="Downloaded"
            >
              <svg class="w-4 h-4 text-green-600 dark:text-green-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5a2 2 0 012-2h4a2 2 0 012 2v3H8V5z" />
              </svg>
            </div>
            
            <!-- Download Error -->
            <div
              v-else-if="chapter.download_status === 'error'"
              class="flex items-center justify-center w-8 h-8 rounded-full bg-red-100 dark:bg-red-900"
              title="Download Error"
            >
              <svg class="w-4 h-4 text-red-600 dark:text-red-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            
            <!-- Not Downloaded -->
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
          <div class="flex items-center space-x-2">
            <!-- Read Button -->
            <button
              v-if="chapter.download_status === 'downloaded'"
              @click="$emit('read-chapter', chapter)"
              class="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Read
            </button>

            <!-- Download Button or Progress -->
            <div v-if="chapter.download_status !== 'downloaded'">
              <!-- Show progress if actively downloading -->
              <DownloadProgressIndicator
                v-if="activeDownload"
                :download-info="activeDownload"
                variant="inline"
                @cancel-download="cancelDownload"
              />

              <!-- Show download button if not downloading -->
              <button
                v-else
                @click="$emit('download-chapter', chapter)"
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
                {{ downloading ? 'Downloading...' : (chapter.download_status === 'error' ? 'Retry' : 'Download') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Progress Bar (if reading progress exists) -->
      <div v-if="chapter.reading_progress && !chapter.reading_progress.is_completed" class="mt-3">
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
          <div
            class="bg-primary-600 h-1.5 rounded-full transition-all duration-300"
            :style="{ width: `${progressPercentage}%` }"
          ></div>
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {{ progressPercentage }}% complete
        </p>
      </div>
    </div>
  </li>
</template>

<script setup>
import { computed, ref } from "vue";
import { useDownloadsStore } from "../stores/downloads";
import DownloadProgressIndicator from "./DownloadProgressIndicator.vue";

const props = defineProps({
  chapter: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["read-chapter", "download-chapter"]);

const downloadsStore = useDownloadsStore();
const downloading = ref(false);

const progressPercentage = computed(() => {
  if (!props.chapter.reading_progress || !props.chapter.pages_count) return 0;

  const currentPage = props.chapter.reading_progress.page || 1;
  const totalPages = props.chapter.pages_count;

  return Math.round((currentPage / totalPages) * 100);
});

const activeDownload = computed(() => {
  return downloadsStore.getDownloadsByChapter(props.chapter.id)[0] || null;
});

const isCurrentlyDownloading = computed(() => {
  return activeDownload.value && activeDownload.value.status === "downloading";
});

const cancelDownload = async () => {
  if (activeDownload.value) {
    try {
      await downloadsStore.cancelDownload(activeDownload.value.task_id);
    } catch (error) {
      console.error("Error canceling download:", error);
    }
  }
};
</script>

<style scoped>
.enhanced-chapter-card {
  transition: all 0.2s ease-in-out;
}

.enhanced-chapter-card:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.dark .enhanced-chapter-card:hover {
  background-color: rgba(255, 255, 255, 0.02);
}
</style>
