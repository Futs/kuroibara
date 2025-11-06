<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <div class="bg-white dark:bg-gray-800 shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
                Downloads
              </h1>
              <p class="text-gray-600 dark:text-gray-400 mt-1">
                Manage your manga downloads and view progress
              </p>
            </div>
            <div class="flex items-center space-x-4">
              <!-- Download Stats -->
              <div class="text-right">
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  Active: {{ activeDownloadsCount }} | Queue:
                  {{ queuedDownloadsCount }}
                </div>
                <div class="text-xs text-gray-400 dark:text-gray-500">
                  Speed: {{ totalDownloadSpeed }}
                </div>
              </div>
              <!-- Controls -->
              <div class="flex items-center space-x-2">
                <button
                  @click="pauseAllDownloads"
                  :disabled="activeDownloadsCount === 0"
                  class="btn btn-secondary text-sm"
                >
                  {{ allPaused ? "Resume All" : "Pause All" }}
                </button>
                <button
                  v-if="activeDownloadsCount > 0 || queuedDownloadsCount > 0"
                  @click="cancelAllDownloads"
                  class="btn bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 text-sm"
                  :disabled="cancellingAll"
                >
                  {{ cancellingAll ? "Cancelling..." : "Cancel All" }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Active Downloads -->
      <div v-if="activeDownloads.length > 0" class="mb-8">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Active Downloads ({{ activeDownloads.length }})
        </h2>
        <div class="space-y-4">
          <div
            v-for="download in activeDownloads"
            :key="download.id"
            class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg p-6"
          >
            <!-- Download Header -->
            <div class="flex items-start justify-between mb-4">
              <div class="flex-1 min-w-0">
                <h3
                  class="text-lg font-medium text-gray-900 dark:text-white truncate"
                >
                  {{ download.manga_title }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{
                    download.type === "bulk"
                      ? "Bulk Download"
                      : `Chapter ${download.chapter_number}`
                  }}
                  {{
                    download.chapter_title ? `: ${download.chapter_title}` : ""
                  }}
                </p>
              </div>
              <div class="flex items-center space-x-2 ml-4">
                <span
                  :class="[
                    'px-2 py-1 text-xs rounded-full',
                    download.status === 'downloading'
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                      : download.status === 'paused'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
                  ]"
                >
                  {{ download.status }}
                </span>
                <button
                  @click="cancelDownload(download.id)"
                  class="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>

            <!-- Progress Section -->
            <div class="space-y-3">
              <!-- Progress Bar (Example B Style) -->
              <div>
                <div class="flex items-center justify-between text-sm mb-2">
                  <span class="text-gray-600 dark:text-gray-400">
                    {{
                      download.type === "bulk"
                        ? `${download.completed_chapters}/${download.total_chapters} chapters`
                        : `${download.downloaded_pages}/${download.total_pages} pages`
                    }}
                  </span>
                  <span class="text-gray-600 dark:text-gray-400">
                    {{ Math.round(download.progress) }}%
                  </span>
                </div>
                <div
                  class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2"
                >
                  <div
                    :class="[
                      'h-2 rounded-full transition-all duration-300',
                      download.status === 'downloading'
                        ? 'bg-primary-600'
                        : download.status === 'paused'
                          ? 'bg-yellow-500'
                          : 'bg-gray-500',
                    ]"
                    :style="{ width: `${download.progress}%` }"
                  ></div>
                </div>
                <div
                  class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mt-1"
                >
                  <span>{{ download.speed || "--" }}</span>
                  <span>ETA: {{ download.eta || "--" }}</span>
                </div>
              </div>

              <!-- Additional Info -->
              <div
                class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400"
              >
                <span>Started {{ formatTime(download.started_at) }}</span>
                <span
                  >{{ formatFileSize(download.downloaded_size) }} /
                  {{ formatFileSize(download.total_size) }}</span
                >
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Download Queue -->
      <div v-if="queuedDownloads.length > 0" class="mb-8">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Download Queue ({{ queuedDownloads.length }})
        </h2>
        <div
          class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg divide-y divide-gray-200 dark:divide-gray-600"
        >
          <div
            v-for="(download, index) in queuedDownloads"
            :key="download.id"
            class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="flex-shrink-0">
                  <div
                    class="w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center"
                  >
                    <span
                      class="text-xs font-medium text-gray-600 dark:text-gray-400"
                    >
                      {{ index + 1 }}
                    </span>
                  </div>
                </div>
                <div>
                  <div
                    class="text-sm font-medium text-gray-900 dark:text-white"
                  >
                    {{ download.manga_title }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    {{
                      download.type === "bulk"
                        ? "Bulk Download"
                        : `Chapter ${download.chapter_number}`
                    }}
                    {{
                      download.chapter_title
                        ? `: ${download.chapter_title}`
                        : ""
                    }}
                  </div>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  {{ formatFileSize(download.total_size) }}
                </span>
                <button
                  @click="removeFromQueue(download.id)"
                  class="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 text-sm"
                >
                  Remove
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Download History -->
      <div v-if="downloadHistory.length > 0" class="mb-8">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Downloads ({{ downloadHistory.length }})
          </h2>
          <button
            @click="clearAllHistory"
            class="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
            :disabled="clearingHistory"
          >
            {{ clearingHistory ? "Clearing..." : "Clear History" }}
          </button>
        </div>
        <div
          class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg divide-y divide-gray-200 dark:divide-gray-600"
        >
          <div
            v-for="download in downloadHistory.slice(0, 10)"
            :key="download.id"
            class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="flex-shrink-0">
                  <div
                    :class="[
                      'w-4 h-4 rounded-full',
                      download.status === 'completed'
                        ? 'bg-green-500'
                        : download.status === 'failed'
                          ? 'bg-red-500'
                          : 'bg-gray-400',
                    ]"
                  ></div>
                </div>
                <div>
                  <div
                    class="text-sm font-medium text-gray-900 dark:text-white"
                  >
                    {{ download.manga_title }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    {{
                      download.type === "bulk"
                        ? "Bulk Download"
                        : `Chapter ${download.chapter_number}`
                    }}
                    • {{ formatTime(download.completed_at) }}
                  </div>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <span
                  :class="[
                    'text-xs px-2 py-1 rounded-full',
                    download.status === 'completed'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
                  ]"
                >
                  {{ download.status }}
                </span>
                <button
                  v-if="download.status === 'failed'"
                  @click="retryDownload(download)"
                  class="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 text-sm"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-if="
          activeDownloads.length === 0 &&
          queuedDownloads.length === 0 &&
          downloadHistory.length === 0
        "
        class="text-center py-12"
      >
        <div class="text-gray-400 dark:text-gray-500 mb-4">
          <svg
            class="mx-auto h-12 w-12"
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
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No downloads yet
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          Start downloading manga chapters from your library or search results.
        </p>
        <router-link to="/library" class="btn btn-primary">
          Go to Library
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useDownloadsStore } from "../stores/downloads";

