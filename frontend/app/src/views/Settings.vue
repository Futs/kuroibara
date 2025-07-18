<template>
  <div class="settings">
    <div class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">
      <div class="px-4 py-5 sm:px-6">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Customize your Kuroibara experience
        </p>
      </div>

      <!-- Tab Navigation -->
      <div class="border-t border-gray-200 dark:border-dark-600">
        <nav class="flex space-x-8 px-4 sm:px-6" aria-label="Tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              activeTab === tab.id
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm',
            ]"
          >
            {{ tab.name }}
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div class="px-4 py-5 sm:p-6">
        <!-- General Tab -->
        <div v-if="activeTab === 'general'" class="space-y-6">
          <!-- Provider Preferences -->
          <div>
            <div class="mb-6">
              <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Providers
              </h3>
              <p class="text-gray-600 dark:text-gray-400">
                Configure your preferred manga providers and their settings.
              </p>
            </div>
            <div class="mt-4">
              <ProviderPreferences />
            </div>
          </div>
        </div>

        <!-- Integrations Tab -->
        <div v-else-if="activeTab === 'integrations'" class="space-y-6">
          <!-- External Integrations -->
          <div>
            <div class="mb-6">
              <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                External Integrations
              </h3>
              <p class="text-gray-600 dark:text-gray-400">
                Connect with external manga tracking services and APIs to sync
                your reading progress and ratings.
              </p>
            </div>
            <div class="mt-4">
              <IntegrationSettings />
            </div>
          </div>
        </div>

        <!-- Media Management Tab -->
        <div v-else-if="activeTab === 'media'" class="space-y-6">
          <!-- Naming & Organization -->
          <div>
            <div class="mb-6">
              <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Naming & Organization
              </h3>
              <p class="text-gray-600 dark:text-gray-400">
                Configure how manga and chapters are named and organized
              </p>
            </div>

            <div class="mt-4">
              <label
                for="mangaNamingFormat"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Manga Folder Structure
              </label>
              <div class="mt-1">
                <input
                  id="mangaNamingFormat"
                  v-model="namingFormatManga"
                  type="text"
                  class="block w-full px-3 py-2 rounded-md focus:ring-primary-500 focus:border-primary-500 sm:text-sm border-gray-300 dark:border-dark-600 dark:bg-dark-700 dark:text-white"
                  placeholder="{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
                />
              </div>
              <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Available variables: {Manga Title}, {Volume}, {Chapter Number},
                {Chapter Name}, {Language}, {Year}, {Source}
              </p>
              <div
                v-if="mangaNamingPreview"
                class="mt-2 p-2 bg-gray-50 dark:bg-dark-700 rounded text-xs text-gray-600 dark:text-gray-300"
              >
                Preview: {{ mangaNamingPreview }}
              </div>
            </div>

            <div class="mt-6">
              <label
                for="chapterNamingFormat"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Chapter File Naming
              </label>
              <div class="mt-1">
                <input
                  id="chapterNamingFormat"
                  v-model="namingFormatChapter"
                  type="text"
                  class="block w-full px-3 py-2 rounded-md focus:ring-primary-500 focus:border-primary-500 sm:text-sm border-gray-300 dark:border-dark-600 dark:bg-dark-700 dark:text-white"
                  placeholder="{Chapter Number} - {Chapter Name}"
                />
              </div>
              <div
                v-if="chapterNamingPreview"
                class="mt-2 p-2 bg-gray-50 dark:bg-dark-700 rounded text-xs text-gray-600 dark:text-gray-300"
              >
                Preview: {{ chapterNamingPreview }}
              </div>
            </div>

            <div class="mt-6 space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <label
                    class="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Auto-organize imports
                  </label>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    Automatically organize files when importing
                  </p>
                </div>
                <button
                  @click="toggleAutoOrganize"
                  class="relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  :class="
                    autoOrganizeImports
                      ? 'bg-primary-600'
                      : 'bg-gray-200 dark:bg-dark-600'
                  "
                >
                  <span
                    class="pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200"
                    :class="
                      autoOrganizeImports ? 'translate-x-5' : 'translate-x-0'
                    "
                  ></span>
                </button>
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <label
                    class="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Create CBZ files
                  </label>
                  <p class="text-xs text-gray-500 dark:text-gray-400">
                    Convert chapters to CBZ format for better compatibility
                  </p>
                </div>
                <button
                  @click="toggleCreateCbz"
                  class="relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  :class="
                    createCbzFiles
                      ? 'bg-primary-600'
                      : 'bg-gray-200 dark:bg-dark-600'
                  "
                >
                  <span
                    class="pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200"
                    :class="createCbzFiles ? 'translate-x-5' : 'translate-x-0'"
                  ></span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- UI Tab -->
        <div v-else-if="activeTab === 'ui'" class="space-y-6">
          <!-- Theme Settings -->
          <div>
            <div class="mb-6">
              <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Themes
              </h3>
              <p class="text-gray-600 dark:text-gray-400">
                Choose your preferred color scheme
              </p>
            </div>

            <div class="mt-4">
              <label
                class="text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Theme
              </label>
              <div class="mt-2 grid grid-cols-3 gap-3">
                <button
                  @click="setTheme('light')"
                  class="relative px-4 py-3 border rounded-md shadow-sm focus:outline-none"
                  :class="[
                    theme === 'light'
                      ? 'bg-primary-50 dark:bg-primary-900 border-primary-500 ring-2 ring-primary-500'
                      : 'border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800',
                  ]"
                >
                  <span
                    class="flex items-center justify-center text-sm font-medium text-gray-900 dark:text-white"
                  >
                    <svg
                      class="h-5 w-5 mr-2 text-yellow-500"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                      />
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
                      : 'border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800',
                  ]"
                >
                  <span
                    class="flex items-center justify-center text-sm font-medium text-gray-900 dark:text-white"
                  >
                    <svg
                      class="h-5 w-5 mr-2 text-gray-400"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                      />
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
                      : 'border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800',
                  ]"
                >
                  <span
                    class="flex items-center justify-center text-sm font-medium text-gray-900 dark:text-white"
                  >
                    <svg
                      class="h-5 w-5 mr-2 text-gray-500"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                      />
                    </svg>
                    System
                  </span>
                </button>
              </div>
            </div>
          </div>

          <!-- Language Settings -->
          <div
            class="pt-8 mt-8 border-t-2 border-gray-200 dark:border-dark-600"
          >
            <div class="mb-6">
              <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Language
              </h3>
              <p class="text-gray-600 dark:text-gray-400">
                Choose your preferred language for the interface
              </p>
            </div>
            <div class="mt-4">
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Language settings will be available in future updates.
              </p>
            </div>
          </div>

          <!-- NSFW Content Settings -->
          <div
            class="pt-8 mt-8 border-t-2 border-gray-200 dark:border-dark-600"
          >
            <div class="mb-6">
              <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Content Filtering
              </h3>
              <p class="text-gray-600 dark:text-gray-400">
                Control how explicit content is displayed
              </p>
            </div>

            <div class="mt-4 flex items-center justify-between">
              <div>
                <label
                  class="text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Blur NSFW Content
                </label>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Blur images marked as NSFW or explicit
                </p>
              </div>
              <button
                @click="toggleNsfwBlur"
                class="relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                :class="
                  nsfwBlur ? 'bg-primary-600' : 'bg-gray-200 dark:bg-dark-600'
                "
              >
                <span
                  class="pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200"
                  :class="nsfwBlur ? 'translate-x-5' : 'translate-x-0'"
                ></span>
              </button>
            </div>
          </div>
        </div>

        <!-- Backup & Recovery Tab -->
        <div v-else-if="activeTab === 'backup'" class="space-y-6">
          <!-- Backup Management -->
          <div class="mb-8">
            <BackupManager />
          </div>

          <!-- Storage Recovery -->
          <div
            class="pt-8 mt-8 border-t-2 border-gray-200 dark:border-dark-600"
          >
            <StorageRecovery />
          </div>
        </div>

        <!-- Downloads Tab -->
        <div v-else-if="activeTab === 'downloads'" class="space-y-6">
          <!-- Storage Settings -->
          <div>
            <div class="mb-6">
              <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Storage Settings
              </h3>
              <p class="text-gray-600 dark:text-gray-400">
                Configure how and where your manga files are stored
              </p>
            </div>

            <div class="space-y-6">
              <!-- Storage Type -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Storage Type
                </label>
                <div class="flex items-center space-x-4">
                  <select
                    v-model="storageType"
                    class="block w-48 px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
                  >
                    <option value="local">Local Storage</option>
                    <option value="s3">Amazon S3</option>
                    <option value="gcs">Google Cloud Storage</option>
                    <option value="azure">Azure Blob Storage</option>
                  </select>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    Choose where to store downloaded manga files
                  </p>
                </div>
              </div>

              <!-- Max Upload Size -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Maximum Upload Size
                </label>
                <div class="flex items-center space-x-4">
                  <select
                    v-model="maxUploadSize"
                    class="block w-48 px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
                  >
                    <option value="50MB">50 MB</option>
                    <option value="100MB">100 MB</option>
                    <option value="250MB">250 MB</option>
                    <option value="500MB">500 MB</option>
                    <option value="1GB">1 GB</option>
                    <option value="2GB">2 GB</option>
                  </select>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    Maximum size for individual file uploads
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Chapter Update Settings -->
          <div>
            <div class="mb-6">
              <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Chapter Update Settings
              </h3>
              <p class="text-gray-600 dark:text-gray-400">
                Configure how and when chapter lists are updated from providers
              </p>
            </div>

            <div class="space-y-6">
              <!-- Auto-Refresh Interval -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Auto-Refresh Interval
                </label>
                <div class="flex items-center space-x-4">
                  <select
                    v-model="chapterAutoRefreshInterval"
                    class="block w-48 px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-dark-700 text-gray-900 dark:text-white"
                  >
                    <option :value="0">Disabled</option>
                    <option :value="60">1 minute</option>
                    <option :value="300">5 minutes</option>
                    <option :value="600">10 minutes</option>
                    <option :value="1800">30 minutes</option>
                    <option :value="3600">1 hour</option>
                  </select>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    How often to automatically check for new chapters
                  </p>
                </div>
              </div>

              <!-- Check on Tab Focus -->
              <div class="flex items-center justify-between">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Check on Tab Focus
                  </label>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    Automatically check for updates when returning to the tab
                  </p>
                </div>
                <button
                  @click="chapterCheckOnTabFocus = !chapterCheckOnTabFocus"
                  :class="[
                    chapterCheckOnTabFocus ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700',
                    'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2'
                  ]"
                >
                  <span
                    :class="[
                      chapterCheckOnTabFocus ? 'translate-x-5' : 'translate-x-0',
                      'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out'
                    ]"
                  />
                </button>
              </div>

              <!-- Show Update Notifications -->
              <div class="flex items-center justify-between">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Show Update Notifications
                  </label>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    Display notifications when new chapters are found
                  </p>
                </div>
                <button
                  @click="chapterShowUpdateNotifications = !chapterShowUpdateNotifications"
                  :class="[
                    chapterShowUpdateNotifications ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700',
                    'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2'
                  ]"
                >
                  <span
                    :class="[
                      chapterShowUpdateNotifications ? 'translate-x-5' : 'translate-x-0',
                      'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out'
                    ]"
                  />
                </button>
              </div>

              <!-- Enable Manual Refresh -->
              <div class="flex items-center justify-between">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Enable Manual Refresh Button
                  </label>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    Show manual refresh button on manga details pages
                  </p>
                </div>
                <button
                  @click="chapterEnableManualRefresh = !chapterEnableManualRefresh"
                  :class="[
                    chapterEnableManualRefresh ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700',
                    'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2'
                  ]"
                >
                  <span
                    :class="[
                      chapterEnableManualRefresh ? 'translate-x-5' : 'translate-x-0',
                      'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out'
                    ]"
                  />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Save Button (shown for all tabs) -->
        <div
          class="pt-6 border-t border-gray-200 dark:border-dark-600 flex justify-end"
        >
          <button
            @click="saveSettings"
            :disabled="loading"
            class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              v-if="loading"
              class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
            Save Settings
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useSettingsStore } from "../stores/settings";
import ProviderPreferences from "../components/ProviderPreferences.vue";
import IntegrationSettings from "../components/IntegrationSettings.vue";
import BackupManager from "../components/BackupManager.vue";
import StorageRecovery from "../components/StorageRecovery.vue";

