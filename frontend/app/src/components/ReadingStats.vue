<template>
  <div class="reading-stats bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6">
    <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Reading Statistics</h2>
    
    <!-- Overview Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <div class="stat-card bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-blue-600 dark:text-blue-400 text-2xl mr-3">📚</div>
          <div>
            <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {{ readingStats.totalPagesRead.toLocaleString() }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Pages Read</div>
          </div>
        </div>
      </div>
      
      <div class="stat-card bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-green-600 dark:text-green-400 text-2xl mr-3">⏰</div>
          <div>
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">
              {{ formattedReadingTime }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Time Spent</div>
          </div>
        </div>
      </div>
      
      <div class="stat-card bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-purple-600 dark:text-purple-400 text-2xl mr-3">🔥</div>
          <div>
            <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {{ readingStats.currentStreak }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Current Streak</div>
          </div>
        </div>
      </div>
      
      <div class="stat-card bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
        <div class="flex items-center">
          <div class="text-orange-600 dark:text-orange-400 text-2xl mr-3">🏆</div>
          <div>
            <div class="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {{ unlockedAchievements.length }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Achievements</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Weekly Progress -->
    <div class="mb-8">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">This Week</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <div class="text-sm text-gray-600 dark:text-gray-300">Time Spent</div>
          <div class="text-xl font-bold text-gray-900 dark:text-white">
            {{ formatTime(weeklyStats.timeSpent) }}
          </div>
        </div>
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <div class="text-sm text-gray-600 dark:text-gray-300">Pages Read</div>
          <div class="text-xl font-bold text-gray-900 dark:text-white">
            {{ weeklyStats.pagesRead }}
          </div>
        </div>
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <div class="text-sm text-gray-600 dark:text-gray-300">Chapters Read</div>
          <div class="text-xl font-bold text-gray-900 dark:text-white">
            {{ weeklyStats.chaptersRead }}
          </div>
        </div>
      </div>
    </div>

    <!-- Achievements -->
    <div class="mb-8">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Achievements</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="achievement in allAchievements"
          :key="achievement.id"
          class="achievement-card p-4 rounded-lg border"
          :class="isUnlocked(achievement.id) 
            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
            : 'bg-gray-50 dark:bg-dark-700 border-gray-200 dark:border-dark-600'"
        >
          <div class="flex items-start">
            <div class="text-2xl mr-3" :class="{ 'grayscale': !isUnlocked(achievement.id) }">
              {{ achievement.icon }}
            </div>
            <div class="flex-1">
              <div class="font-semibold text-gray-900 dark:text-white">
                {{ achievement.title }}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-300 mb-2">
                {{ achievement.description }}
              </div>
              <div v-if="!isUnlocked(achievement.id)" class="w-full bg-gray-200 dark:bg-dark-600 rounded-full h-2">
                <div 
                  class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  :style="{ width: `${getAchievementProgress(achievement.id)}%` }"
                ></div>
              </div>
              <div v-else class="text-green-600 dark:text-green-400 text-sm font-medium">
                ✓ Unlocked
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Reading History -->
    <div>
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Reading</h3>
      <div class="space-y-3">
        <div
          v-for="session in recentHistory"
          :key="session.date"
          class="flex items-center justify-between p-3 bg-gray-50 dark:bg-dark-700 rounded-lg"
        >
          <div>
            <div class="font-medium text-gray-900 dark:text-white">
              {{ session.mangaTitle }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">
              {{ session.chapterTitle }}
            </div>
          </div>
          <div class="text-right">
            <div class="text-sm text-gray-600 dark:text-gray-300">
              {{ formatTime(session.timeSpent) }} • {{ session.pagesRead }} pages
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ formatDate(session.date) }}
            </div>
          </div>
        </div>
        
        <div v-if="recentHistory.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
          No reading history yet. Start reading to see your progress!
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useReaderStore } from '../stores/reader';

const readerStore = useReaderStore();

// Computed properties
const readingStats = computed(() => readerStore.getReadingStats);
const formattedReadingTime = computed(() => readerStore.getFormattedReadingTime);
const weeklyStats = computed(() => readerStore.getWeeklyReadingStats);
const unlockedAchievements = computed(() => readerStore.getUnlockedAchievements());
const allAchievements = computed(() => readerStore.getAchievementDefinitions());
const recentHistory = computed(() => readerStore.getReadingHistory.slice(0, 10));

// Methods
const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  
  if (hours > 0) {
    return `${hours}h ${remainingMinutes}m`;
  }
  return `${minutes}m`;
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString();
};

const isUnlocked = (achievementId) => {
  return readerStore.unlockedAchievements.includes(achievementId);
};

const getAchievementProgress = (achievementId) => {
  return readerStore.getAchievementProgress(achievementId);
};
</script>

<style scoped>
.stat-card {
  transition: transform 0.2s ease-in-out;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.achievement-card {
  transition: all 0.2s ease-in-out;
}

.achievement-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.grayscale {
  filter: grayscale(100%);
  opacity: 0.6;
}
</style>