const downloadsStore = useDownloadsStore();

// Reactive state
const cancellingAll = ref(false);
const clearingHistory = ref(false);

// Computed properties
const activeDownloads = computed(() => {
  return Array.from(downloadsStore.activeDownloads.values()).filter(
    (download) =>
      download.status === "downloading" ||
      download.status === "paused" ||
      download.status === "completed" ||
      download.status === "failed",
  );
});

const queuedDownloads = computed(() => {
  return Array.from(downloadsStore.activeDownloads.values()).filter(
    (download) => download.status === "queued",
  );
});

const downloadHistory = computed(() => {
  return downloadsStore.downloadHistory.slice().reverse(); // Most recent first
});

const activeDownloadsCount = computed(() => activeDownloads.value.length);
const queuedDownloadsCount = computed(() => queuedDownloads.value.length);

const totalDownloadSpeed = computed(() => {
  const totalSpeed = activeDownloads.value.reduce((sum, download) => {
    if (download.speed && download.status === "downloading") {
      // Parse speed like "1.2 MB/s" to bytes per second
      const match = download.speed.match(/(\d+\.?\d*)\s*(KB|MB|GB)\/s/i);
      if (match) {
        const value = parseFloat(match[1]);
        const unit = match[2].toUpperCase();
        const multiplier =
          unit === "KB"
            ? 1024
            : unit === "MB"
              ? 1024 * 1024
              : 1024 * 1024 * 1024;
        return sum + value * multiplier;
      }
    }
    return sum;
  }, 0);

  return formatSpeed(totalSpeed);
});