const route = useRoute();
const settingsStore = useSettingsStore();

// Tab management
const activeTab = ref("general");
const tabs = ref([
  { id: "general", name: "General" },
  { id: "integrations", name: "Integrations" },
  { id: "media", name: "Media Management" },
  { id: "ui", name: "UI" },
  { id: "backup", name: "Backup & Recovery" },
  { id: "downloads", name: "Downloads" },
]);

// Local state
const theme = ref(settingsStore.getTheme);
const nsfwBlur = ref(settingsStore.getNsfwBlur);
const downloadQuality = ref(settingsStore.getDownloadQuality);
const downloadPath = ref(settingsStore.getDownloadPath);

// Naming settings
const namingFormatManga = ref(
  "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}",
);
const namingFormatChapter = ref("{Chapter Number} - {Chapter Name}");
const autoOrganizeImports = ref(true);
const createCbzFiles = ref(true);
const preserveOriginalFiles = ref(false);

// Chapter update settings
const chapterAutoRefreshInterval = ref(settingsStore.getChapterAutoRefreshInterval);
const chapterCheckOnTabFocus = ref(settingsStore.getChapterCheckOnTabFocus);
const chapterShowUpdateNotifications = ref(settingsStore.getChapterShowUpdateNotifications);
const chapterEnableManualRefresh = ref(settingsStore.getChapterEnableManualRefresh);

