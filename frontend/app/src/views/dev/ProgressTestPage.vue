<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
          Progress Indicator Test Page
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-2">
          Test all progress indicator variations for download functionality
        </p>
      </div>

      <!-- Controls -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Test Controls
        </h2>
        <div class="flex flex-wrap gap-4">
          <button
            @click="startBulkDownload"
            :disabled="bulkDownloading"
            class="btn-primary"
          >
            {{ bulkDownloading ? 'Stop Bulk Download' : 'Start Bulk Download Test' }}
          </button>
          <button
            @click="startChapterDownload"
            :disabled="chapterDownloading"
            class="btn-secondary"
          >
            {{ chapterDownloading ? 'Stop Chapter Download' : 'Start Chapter Download Test' }}
          </button>
          <button @click="resetAll" class="btn bg-gray-500 text-white hover:bg-gray-600">
            Reset All
          </button>
        </div>
        <div class="mt-4 text-sm text-gray-600 dark:text-gray-400">
          <p>Progress: {{ Math.round(progress) }}% | Chapters: {{ completedChapters }}/{{ totalChapters }}</p>
        </div>
      </div>

      <!-- Download All Button Examples -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
          "Download All" Button Progress Indicators
        </h2>
        
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Example A: Inline Progress with Spinner -->
          <div class="space-y-4">
            <h3 class="font-medium text-gray-900 dark:text-white">
              Example A: Inline Progress with Spinner
            </h3>
            <div class="p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
              <button 
                class="btn-primary w-full flex items-center justify-center"
                :disabled="bulkDownloading"
                @click="startBulkDownload"
              >
                <svg 
                  v-if="bulkDownloading" 
                  class="animate-spin -ml-1 mr-2 h-4 w-4" 
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
                {{ bulkDownloading ? `Downloading... ${Math.round(progress)}%` : 'Download All' }}
              </button>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Button content changes to show spinner and progress percentage
            </p>
          </div>

          <!-- Example B: Progress Bar Below Button -->
          <div class="space-y-4">
            <h3 class="font-medium text-gray-900 dark:text-white">
              Example B: Progress Bar Below Button
            </h3>
            <div class="p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
              <div class="space-y-2">
                <button 
                  class="btn-primary w-full" 
                  :disabled="bulkDownloading"
                  @click="startBulkDownload"
                >
                  {{ bulkDownloading ? 'Downloading...' : 'Download All' }}
                </button>
                <div v-if="bulkDownloading" class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    class="bg-primary-600 h-2 rounded-full transition-all duration-300" 
                    :style="{width: `${progress}%`}"
                  ></div>
                </div>
                <div v-if="bulkDownloading" class="text-xs text-gray-600 dark:text-gray-400 text-center">
                  {{ completedChapters }}/{{ totalChapters }} chapters • {{ Math.round(progress) }}%
                </div>
              </div>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Progress bar appears below button with detailed stats
            </p>
          </div>

          <!-- Example C: Overlay Progress Card -->
          <div class="space-y-4">
            <h3 class="font-medium text-gray-900 dark:text-white">
              Example C: Overlay Progress Card
            </h3>
            <div class="p-4 border border-gray-200 dark:border-gray-600 rounded-lg relative">
              <button 
                class="btn-primary w-full" 
                :disabled="bulkDownloading"
                @click="startBulkDownload"
              >
                Download All
              </button>
              
              <!-- Overlay Progress Card -->
              <div 
                v-if="bulkDownloading" 
                class="absolute top-full left-4 right-4 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg p-3 z-10"
              >
                <div class="flex items-center space-x-3">
                  <svg class="animate-spin h-5 w-5 text-primary-600" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <div class="flex-1">
                    <div class="text-sm font-medium text-gray-900 dark:text-white">Downloading All Chapters</div>
                    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
                      <div class="bg-primary-600 h-1.5 rounded-full transition-all duration-300" :style="{width: `${progress}%`}"></div>
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {{ completedChapters }}/{{ totalChapters }} • {{ Math.round(progress) }}%
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Floating card appears below button with detailed progress
            </p>
          </div>
        </div>
      </div>

      <!-- Individual Chapter Button Examples -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
          Individual Chapter "Download" Button Progress Indicators
        </h2>
        
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Example A: Button State Change -->
          <div class="space-y-4">
            <h3 class="font-medium text-gray-900 dark:text-white">
              Example A: Button State Change
            </h3>
            <div class="p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
              <div class="space-y-3">
                <div v-for="(chapter, index) in testChapters" :key="index" class="flex items-center justify-between">
                  <span class="text-sm text-gray-900 dark:text-white">Chapter {{ chapter.number }}</span>
                  <button 
                    :class="[
                      'text-xs px-2 py-1 rounded-md transition-all duration-200 flex items-center',
                      chapter.downloading ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300' : 'text-primary-600 dark:text-primary-400 hover:text-primary-700'
                    ]"
                    :disabled="chapter.downloading"
                    @click="startChapterDownload(index)"
                  >
                    <svg v-if="chapter.downloading" class="animate-spin h-3 w-3 inline mr-1" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {{ chapter.downloading ? `${Math.round(chapter.progress)}%` : 'Download' }}
                  </button>
                </div>
              </div>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Button changes appearance and shows spinner with progress percentage
            </p>
          </div>

          <!-- Example B: Inline Progress Bar -->
          <div class="space-y-4">
            <h3 class="font-medium text-gray-900 dark:text-white">
              Example B: Inline Progress Bar
            </h3>
            <div class="p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
              <div class="space-y-3">
                <div v-for="(chapter, index) in testChapters" :key="`b-${index}`" class="flex items-center justify-between">
                  <span class="text-sm text-gray-900 dark:text-white">Chapter {{ chapter.number }}</span>
                  <div class="flex items-center space-x-2 min-w-0 flex-1 max-w-32">
                    <div v-if="chapter.downloading" class="flex-1">
                      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div class="bg-primary-600 h-1.5 rounded-full transition-all duration-300" :style="{width: `${chapter.progress}%`}"></div>
                      </div>
                    </div>
                    <button
                      v-if="!chapter.downloading"
                      class="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 whitespace-nowrap"
                      @click="startChapterDownload(index)"
                    >
                      Download
                    </button>
                    <span v-else class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">{{ Math.round(chapter.progress) }}%</span>
                  </div>
                </div>
              </div>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Button is replaced with progress bar and percentage
            </p>
          </div>

          <!-- Example C: Status Indicator Replacement -->
          <div class="space-y-4">
            <h3 class="font-medium text-gray-900 dark:text-white">
              Example C: Status Indicator Replacement
            </h3>
            <div class="p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
              <div class="space-y-3">
                <div v-for="(chapter, index) in testChapters" :key="`c-${index}`" class="flex items-center justify-between">
                  <div class="flex items-center space-x-3">
                    <div class="flex-shrink-0">
                      <!-- Progress Circle -->
                      <div v-if="chapter.downloading" class="relative w-4 h-4">
                        <div class="w-4 h-4 rounded-full bg-gray-200 dark:bg-gray-600"></div>
                        <div
                          class="absolute inset-0 rounded-full bg-primary-600 transition-all duration-300"
                          :style="{
                            background: `conic-gradient(rgb(2 132 199) ${chapter.progress * 3.6}deg, rgb(229 231 235) 0deg)`
                          }"
                        ></div>
                        <div class="absolute inset-1 rounded-full bg-white dark:bg-gray-800"></div>
                      </div>
                      <!-- Status Dots -->
                      <div v-else-if="chapter.status === 'downloaded'" class="w-4 h-4 rounded-full bg-green-500" title="Downloaded"></div>
                      <div v-else-if="chapter.status === 'error'" class="w-4 h-4 rounded-full bg-red-500" title="Error"></div>
                      <div v-else class="w-4 h-4 rounded-full bg-gray-300 dark:bg-gray-600" title="Not Downloaded"></div>
                    </div>
                    <span class="text-sm text-gray-900 dark:text-white">Chapter {{ chapter.number }}</span>
                  </div>
                  <button
                    v-if="!chapter.downloading && chapter.status !== 'downloaded'"
                    class="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700"
                    @click="startChapterDownload(index)"
                  >
                    Download
                  </button>
                  <span v-else-if="chapter.downloading" class="text-xs text-gray-500 dark:text-gray-400">
                    {{ Math.round(chapter.progress) }}%
                  </span>
                </div>
              </div>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Status dot becomes a circular progress indicator
            </p>
          </div>
        </div>
      </div>

      <!-- Real-world Example -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
          Real-world Example: Manga Chapter List
        </h2>

        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">Solo Leveling</h3>
            <div class="relative">
              <button
                class="btn-primary"
                :disabled="bulkDownloading"
                @click="startBulkDownload"
              >
                <svg
                  v-if="bulkDownloading"
                  class="animate-spin -ml-1 mr-2 h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ bulkDownloading ? `Downloading... ${Math.round(progress)}%` : 'Download All' }}
              </button>

              <!-- Progress overlay for bulk download -->
              <div
                v-if="bulkDownloading"
                class="absolute top-full right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg p-3 min-w-64 z-10"
              >
                <div class="flex items-center space-x-3">
                  <svg class="animate-spin h-5 w-5 text-primary-600" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <div class="flex-1">
                    <div class="text-sm font-medium text-gray-900 dark:text-white">Downloading All Chapters</div>
                    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
                      <div class="bg-primary-600 h-1.5 rounded-full transition-all duration-300" :style="{width: `${progress}%`}"></div>
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {{ completedChapters }}/{{ totalChapters }} chapters • {{ Math.round(progress) }}% • ETA: {{ estimatedTime }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="border border-gray-200 dark:border-gray-600 rounded-lg divide-y divide-gray-200 dark:divide-dark-600">
            <div
              v-for="(chapter, index) in testChapters"
              :key="`real-${index}`"
              class="p-4 hover:bg-gray-50 dark:hover:bg-dark-700 transition-colors"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="flex-shrink-0">
                    <!-- Progress Circle for downloading -->
                    <div v-if="chapter.downloading" class="relative w-5 h-5">
                      <div class="w-5 h-5 rounded-full bg-gray-200 dark:bg-gray-600"></div>
                      <div
                        class="absolute inset-0 rounded-full transition-all duration-300"
                        :style="{
                          background: `conic-gradient(rgb(2 132 199) ${chapter.progress * 3.6}deg, transparent 0deg)`
                        }"
                      ></div>
                      <div class="absolute inset-1 rounded-full bg-white dark:bg-gray-800"></div>
                    </div>
                    <!-- Status indicators -->
                    <div v-else-if="chapter.status === 'downloaded'" class="w-5 h-5 rounded-full bg-green-500" title="Downloaded"></div>
                    <div v-else-if="chapter.status === 'error'" class="w-5 h-5 rounded-full bg-red-500" title="Error"></div>
                    <div v-else class="w-5 h-5 rounded-full bg-gray-300 dark:bg-gray-600" title="Not Downloaded"></div>
                  </div>
                  <div>
                    <div class="text-sm font-medium text-gray-900 dark:text-white">
                      Chapter {{ chapter.number }}: {{ chapter.title }}
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                      {{ chapter.pages }} pages • {{ chapter.size }}
                    </div>
                  </div>
                </div>

                <div class="flex items-center space-x-3">
                  <!-- Progress info for downloading chapters -->
                  <div v-if="chapter.downloading" class="text-right">
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                      {{ Math.round(chapter.progress) }}% • {{ chapter.downloadedPages }}/{{ chapter.pages }} pages
                    </div>
                    <div class="text-xs text-gray-400 dark:text-gray-500">
                      {{ chapter.speed }} • ETA: {{ chapter.eta }}
                    </div>
                  </div>

                  <!-- Action buttons -->
                  <button
                    v-if="!chapter.downloading && chapter.status !== 'downloaded'"
                    class="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 px-3 py-1 rounded-md hover:bg-primary-50 dark:hover:bg-primary-900"
                    @click="startChapterDownload(index)"
                  >
                    Download
                  </button>
                  <button
                    v-else-if="chapter.downloading"
                    class="text-sm text-red-600 dark:text-red-400 hover:text-red-700 px-3 py-1 rounded-md hover:bg-red-50 dark:hover:bg-red-900"
                    @click="stopChapterDownload(index)"
                  >
                    Cancel
                  </button>
                  <button
                    v-else-if="chapter.status === 'error'"
                    class="text-sm text-orange-600 dark:text-orange-400 hover:text-orange-700 px-3 py-1 rounded-md hover:bg-orange-50 dark:hover:bg-orange-900"
                    @click="startChapterDownload(index)"
                  >
                    Retry
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue';