const allPaused = computed(() => {
  return (
    activeDownloads.value.length > 0 &&
    activeDownloads.value.every((download) => download.status === "paused")
  );
});

// Methods
const formatTime = (timestamp) => {
  if (!timestamp) return "--";
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
};

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
};

const formatSpeed = (bytesPerSecond) => {
  if (!bytesPerSecond || bytesPerSecond === 0) return "0 B/s";
  const k = 1024;
  const sizes = ["B/s", "KB/s", "MB/s", "GB/s"];
  const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k));
  return (
    parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
  );
};

const cancelDownload = async (downloadId) => {
  if (confirm("Are you sure you want to cancel this download?")) {
    try {
      await downloadsStore.cancelDownload(downloadId);
    } catch (error) {
      console.error("Error canceling download:", error);
      alert("Failed to cancel download: " + error.message);
    }
  }
};

const pauseAllDownloads = async () => {
  try {
    if (allPaused.value) {
      // Resume all downloads
      for (const download of activeDownloads.value) {
        if (download.status === "paused") {
          await downloadsStore.resumeDownload(download.id);
        }
      }
    } else {
      // Pause all downloads
      for (const download of activeDownloads.value) {
        if (download.status === "downloading") {
          await downloadsStore.pauseDownload(download.id);
        }
      }
    }
  } catch (error) {
    console.error("Error pausing/resuming downloads:", error);
    alert("Failed to pause/resume downloads: " + error.message);
  }
};

const removeFromQueue = async (downloadId) => {
  if (
    confirm("Are you sure you want to remove this download from the queue?")
  ) {
    try {
      await downloadsStore.cancelDownload(downloadId);
    } catch (error) {
      console.error("Error removing from queue:", error);
      alert("Failed to remove from queue: " + error.message);
    }
  }
};

const cancelAllDownloads = async () => {
  if (
    confirm(
      "Are you sure you want to cancel all active downloads? This action cannot be undone.",
    )
  ) {
    cancellingAll.value = true;
    try {
      const result = await downloadsStore.cancelAllDownloads();
      alert(`Successfully cancelled ${result.cancelled_count} downloads`);
    } catch (error) {
      console.error("Error cancelling all downloads:", error);
      alert("Failed to cancel all downloads: " + error.message);
    } finally {
      cancellingAll.value = false;
    }
  }
};

const clearAllHistory = async () => {
  if (
    confirm(
      "Are you sure you want to clear all download history? This action cannot be undone.",
    )
  ) {
    clearingHistory.value = true;
    try {
      const result = await downloadsStore.clearDownloadHistory();
      alert(`Successfully cleared ${result.cleared_count} completed downloads`);
    } catch (error) {
      console.error("Error clearing download history:", error);
      alert("Failed to clear download history: " + error.message);
    } finally {
      clearingHistory.value = false;
    }
  }
};

const retryDownload = async (download) => {
  try {
    // Re-add the failed download to the queue
    await downloadsStore.retryDownload(download);
  } catch (error) {
    console.error("Error retrying download:", error);
    alert("Failed to retry download: " + error.message);
  }
};

// Lifecycle
onMounted(() => {
  // Initialize downloads store (starts polling and WebSocket)
  downloadsStore.init();
});

onUnmounted(() => {
  // Keep WebSocket connection alive for other components
  // But stop polling to avoid unnecessary requests
  downloadsStore.stopPolling();
});
</script>

<style scoped>
@reference "../style.css";
.btn {
  @apply px-4 py-2 rounded-md font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2;
}

.btn-primary {
  @apply bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-secondary {
  @apply bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed;
}
</style>
