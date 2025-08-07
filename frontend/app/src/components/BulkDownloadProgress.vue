<template>
  <div
    v-if="bulkDownloads.length > 0"
    class="fixed bottom-4 right-4 z-50 space-y-2"
  >
    <div
      v-for="bulk in bulkDownloads"
      :key="bulk.id"
      class="bg-gray-50 dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg shadow-lg p-4 min-w-80"
    >
      <!-- Header -->
      <div class="flex items-center justify-between mb-3">
        <h4 class="text-sm font-medium text-gray-900 dark:text-white">
          Bulk Download
        </h4>
        <div class="flex items-center space-x-2">
          <span
            :class="[
              'px-2 py-1 text-xs rounded-full',
              bulk.status === 'downloading'
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                : bulk.status === 'completed'
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : bulk.status === 'cancelled'
                    ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    : 'bg-gray-50 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
            ]"
          >
            {{ bulk.status }}
          </span>
          <button
            @click="removeBulkDownload(bulk.id)"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            title="Close"
          >
            ×
          </button>
        </div>
      </div>

      <!-- Progress -->
      <div class="mb-3">
        <div class="flex items-center justify-between text-sm mb-1">
          <span class="text-gray-600 dark:text-gray-400">
            {{ bulk.completed_chapters }}/{{ bulk.total_chapters }} chapters
          </span>
          <span class="text-gray-600 dark:text-gray-400">
            {{
              Math.round((bulk.completed_chapters / bulk.total_chapters) * 100)
            }}%
          </span>
        </div>
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            class="bg-primary-600 h-2 rounded-full transition-all duration-300"
            :style="{
              width: `${(bulk.completed_chapters / bulk.total_chapters) * 100}%`,
            }"
          ></div>
        </div>
      </div>

      <!-- Failed chapters indicator -->
      <div v-if="bulk.failed_chapters > 0" class="mb-3">
        <span class="text-sm text-red-600 dark:text-red-400">
          {{ bulk.failed_chapters }} chapters failed
        </span>
      </div>

      <!-- Actions -->
      <div class="flex items-center justify-between">
        <div class="text-xs text-gray-500 dark:text-gray-400">
          Started {{ formatTime(bulk.started_at) }}
        </div>
        <div class="flex space-x-2">
          <button
            v-if="bulk.status === 'downloading'"
            @click="cancelBulkDownload(bulk.id)"
            class="px-3 py-1 text-xs bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200 rounded-md hover:bg-red-200 dark:hover:bg-red-800 transition-colors"
          >
            Abort
          </button>
          <button
            v-if="bulk.status === 'completed' || bulk.status === 'cancelled'"
            @click="removeBulkDownload(bulk.id)"
            class="px-3 py-1 text-xs bg-gray-50 text-gray-700 dark:bg-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useDownloadsStore } from "../stores/downloads";

const downloadsStore = useDownloadsStore();

const bulkDownloads = computed(() => {
  return downloadsStore.getBulkDownloads.filter(
    (bulk) => bulk.status !== "dismissed",
  );
});

const cancelBulkDownload = async (bulkId) => {
  if (confirm("Are you sure you want to abort this bulk download?")) {
    try {
      await downloadsStore.cancelBulkDownload(bulkId);
    } catch (error) {
      console.error("Error canceling bulk download:", error);
      alert("Failed to cancel bulk download: " + error.message);
    }
  }
};

const removeBulkDownload = (bulkId) => {
  downloadsStore.removeBulkDownload(bulkId);
};

const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString();
};
</script>

<style scoped>
.bulk-download-progress {
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
