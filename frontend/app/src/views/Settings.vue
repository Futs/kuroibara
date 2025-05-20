<template>
  <div class="settings">
    <div class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">
      <div class="px-4 py-5 sm:px-6">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Customize your Kurobara experience
        </p>
      </div>
      
      <div class="border-t border-gray-200 dark:border-dark-600 px-4 py-5 sm:p-6">
        <div class="space-y-6">
          <!-- Theme Settings -->
          <div>
            <h3 class="text-lg font-medium leading-6 text-gray-900 dark:text-white">
              Appearance
            </h3>
            
            <div class="mt-4">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Theme
              </label>
              <div class="mt-2 grid grid-cols-3 gap-3">
                <button 
                  @click="setTheme('light')" 
                  class="relative px-4 py-3 border rounded-md shadow-sm focus:outline-none"
                  :class="[
                    theme === 'light' 
                      ? 'bg-primary-50 dark:bg-primary-900 border-primary-500 ring-2 ring-primary-500' 
                      : 'border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800'
                  ]"
                >
                  <span class="flex items-center justify-center text-sm font-medium text-gray-900 dark:text-white">
                    <svg class="h-5 w-5 mr-2 text-yellow-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    Light
                  </span>
                </button>
                
                <button 
                  @click="setTheme('dark')" 
                  class="relative px-4 py-3 border rounded-md shadow-sm focus:outline-none"
                  :class="[
                    theme === 'dark' 
                      ? 'bg-primary-50 dark:bg-primary-900 border-primary-500 ring-2 ring-primary-500' 
                      : 'border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800'
                  ]"
                >
                  <span class="flex items-center justify-center text-sm font-medium text-gray-900 dark:text-white">
                    <svg class="h-5 w-5 mr-2 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                    Dark
                  </span>
                </button>
                
                <button 
                  @click="setTheme('system')" 
                  class="relative px-4 py-3 border rounded-md shadow-sm focus:outline-none"
                  :class="[
                    theme === 'system' 
                      ? 'bg-primary-50 dark:bg-primary-900 border-primary-500 ring-2 ring-primary-500' 
                      : 'border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800'
                  ]"
                >
                  <span class="flex items-center justify-center text-sm font-medium text-gray-900 dark:text-white">
                    <svg class="h-5 w-5 mr-2 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    System
                  </span>
                </button>
              </div>
            </div>
          </div>
          
          <!-- Content Settings -->
          <div class="pt-6 border-t border-gray-200 dark:border-dark-600">
            <h3 class="text-lg font-medium leading-6 text-gray-900 dark:text-white">
              Content
            </h3>
            
            <div class="mt-4 flex items-center justify-between">
              <div>
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Blur NSFW Content
                </label>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Blur images marked as NSFW or explicit
                </p>
              </div>
              <button 
                @click="toggleNsfwBlur" 
                class="relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                :class="nsfwBlur ? 'bg-primary-600' : 'bg-gray-200 dark:bg-dark-600'"
              >
                <span 
                  class="pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200"
                  :class="nsfwBlur ? 'translate-x-5' : 'translate-x-0'"
                ></span>
              </button>
            </div>
          </div>
          
          <!-- Download Settings -->
          <div class="pt-6 border-t border-gray-200 dark:border-dark-600">
            <h3 class="text-lg font-medium leading-6 text-gray-900 dark:text-white">
              Downloads
            </h3>
            
            <div class="mt-4">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Download Quality
              </label>
              <div class="mt-2 grid grid-cols-3 gap-3">
                <button 
                  @click="setDownloadQuality('low')" 
                  class="relative px-4 py-3 border rounded-md shadow-sm focus:outline-none"
                  :class="[
                    downloadQuality === 'low' 
                      ? 'bg-primary-50 dark:bg-primary-900 border-primary-500 ring-2 ring-primary-500' 
                      : 'border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800'
                  ]"
                >
                  <span class="text-sm font-medium text-gray-900 dark:text-white">
                    Low
                  </span>
                </button>
                
                <button 
                  @click="setDownloadQuality('medium')" 
                  class="relative px-4 py-3 border rounded-md shadow-sm focus:outline-none"
                  :class="[
                    downloadQuality === 'medium' 
                      ? 'bg-primary-50 dark:bg-primary-900 border-primary-500 ring-2 ring-primary-500' 
                      : 'border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800'
                  ]"
                >
                  <span class="text-sm font-medium text-gray-900 dark:text-white">
                    Medium
                  </span>
                </button>
                
                <button 
                  @click="setDownloadQuality('high')" 
                  class="relative px-4 py-3 border rounded-md shadow-sm focus:outline-none"
                  :class="[
                    downloadQuality === 'high' 
                      ? 'bg-primary-50 dark:bg-primary-900 border-primary-500 ring-2 ring-primary-500' 
                      : 'border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800'
                  ]"
                >
                  <span class="text-sm font-medium text-gray-900 dark:text-white">
                    High
                  </span>
                </button>
              </div>
              <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Higher quality downloads will use more storage space.
              </p>
            </div>
            
            <div class="mt-6">
              <label for="downloadPath" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Download Path
              </label>
              <div class="mt-1 flex rounded-md shadow-sm">
                <input 
                  id="downloadPath" 
                  v-model="downloadPath" 
                  type="text" 
                  class="flex-1 min-w-0 block w-full px-3 py-2 rounded-md focus:ring-primary-500 focus:border-primary-500 sm:text-sm border-gray-300 dark:border-dark-600 dark:bg-dark-700 dark:text-white"
                  placeholder="Default download location"
                />
                <button 
                  @click="resetDownloadPath" 
                  class="ml-3 inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Reset
                </button>
              </div>
              <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Leave empty to use the default download location.
              </p>
            </div>
          </div>
          
          <!-- Save Button -->
          <div class="pt-6 border-t border-gray-200 dark:border-dark-600 flex justify-end">
            <button 
              @click="saveSettings" 
              :disabled="loading" 
              class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useSettingsStore } from '../stores/settings';

const settingsStore = useSettingsStore();

// Local state
const theme = ref(settingsStore.getTheme);
const nsfwBlur = ref(settingsStore.getNsfwBlur);
const downloadQuality = ref(settingsStore.getDownloadQuality);
const downloadPath = ref(settingsStore.getDownloadPath);

// Computed
const loading = computed(() => settingsStore.loading);
const error = computed(() => settingsStore.error);

// Methods
const setTheme = (newTheme) => {
  theme.value = newTheme;
};

const toggleNsfwBlur = () => {
  nsfwBlur.value = !nsfwBlur.value;
};

const setDownloadQuality = (quality) => {
  downloadQuality.value = quality;
};

const resetDownloadPath = () => {
  downloadPath.value = 'default';
};

const saveSettings = async () => {
  settingsStore.setTheme(theme.value);
  settingsStore.setNsfwBlur(nsfwBlur.value);
  settingsStore.setDownloadQuality(downloadQuality.value);
  settingsStore.setDownloadPath(downloadPath.value);
  
  await settingsStore.updateUserSettings();
};

onMounted(() => {
  settingsStore.fetchUserSettings();
});
</script>