// Storage settings
const storageType = ref(settingsStore.getStorageType);
const maxUploadSize = ref(settingsStore.getMaxUploadSize);

// Computed
const loading = computed(() => settingsStore.loading);
const error = computed(() => settingsStore.error);

// Naming previews
const mangaNamingPreview = computed(() => {
  if (!namingFormatManga.value) return "";
  return namingFormatManga.value
    .replace("{Manga Title}", "Naruto")
    .replace("{Volume}", "1")
    .replace("{Chapter Number}", "1")
    .replace("{Chapter Name}", "Enter Sasuke!")
    .replace("{Language}", "en")
    .replace("{Year}", "2023")
    .replace("{Source}", "mangadex");
});

const chapterNamingPreview = computed(() => {
  if (!namingFormatChapter.value) return "";
  return (
    namingFormatChapter.value
      .replace("{Chapter Number}", "1")
      .replace("{Chapter Name}", "Enter Sasuke!")
      .replace("{Language}", "en")
      .replace("{Year}", "2023")
      .replace("{Source}", "mangadex") + ".cbz"
  );
});

// Methods
const setTheme = (newTheme) => {
  theme.value = newTheme;
  settingsStore.setTheme(newTheme);
  console.log("Theme changed to:", newTheme);
};

const toggleNsfwBlur = () => {
  settingsStore.toggleNsfwBlur();
  nsfwBlur.value = settingsStore.getNsfwBlur;
};

