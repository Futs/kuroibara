<template>
  <li
    class="enhanced-chapter-card border-b border-gray-200 dark:border-dark-600 last:border-b-0"
  >
    <div
      class="px-4 py-4 hover:bg-gray-50 dark:hover:bg-dark-700 transition-colors duration-200"
    >
      <div class="flex items-center justify-between">
        <!-- Chapter Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center space-x-3">
            <div class="flex-1">
              <p
                class="text-sm font-medium text-gray-900 dark:text-white truncate"
              >
                Chapter {{ chapter.number
                }}{{ chapter.title ? `: ${chapter.title}` : "" }}
              </p>
              <div class="flex items-center space-x-4 mt-1">
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ chapter.language }} •
                  {{ chapter.pages_count || "Unknown" }} pages
                </p>
                <p
                  v-if="chapter.volume"
                  class="text-xs text-gray-500 dark:text-gray-400"
                >
                  Volume {{ chapter.volume }}
                </p>
                <p
                  v-if="chapter.reading_progress"
                  class="text-xs text-blue-600 dark:text-blue-400"
                >
                  {{
                    chapter.reading_progress.is_completed
                      ? "Completed"
                      : `Page ${chapter.reading_progress.page}`
                  }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Download Status & Actions -->
        <div class="flex items-center space-x-3">
          <!-- Download Status Icon (Example C: Status Indicator Replacement) -->
          <div class="flex-shrink-0">
            <!-- Progress Circle for downloading chapters -->
            <div
              v-if="activeDownload && activeDownload.status === 'downloading'"
              class="relative w-8 h-8"
            >
              <div
                class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-600"
              ></div>
              <div
                class="absolute inset-0 rounded-full transition-all duration-300"
                :style="{
                  background: `conic-gradient(rgb(2 132 199) ${(activeDownload.progress || 0) * 3.6}deg, transparent 0deg)`,
                }"
              ></div>
              <div
                class="absolute inset-1 rounded-full bg-white dark:bg-dark-800"
              ></div>
              <div class="absolute inset-0 flex items-center justify-center">
                <span
                  class="text-xs font-medium text-gray-700 dark:text-gray-300"
                >
                  {{ Math.round(activeDownload.progress || 0) }}
                </span>
              </div>
            </div>

            <!-- Downloaded -->
            <div
              v-else-if="chapter.download_status === 'downloaded'"
              class="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 dark:bg-green-900"
              title="Downloaded"
            >
              <svg
                class="w-4 h-4 text-green-600 dark:text-green-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>

            <!-- Download Error -->
            <div
              v-else-if="chapter.download_status === 'error'"
              class="flex items-center justify-center w-8 h-8 rounded-full bg-red-100 dark:bg-red-900"
              title="Download Error"
            >
              <svg
                class="w-4 h-4 text-red-600 dark:text-red-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>

            <!-- Not Downloaded -->
            <div
              v-else
              class="flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700"
              title="Not Downloaded"
            >
              <svg
                class="w-4 h-4 text-gray-600 dark:text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
                />
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

            <!-- Re-Download Button (for downloaded chapters) -->
            <button
              v-if="chapter.download_status === 'downloaded'"
              @click="$emit('redownload-chapter', chapter)"
              :disabled="downloading"
              class="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-dark-600 text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Re-download this chapter"
            >
              <svg
                class="h-3 w-3 mr-1"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Re-Download
            </button>

            <!-- Delete Button -->
            <button
              v-if="chapter.download_status === 'downloaded'"
              @click="confirmDelete"
              :disabled="deleting"
              class="inline-flex items-center px-3 py-1 border border-red-300 dark:border-red-600 text-sm leading-4 font-medium rounded-md text-red-700 dark:text-red-400 bg-white dark:bg-dark-800 hover:bg-red-50 dark:hover:bg-red-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Delete this chapter"
            >
              <svg
                v-if="deleting"
                class="animate-spin -ml-1 mr-1 h-3 w-3 text-current"
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
              <svg
                v-else
                class="h-3 w-3 mr-1"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              Delete
            </button>

            <!-- Download Button or Progress (Example C Style) -->
            <div v-if="chapter.download_status !== 'downloaded'">
              <!-- Show progress percentage if actively downloading -->
              <div
                v-if="activeDownload && activeDownload.status === 'downloading'"
                class="flex items-center space-x-2"
              >
                <span class="text-sm text-gray-500 dark:text-gray-400">
                  {{ Math.round(activeDownload.progress || 0) }}%
                </span>
                <button
                  @click="cancelDownload"
                  class="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                >
                  Cancel
                </button>
              </div>

              <!-- Show download button if not downloading -->
              <button
                v-else
                @click="$emit('download-chapter', chapter)"
                :disabled="downloading"
                class="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-dark-600 text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg
                  class="h-3 w-3 mr-1"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                {{ chapter.download_status === "error" ? "Retry" : "Download" }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Progress Bar (if reading progress exists) -->
      <div
        v-if="
          chapter.reading_progress && !chapter.reading_progress.is_completed
        "
        class="mt-3"
      >
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

const emit = defineEmits([
  "read-chapter",
  "download-chapter",
  "redownload-chapter",
  "delete-chapter",
]);

const downloadsStore = useDownloadsStore();
const downloading = ref(false);
const deleting = ref(false);

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

const confirmDelete = () => {
  if (
    confirm(
      `Are you sure you want to delete Chapter ${props.chapter.number}${props.chapter.title ? `: ${props.chapter.title}` : ""}?`,
    )
  ) {
    deleting.value = true;
    emit("delete-chapter", props.chapter);
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
