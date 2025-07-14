<template>
  <div
    class="library-statistics bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6"
  >
    <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
      Library Statistics
    </h2>

    <!-- Overview Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <div class="stat-card bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-blue-600 dark:text-blue-400 text-3xl mr-3">📚</div>
          <div>
            <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {{ statistics.total.toLocaleString() }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">
              Total Manga
            </div>
          </div>
        </div>
      </div>

      <div class="stat-card bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-green-600 dark:text-green-400 text-3xl mr-3">✅</div>
          <div>
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">
              {{ statistics.completed.toLocaleString() }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">
              Completed
            </div>
          </div>
        </div>
      </div>

      <div class="stat-card bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-yellow-600 dark:text-yellow-400 text-3xl mr-3">
            ⭐
          </div>
          <div>
            <div
              class="text-2xl font-bold text-yellow-600 dark:text-yellow-400"
            >
              {{ statistics.favorites.toLocaleString() }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">
              Favorites
            </div>
          </div>
        </div>
      </div>

      <div class="stat-card bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-purple-600 dark:text-purple-400 text-3xl mr-3">
            📖
          </div>
          <div>
            <div
              class="text-2xl font-bold text-purple-600 dark:text-purple-400"
            >
              {{ statistics.reading.toLocaleString() }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">
              Currently Reading
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Reading Status Distribution -->
    <div class="mb-8">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Reading Status Distribution
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Progress Bar Chart -->
        <div class="space-y-3">
          <div
            v-for="status in readingStatusData"
            :key="status.label"
            class="flex items-center"
          >
            <div class="w-20 text-sm text-gray-600 dark:text-gray-300">
              {{ status.label }}
            </div>
            <div class="flex-1 mx-3">
              <div class="w-full bg-gray-200 dark:bg-dark-600 rounded-full h-3">
                <div
                  class="h-3 rounded-full transition-all duration-500"
                  :class="status.colorClass"
                  :style="{ width: `${status.percentage}%` }"
                ></div>
              </div>
            </div>
            <div
              class="w-16 text-sm text-gray-600 dark:text-gray-300 text-right"
            >
              {{ status.count }} ({{ status.percentage.toFixed(1) }}%)
            </div>
          </div>
        </div>

        <!-- Pie Chart Representation -->
        <div class="flex items-center justify-center">
          <div class="relative w-48 h-48">
            <svg
              class="w-full h-full transform -rotate-90"
              viewBox="0 0 100 100"
            >
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#e5e7eb"
                stroke-width="8"
                class="dark:stroke-gray-600"
              />
              <circle
                v-for="(segment, index) in pieChartSegments"
                :key="index"
                cx="50"
                cy="50"
                r="40"
                fill="none"
                :stroke="segment.color"
                stroke-width="8"
                :stroke-dasharray="`${segment.length} ${251.2 - segment.length}`"
                :stroke-dashoffset="segment.offset"
                class="transition-all duration-500"
              />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <div class="text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ statistics.total }}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-300">
                  Total
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Top Genres -->
    <div class="mb-8">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Top Genres
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="genre in topGenres"
          :key="genre.name"
          class="bg-gray-50 dark:bg-dark-700 p-3 rounded-lg"
        >
          <div class="flex items-center justify-between">
            <span class="font-medium text-gray-900 dark:text-white">{{
              genre.name
            }}</span>
            <span class="text-sm text-gray-600 dark:text-gray-300">{{
              genre.count
            }}</span>
          </div>
          <div
            class="w-full bg-gray-200 dark:bg-dark-600 rounded-full h-2 mt-2"
          >
            <div
              class="bg-blue-600 h-2 rounded-full transition-all duration-500"
              :style="{ width: `${genre.percentage}%` }"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Top Authors -->
    <div class="mb-8">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Top Authors
      </h3>
      <div class="space-y-2">
        <div
          v-for="author in topAuthors"
          :key="author.name"
          class="flex items-center justify-between p-3 bg-gray-50 dark:bg-dark-700 rounded-lg"
        >
          <span class="font-medium text-gray-900 dark:text-white">{{
            author.name
          }}</span>
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-600 dark:text-gray-300"
              >{{ author.count }} manga</span
            >
            <div class="w-20 bg-gray-200 dark:bg-dark-600 rounded-full h-2">
              <div
                class="bg-green-600 h-2 rounded-full transition-all duration-500"
                :style="{ width: `${author.percentage}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Library Growth -->
    <div class="mb-8">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Library Growth
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg text-center">
          <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {{ addedThisWeek }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-300">
            Added This Week
          </div>
        </div>
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg text-center">
          <div class="text-2xl font-bold text-green-600 dark:text-green-400">
            {{ addedThisMonth }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-300">
            Added This Month
          </div>
        </div>
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg text-center">
          <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {{ averagePerWeek }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-300">
            Average Per Week
          </div>
        </div>
      </div>
    </div>

    <!-- Storage Information -->
    <div v-if="statistics.totalSize > 0">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Storage Information
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <div class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ formatFileSize(statistics.totalSize) }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-300">
            Total Library Size
          </div>
        </div>
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <div class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ formatFileSize(averageMangaSize) }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-300">
            Average Manga Size
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useLibraryStore } from "../stores/library";

const libraryStore = useLibraryStore();

// Computed properties
const statistics = computed(() => libraryStore.getStatistics);

const readingStatusData = computed(() => {
  const total = statistics.value.total || 1; // Avoid division by zero
  return [
    {
      label: "Unread",
      count: statistics.value.unread || 0,
      percentage: ((statistics.value.unread || 0) / total) * 100,
      colorClass: "bg-gray-500",
      color: "#6B7280",
    },
    {
      label: "Reading",
      count: statistics.value.reading || 0,
      percentage: ((statistics.value.reading || 0) / total) * 100,
      colorClass: "bg-blue-500",
      color: "#3B82F6",
    },
    {
      label: "Completed",
      count: statistics.value.completed || 0,
      percentage: ((statistics.value.completed || 0) / total) * 100,
      colorClass: "bg-green-500",
      color: "#10B981",
    },
    {
      label: "On Hold",
      count: statistics.value.onHold || 0,
      percentage: ((statistics.value.onHold || 0) / total) * 100,
      colorClass: "bg-yellow-500",
      color: "#F59E0B",
    },
    {
      label: "Dropped",
      count: statistics.value.dropped || 0,
      percentage: ((statistics.value.dropped || 0) / total) * 100,
      colorClass: "bg-red-500",
      color: "#EF4444",
    },
  ];
});

const pieChartSegments = computed(() => {
  const circumference = 2 * Math.PI * 40; // 2πr where r=40
  let currentOffset = 0;

  return readingStatusData.value.map((status) => {
    const length = (status.percentage / 100) * circumference;
    const segment = {
      length,
      offset: -currentOffset,
      color: status.color,
    };
    currentOffset += length;
    return segment;
  });
});

const topGenres = computed(() => {
  const genres = Object.entries(statistics.value.genreDistribution || {})
    .map(([name, count]) => ({
      name,
      count,
      percentage: (count / statistics.value.total) * 100,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 9);

  return genres;
});

const topAuthors = computed(() => {
  const authors = Object.entries(statistics.value.authorDistribution || {})
    .map(([name, count]) => ({
      name,
      count,
      percentage: (count / statistics.value.total) * 100,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  return authors;
});

const addedThisWeek = computed(() => {
  // This would typically come from the API
  // For now, we'll calculate based on available data
  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

  return libraryStore.manga.filter(
    (item) => new Date(item.created_at) >= oneWeekAgo,
  ).length;
});

const addedThisMonth = computed(() => {
  const oneMonthAgo = new Date();
  oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

  return libraryStore.manga.filter(
    (item) => new Date(item.created_at) >= oneMonthAgo,
  ).length;
});

const averagePerWeek = computed(() => {
  // Calculate based on the oldest manga date
  const manga = libraryStore.manga;
  if (manga.length === 0) return 0;

  const oldestDate = new Date(
    Math.min(...manga.map((item) => new Date(item.created_at))),
  );
  const now = new Date();
  const weeksDiff = Math.max(1, (now - oldestDate) / (1000 * 60 * 60 * 24 * 7));

  return Math.round(manga.length / weeksDiff);
});

const averageMangaSize = computed(() => {
  const total = statistics.value.totalSize || 0;
  const count = statistics.value.total || 1;
  return total / count;
});

// Methods
const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};
</script>

<style scoped>
.stat-card {
  transition: transform 0.2s ease-in-out;
}

.stat-card:hover {
  transform: translateY(-2px);
}

/* Custom animations for charts */
.transition-all {
  transition: all 0.5s ease-in-out;
}
</style>