const setDownloadQuality = (quality) => {
  downloadQuality.value = quality;
};

const browseDownloadPath = () => {
  console.log("Browse download path");
};

const resetDownloadPath = () => {
  downloadPath.value = "";
};

const toggleAutoOrganize = () => {
  autoOrganizeImports.value = !autoOrganizeImports.value;
};

const toggleCreateCbz = () => {
  createCbzFiles.value = !createCbzFiles.value;
};

const togglePreserveOriginal = () => {
  preserveOriginalFiles.value = !preserveOriginalFiles.value;
};

const saveSettings = async () => {
  settingsStore.setTheme(theme.value);
  settingsStore.setNsfwBlur(nsfwBlur.value);
  settingsStore.setDownloadQuality(downloadQuality.value);
  settingsStore.setDownloadPath(downloadPath.value);

  settingsStore.setNamingSettings({
    namingFormatManga: namingFormatManga.value,
    namingFormatChapter: namingFormatChapter.value,
    autoOrganizeImports: autoOrganizeImports.value,
    createCbzFiles: createCbzFiles.value,
    preserveOriginalFiles: preserveOriginalFiles.value,
  });

  settingsStore.setChapterUpdateSettings({
    chapterAutoRefreshInterval: chapterAutoRefreshInterval.value,
    chapterCheckOnTabFocus: chapterCheckOnTabFocus.value,
    chapterShowUpdateNotifications: chapterShowUpdateNotifications.value,
    chapterEnableManualRefresh: chapterEnableManualRefresh.value,
  });

  // Update storage settings
  settingsStore.setStorageType(storageType.value);
  settingsStore.setMaxUploadSize(maxUploadSize.value);

  await settingsStore.updateUserSettings();
};

