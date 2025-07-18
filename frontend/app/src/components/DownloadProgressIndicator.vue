<template>
  <div v-if="downloadInfo" class="download-progress-indicator">
    <!-- Inline Progress (for chapter cards) -->
    <div v-if="variant === 'inline'" class="flex items-center space-x-2">
      <div class="flex-1">
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
          <div
            class="bg-primary-600 h-1.5 rounded-full transition-all duration-300"
            :style="{ width: `${downloadInfo.progress}%` }"
          ></div>
        </div>
      </div>
      <span class="text-xs text-gray-500 dark:text-gray-400 min-w-0">
        {{ downloadInfo.progress }}%
      </span>
      <button
        @click="$emit('cancel-download')"
        class="text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
        title="Cancel Download"
      >
        ×
      </button>
    </div>

    <!-- Card Progress (for download manager) -->
    <div
      v-else-if="variant === 'card'"
      class="bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg p-4"
    >
      <div class="flex items-start justify-between">
        <div class="flex-1 min-w-0">
          <h4
            class="text-sm font-medium text-gray-900 dark:text-white truncate"
          >
            {{
              downloadInfo.chapter_title ||
              `Chapter ${downloadInfo.chapter_number}`
            }}
          </h4>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {{ downloadInfo.manga_title }}
          </p>

          <!-- Progress Bar -->
          <div class="mt-3">
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-600 dark:text-gray-400">
                {{ downloadInfo.downloaded_pages || 0 }}/{{
                  downloadInfo.total_pages || 0
                }}
                pages
              </span>
              <span class="text-gray-600 dark:text-gray-400">
                {{ downloadInfo.progress }}%
              </span>
            </div>
            <div
              class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-1"
            >
              <div
                :class="[
                  'h-2 rounded-full transition-all duration-300',
                  getProgressBarClass(downloadInfo.status),
                ]"
                :style="{ width: `${downloadInfo.progress}%` }"
              ></div>
            </div>
          </div>

          <!-- Status and Time -->
          <div class="flex items-center justify-between mt-2">
            <span
              :class="[
                'text-xs font-medium',
                getStatusClass(downloadInfo.status),
              ]"
            >
              {{ formatStatus(downloadInfo.status) }}
            </span>
            <span class="text-xs text-gray-500 dark:text-gray-400">
              {{ formatElapsedTime(downloadInfo.started_at) }}
            </span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center space-x-2 ml-4">
          <button
            v-if="downloadInfo.status === 'downloading'"
            @click="$emit('cancel-download')"
            class="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
            title="Cancel Download"
          >
            Cancel
          </button>
          <button
            v-else-if="downloadInfo.status === 'failed'"
            @click="$emit('retry-download')"
            class="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
            title="Retry Download"
          >
            Retry
          </button>
        </div>
      </div>
    </div>

    <!-- Mini Progress (for status indicators) -->
    <div v-else-if="variant === 'mini'" class="flex items-center space-x-1">
      <div class="w-8 h-1 bg-gray-200 dark:bg-gray-700 rounded-full">
        <div
          class="bg-primary-600 h-1 rounded-full transition-all duration-300"
          :style="{ width: `${downloadInfo.progress}%` }"
        ></div>
      </div>
      <span class="text-xs text-gray-500 dark:text-gray-400">
        {{ downloadInfo.progress }}%
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  downloadInfo: {
    type: Object,
    default: null,
  },
  variant: {
    type: String,
    default: "inline", // "inline", "card", "mini"
  },
});

const emit = defineEmits(["cancel-download", "retry-download"]);

const getProgressBarClass = (status) => {
  switch (status) {
    case "downloading":
      return "bg-primary-600";
    case "completed":
      return "bg-green-600";
    case "failed":
      return "bg-red-600";
    case "cancelled":
      return "bg-gray-600";
    default:
      return "bg-primary-600";
  }
};

const getStatusClass = (status) => {
  switch (status) {
    case "downloading":
      return "text-primary-600 dark:text-primary-400";
    case "completed":
      return "text-green-600 dark:text-green-400";
    case "failed":
      return "text-red-600 dark:text-red-400";
    case "cancelled":
      return "text-gray-600 dark:text-gray-400";
    default:
      return "text-gray-600 dark:text-gray-400";
  }
};

const formatStatus = (status) => {
  switch (status) {
    case "downloading":
      return "Downloading...";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    case "cancelled":
      return "Cancelled";
    default:
      return "Unknown";
  }
};

const formatElapsedTime = (startTime) => {
  if (!startTime) return "";

  const start = new Date(startTime);
  const now = new Date();
  const elapsed = Math.floor((now - start) / 1000);

  if (elapsed < 60) {
    return `${elapsed}s`;
  } else if (elapsed < 3600) {
    return `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;
  } else {
    const hours = Math.floor(elapsed / 3600);
    const minutes = Math.floor((elapsed % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
};
</script>

<style scoped>
.download-progress-indicator {
  transition: all 0.2s ease-in-out;
}
</style>