// State
const bulkDownloading = ref(false);
const chapterDownloading = ref(false);
const progress = ref(0);
const completedChapters = ref(0);
const totalChapters = ref(24);

// Test data
const testChapters = ref([
  { number: 1, title: "I'm the Only One Who Knows the End", pages: 45, size: "12.3 MB", downloading: false, progress: 0, status: 'downloaded', downloadedPages: 45, speed: '', eta: '' },
  { number: 2, title: "If I Don't Get Stronger, I'll Die", pages: 38, size: "9.8 MB", downloading: false, progress: 0, status: 'not_downloaded', downloadedPages: 0, speed: '', eta: '' },
  { number: 3, title: "It's Like a Game", pages: 42, size: "11.2 MB", downloading: false, progress: 0, status: 'error', downloadedPages: 0, speed: '', eta: '' },
  { number: 4, title: "I Hate Hospitals", pages: 40, size: "10.5 MB", downloading: false, progress: 0, status: 'not_downloaded', downloadedPages: 0, speed: '', eta: '' },
  { number: 5, title: "The Weakest Hunter", pages: 44, size: "12.1 MB", downloading: false, progress: 0, status: 'not_downloaded', downloadedPages: 0, speed: '', eta: '' },
]);

// Intervals
let bulkInterval = null;
let chapterIntervals = new Map();