onMounted(async () => {
  // Check for tab query parameter
  const tabParam = route.query.tab;
  if (tabParam && tabs.value.some((tab) => tab.id === tabParam)) {
    activeTab.value = tabParam;
  }

  theme.value = settingsStore.getTheme;
  nsfwBlur.value = settingsStore.getNsfwBlur;
  downloadQuality.value = settingsStore.getDownloadQuality;
  downloadPath.value = settingsStore.getDownloadPath;

  namingFormatManga.value =
    settingsStore.getNamingFormatManga ||
    "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}";
  namingFormatChapter.value =
    settingsStore.getNamingFormatChapter || "{Chapter Number} - {Chapter Name}";
  autoOrganizeImports.value = settingsStore.getAutoOrganizeImports ?? true;
  createCbzFiles.value = settingsStore.getCreateCbzFiles ?? true;
  preserveOriginalFiles.value = settingsStore.getPreserveOriginalFiles ?? false;

  // Load chapter update settings
  chapterAutoRefreshInterval.value = settingsStore.getChapterAutoRefreshInterval;
  chapterCheckOnTabFocus.value = settingsStore.getChapterCheckOnTabFocus;
  chapterShowUpdateNotifications.value = settingsStore.getChapterShowUpdateNotifications;
  chapterEnableManualRefresh.value = settingsStore.getChapterEnableManualRefresh;

  try {
    await settingsStore.fetchUserSettings();
    theme.value = settingsStore.getTheme;
    nsfwBlur.value = settingsStore.getNsfwBlur;
    downloadQuality.value = settingsStore.getDownloadQuality;
    downloadPath.value = settingsStore.getDownloadPath;

    namingFormatManga.value =
      settingsStore.getNamingFormatManga || namingFormatManga.value;
    namingFormatChapter.value =
      settingsStore.getNamingFormatChapter || namingFormatChapter.value;
    autoOrganizeImports.value =
      settingsStore.getAutoOrganizeImports ?? autoOrganizeImports.value;
    createCbzFiles.value =
      settingsStore.getCreateCbzFiles ?? createCbzFiles.value;
    preserveOriginalFiles.value =
      settingsStore.getPreserveOriginalFiles ?? preserveOriginalFiles.value;

    // Update chapter update settings from server
    chapterAutoRefreshInterval.value = settingsStore.getChapterAutoRefreshInterval;
    chapterCheckOnTabFocus.value = settingsStore.getChapterCheckOnTabFocus;
    chapterShowUpdateNotifications.value = settingsStore.getChapterShowUpdateNotifications;
    chapterEnableManualRefresh.value = settingsStore.getChapterEnableManualRefresh;
  } catch (error) {
    console.log(
      "Could not fetch user settings from backend, using local storage values",
    );
  }
});
</script>
