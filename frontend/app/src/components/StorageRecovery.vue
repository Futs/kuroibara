<template>
  <div class="storage-recovery">
    <!-- Section Header -->
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        Storage Recovery
      </h2>
      <p class="text-gray-600 dark:text-gray-400">
        Recover manga from storage that aren't in your database
      </p>
    </div>

    <div class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">

      <div class="border-t border-gray-200 dark:border-dark-600">
        <!-- Scan Button -->
        <div class="px-4 py-4 border-b border-gray-200 dark:border-dark-600">
          <button
            @click="scanStorage"
            :disabled="loading"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
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
            <svg
              v-else
              class="h-4 w-4 mr-2"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            {{ loading ? "Scanning..." : "Scan Storage" }}
          </button>

          <button
            v-if="recoverableManga.length > 0"
            @click="recoverAll"
            :disabled="recovering"
            class="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              v-if="recovering"
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
            {{
              recovering
                ? "Recovering..."
                : `Recover All (${recoverableManga.length})`
            }}
          </button>
        </div>

        <!-- Error Display -->
        <div
          v-if="error"
          class="px-4 py-3 bg-red-50 dark:bg-red-900 border-b border-red-200 dark:border-red-700"
        >
          <div class="flex">
            <div class="flex-shrink-0">
              <svg
                class="h-5 w-5 text-red-400"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <div class="ml-3">
              <p class="text-sm text-red-800 dark:text-red-200">{{ error }}</p>
            </div>
          </div>
        </div>

        <!-- Success Display -->
        <div
          v-if="successMessage"
          class="px-4 py-3 bg-green-50 dark:bg-green-900 border-b border-green-200 dark:border-green-700"
        >
          <div class="flex">
            <div class="flex-shrink-0">
              <svg
                class="h-5 w-5 text-green-400"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <div class="ml-3">
              <p class="text-sm text-green-800 dark:text-green-200">
                {{ successMessage }}
              </p>
            </div>
          </div>
        </div>

        <!-- Recoverable Manga List -->
        <div
          v-if="recoverableManga.length > 0"
          class="divide-y divide-gray-200 dark:divide-dark-600"
        >
          <div
            v-for="manga in recoverableManga"
            :key="manga.storage_uuid"
            class="px-4 py-4 hover:bg-gray-50 dark:hover:bg-dark-700"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center">
                  <h3
                    class="text-lg font-medium text-gray-900 dark:text-white truncate"
                  >
                    {{ manga.extracted_title }}
                  </h3>
                  <span
                    v-if="manga.has_volume_structure"
                    class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                  >
                    Volumes
                  </span>
                </div>

                <div
                  class="mt-1 flex items-center text-sm text-gray-500 dark:text-gray-400"
                >
                  <span>{{ manga.chapter_count }} chapters</span>
                  <span class="mx-2">•</span>
                  <span>{{ manga.volume_count }} volumes</span>
                  <span class="mx-2">•</span>
                  <span>{{ formatFileSize(manga.storage_size) }}</span>
                </div>

                <div class="mt-2">
                  <p class="text-xs text-gray-400 dark:text-gray-500 font-mono">
                    UUID: {{ manga.storage_uuid }}
                  </p>
                </div>
              </div>

              <div class="ml-4 flex-shrink-0">
                <button
                  @click="recoverSingle(manga)"
                  :disabled="recovering"
                  class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg
                    class="h-4 w-4 mr-1"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                    />
                  </svg>
                  Recover
                </button>
              </div>
            </div>

            <!-- Volume Details (Expandable) -->
            <div
              v-if="expandedManga === manga.storage_uuid"
              class="mt-4 pl-4 border-l-2 border-gray-200 dark:border-dark-600"
            >
              <div
                v-for="(chapters, volumeName) in manga.volumes"
                :key="volumeName"
                class="mb-3"
              >
                <h4
                  class="text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  {{ volumeName }}
                </h4>
                <div
                  class="mt-1 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-1"
                >
                  <div
                    v-for="chapter in chapters.slice(0, 6)"
                    :key="chapter.filename"
                    class="text-xs text-gray-500 dark:text-gray-400 truncate"
                  >
                    {{ chapter.number }} - {{ chapter.title }}
                  </div>
                  <div
                    v-if="chapters.length > 6"
                    class="text-xs text-gray-400 dark:text-gray-500"
                  >
                    ... and {{ chapters.length - 6 }} more
                  </div>
                </div>
              </div>
            </div>

            <div class="mt-2">
              <button
                @click="toggleExpanded(manga.storage_uuid)"
                class="text-xs text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
              >
                {{
                  expandedManga === manga.storage_uuid
                    ? "Hide Details"
                    : "Show Details"
                }}
              </button>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="!loading && scanned" class="px-4 py-8 text-center">
          <svg
            class="mx-auto h-12 w-12 text-gray-400"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            No recoverable manga found
          </h3>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            All manga in storage appear to be properly registered in the
            database.
          </p>
        </div>

        <!-- Initial State -->
        <div v-else-if="!loading && !scanned" class="px-4 py-8 text-center">
          <svg
            class="mx-auto h-12 w-12 text-gray-400"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            Storage Recovery
          </h3>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Click "Scan Storage" to search for manga that can be recovered from
            storage.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import api from "@/services/api.js";