// Computed
const estimatedTime = computed(() => {
  if (!bulkDownloading.value || progress.value === 0) return '--';
  const remainingProgress = 100 - progress.value;
  const timePerPercent = 200; // ms per percent (simulated)
  const remainingTime = (remainingProgress * timePerPercent) / 1000;

  if (remainingTime < 60) return `${Math.round(remainingTime)}s`;
  return `${Math.round(remainingTime / 60)}m`;
});

// Methods
const startBulkDownload = () => {
  if (bulkDownloading.value) {
    stopBulkDownload();
    return;
  }

  bulkDownloading.value = true;
  progress.value = 0;
  completedChapters.value = 0;

  bulkInterval = setInterval(() => {
    progress.value += Math.random() * 3 + 1; // Random progress increment
    completedChapters.value = Math.floor((progress.value / 100) * totalChapters.value);

    if (progress.value >= 100) {
      progress.value = 100;
      completedChapters.value = totalChapters.value;
      stopBulkDownload();
    }
  }, 200);
};

const stopBulkDownload = () => {
  bulkDownloading.value = false;
  if (bulkInterval) {
    clearInterval(bulkInterval);
    bulkInterval = null;
  }
};

const startChapterDownload = (index = null) => {
  if (index !== null) {
    // Start specific chapter download
    const chapter = testChapters.value[index];
    if (chapter.downloading) {
      stopChapterDownload(index);
      return;
    }

    chapter.downloading = true;
    chapter.progress = 0;
    chapter.downloadedPages = 0;
    chapter.speed = '1.2 MB/s';
    chapter.eta = '30s';

    const interval = setInterval(() => {
      chapter.progress += Math.random() * 4 + 2;
      chapter.downloadedPages = Math.floor((chapter.progress / 100) * chapter.pages);

      // Update ETA
      const remainingProgress = 100 - chapter.progress;
      const eta = Math.round((remainingProgress * 300) / 1000); // Simulated ETA
      chapter.eta = eta < 60 ? `${eta}s` : `${Math.round(eta / 60)}m`;

      if (chapter.progress >= 100) {
        chapter.progress = 100;
        chapter.downloadedPages = chapter.pages;
        chapter.downloading = false;
        chapter.status = 'downloaded';
        chapter.speed = '';
        chapter.eta = '';
        clearInterval(interval);
        chapterIntervals.delete(index);
      }
    }, 150);

    chapterIntervals.set(index, interval);
  } else {
    // Start general chapter download test
    if (chapterDownloading.value) {
      stopChapterDownload();
      return;
    }

    chapterDownloading.value = true;

    // Start downloading first non-downloaded chapter
    const firstChapter = testChapters.value.find(ch => ch.status !== 'downloaded' && !ch.downloading);
    if (firstChapter) {
      const index = testChapters.value.indexOf(firstChapter);
      startChapterDownload(index);
    }
  }
};

const stopChapterDownload = (index = null) => {
  if (index !== null) {
    // Stop specific chapter
    const chapter = testChapters.value[index];
    chapter.downloading = false;
    chapter.progress = 0;
    chapter.downloadedPages = 0;
    chapter.speed = '';
    chapter.eta = '';

    if (chapterIntervals.has(index)) {
      clearInterval(chapterIntervals.get(index));
      chapterIntervals.delete(index);
    }
  } else {
    // Stop all chapter downloads
    chapterDownloading.value = false;
    testChapters.value.forEach((chapter, index) => {
      if (chapter.downloading) {
        stopChapterDownload(index);
      }
    });
  }
};

const resetAll = () => {
  stopBulkDownload();
  stopChapterDownload();

  progress.value = 0;
  completedChapters.value = 0;

  // Reset test chapters
  testChapters.value.forEach((chapter, index) => {
    if (index === 0) {
      chapter.status = 'downloaded';
    } else if (index === 2) {
      chapter.status = 'error';
    } else {
      chapter.status = 'not_downloaded';
    }
    chapter.downloading = false;
    chapter.progress = 0;
    chapter.downloadedPages = index === 0 ? chapter.pages : 0;
    chapter.speed = '';
    chapter.eta = '';
  });
};

// Cleanup
onUnmounted(() => {
  stopBulkDownload();
  stopChapterDownload();
});
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-md font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2;
}

.btn-primary {
  @apply bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-secondary {
  @apply bg-secondary-600 text-white hover:bg-secondary-700 focus:ring-secondary-500 disabled:opacity-50 disabled:cursor-not-allowed;
}
</style>