// Reactive state
const loading = ref(false);
const recovering = ref(false);
const scanned = ref(false);
const recoverableManga = ref([]);
const expandedManga = ref(null);
const error = ref(null);
const successMessage = ref(null);

// Methods
const scanStorage = async () => {
  loading.value = true;
  error.value = null;
  successMessage.value = null;

  try {
    const response = await api.get("/v1/organizer/recovery/scan-storage");
    recoverableManga.value = response.data;
    scanned.value = true;

    if (recoverableManga.value.length === 0) {
      successMessage.value =
        "No recoverable manga found. All manga appear to be properly registered.";
    } else {
      successMessage.value = `Found ${recoverableManga.value.length} manga that can be recovered.`;
    }
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to scan storage";
    console.error("Storage scan error:", err);
  } finally {
    loading.value = false;
  }
};

const recoverSingle = async (manga) => {
  recovering.value = true;
  error.value = null;

  try {
    const response = await api.post("/v1/organizer/recovery/recover-manga", {
      storage_uuid: manga.storage_uuid,
      manga_title: manga.extracted_title,
      custom_metadata: manga.metadata,
    });

    if (response.data.success) {
      successMessage.value = response.data.message;
      // Remove from recoverable list
      recoverableManga.value = recoverableManga.value.filter(
        (m) => m.storage_uuid !== manga.storage_uuid,
      );
    } else {
      error.value = response.data.message;
    }
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to recover manga";
    console.error("Recovery error:", err);
  } finally {
    recovering.value = false;
  }
};

const recoverAll = async () => {
  recovering.value = true;
  error.value = null;

  try {
    const recoveryItems = recoverableManga.value.map((manga) => ({
      storage_uuid: manga.storage_uuid,
      manga_title: manga.extracted_title,
      custom_metadata: manga.metadata,
    }));

    const response = await api.post("/v1/organizer/recovery/batch-recover", {
      recovery_items: recoveryItems,
      skip_errors: true,
    });

    const result = response.data;
    successMessage.value = `Recovery completed: ${result.successful_recoveries} successful, ${result.failed_recoveries} failed`;

    if (result.failed_recoveries > 0) {
      error.value = `Some recoveries failed: ${result.errors.join(", ")}`;
    }

    // Clear the list since we attempted to recover all
    recoverableManga.value = [];
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to recover manga";
    console.error("Batch recovery error:", err);
  } finally {
    recovering.value = false;
  }
};

const toggleExpanded = (uuid) => {
  expandedManga.value = expandedManga.value === uuid ? null : uuid;
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// Clear messages after 5 seconds
const clearMessages = () => {
  setTimeout(() => {
    error.value = null;
    successMessage.value = null;
  }, 5000);
};

// Watch for message changes to auto-clear
import { watch } from "vue";
watch([error, successMessage], () => {
  if (error.value || successMessage.value) {
    clearMessages();
  }
});
</script>
