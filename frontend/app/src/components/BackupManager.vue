<template>
  <div class="backup-manager">
    <!-- Section Header -->
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        Backup Management
      </h2>
      <p class="text-gray-600 dark:text-gray-400">
        Create, download, and restore backups of your manga library
      </p>
    </div>

    <div class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">

      <div class="border-t border-gray-200 dark:border-dark-600">
        <!-- Action Buttons -->
        <div class="px-4 py-4 border-b border-gray-200 dark:border-dark-600">
          <div class="flex flex-wrap gap-3">
            <button
              @click="createBackup"
              :disabled="loading"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
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
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Create Backup
            </button>

            <button
              @click="refreshBackups"
              :disabled="loading"
              class="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-dark-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-700 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
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
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Refresh
            </button>

            <label
              class="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-dark-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-700 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 cursor-pointer"
            >
              <svg
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
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              Upload & Restore
              <input
                type="file"
                accept=".tar.gz"
                @change="handleFileUpload"
                class="hidden"
                ref="fileInput"
              />
            </label>
          </div>
        </div>

        <!-- Status Messages -->
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

        <!-- Backup Statistics -->
        <div
          v-if="backupList"
          class="px-4 py-3 bg-gray-50 dark:bg-dark-700 border-b border-gray-200 dark:border-dark-600"
        >
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
            <div>
              <span class="font-medium text-gray-900 dark:text-white"
                >Total Backups:</span
              >
              <span class="ml-1 text-gray-600 dark:text-gray-300">{{
                backupList.total_count
              }}</span>
            </div>
            <div>
              <span class="font-medium text-gray-900 dark:text-white"
                >Total Size:</span
              >
              <span class="ml-1 text-gray-600 dark:text-gray-300">{{
                formatFileSize(backupList.total_size)
              }}</span>
            </div>
            <div>
              <span class="font-medium text-gray-900 dark:text-white"
                >Latest:</span
              >
              <span class="ml-1 text-gray-600 dark:text-gray-300">
                {{
                  backupList.backups.length > 0
                    ? formatDate(backupList.backups[0].created_at)
                    : "None"
                }}
              </span>
            </div>
          </div>
        </div>

        <!-- Retention Policy Section -->
        <div
          class="px-4 py-4 bg-yellow-50 dark:bg-yellow-900/20 border-b border-gray-200 dark:border-dark-600"
        >
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">
              Backup Retention Policy
            </h3>
            <button
              @click="applyRetentionPolicy"
              :disabled="loading"
              class="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-yellow-700 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-yellow-800 dark:text-yellow-200 dark:hover:bg-yellow-700"
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
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              Clean Up Now
            </button>
          </div>

          <div
            v-if="retentionSettings"
            class="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs"
          >
            <div class="text-center p-2 bg-white dark:bg-dark-800 rounded">
              <div class="font-medium text-gray-900 dark:text-white">Daily</div>
              <div class="text-gray-600 dark:text-gray-300">
                {{ retentionSettings.retention_daily }}
              </div>
            </div>
            <div class="text-center p-2 bg-white dark:bg-dark-800 rounded">
              <div class="font-medium text-gray-900 dark:text-white">
                Weekly
              </div>
              <div class="text-gray-600 dark:text-gray-300">
                {{ retentionSettings.retention_weekly }}
              </div>
            </div>
            <div class="text-center p-2 bg-white dark:bg-dark-800 rounded">
              <div class="font-medium text-gray-900 dark:text-white">
                Monthly
              </div>
              <div class="text-gray-600 dark:text-gray-300">
                {{ retentionSettings.retention_monthly }}
              </div>
            </div>
            <div class="text-center p-2 bg-white dark:bg-dark-800 rounded">
              <div class="font-medium text-gray-900 dark:text-white">
                Yearly
              </div>
              <div class="text-gray-600 dark:text-gray-300">
                {{ retentionSettings.retention_yearly }}
              </div>
            </div>
            <div class="text-center p-2 bg-white dark:bg-dark-800 rounded">
              <div class="font-medium text-gray-900 dark:text-white">
                Max Total
              </div>
              <div class="text-gray-600 dark:text-gray-300">
                {{ retentionSettings.retention_max_total }}
              </div>
            </div>
          </div>

          <div
            v-if="retentionResult"
            class="mt-3 p-2 bg-green-100 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded text-sm"
          >
            <div class="text-green-800 dark:text-green-200">
              {{
                retentionResult.message ||
                `Cleaned up ${retentionResult.deleted_count} old backups`
              }}
            </div>
            <div
              v-if="
                retentionResult.deleted_files &&
                retentionResult.deleted_files.length > 0
              "
              class="mt-1 text-xs text-green-600 dark:text-green-300"
            >
              Deleted: {{ retentionResult.deleted_files.join(", ") }}
            </div>
          </div>
        </div>

        <!-- Backup List -->
        <div
          v-if="backupList && backupList.backups.length > 0"
          class="divide-y divide-gray-200 dark:divide-dark-600"
        >
          <div
            v-for="backup in backupList.backups"
            :key="backup.filename"
            class="px-4 py-4 hover:bg-gray-50 dark:hover:bg-dark-700"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center">
                  <h3
                    class="text-sm font-medium text-gray-900 dark:text-white truncate"
                  >
                    {{ backup.filename }}
                  </h3>
                  <span
                    v-if="backup.includes_storage"
                    class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                  >
                    Full Backup
                  </span>
                  <span
                    v-else
                    class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                  >
                    Database Only
                  </span>
                </div>

                <div
                  class="mt-1 flex items-center text-xs text-gray-500 dark:text-gray-400"
                >
                  <span>{{ formatFileSize(backup.size) }}</span>
                  <span class="mx-2">•</span>
                  <span>{{ formatDate(backup.created_at) }}</span>
                  <span v-if="backup.metadata" class="mx-2">•</span>
                  <span v-if="backup.metadata"
                    >v{{ backup.metadata.kuroibara_version }}</span
                  >
                </div>
              </div>

              <div class="ml-4 flex-shrink-0 flex space-x-2">
                <button
                  @click="downloadBackup(backup)"
                  class="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-primary-700 bg-primary-100 hover:bg-primary-200 dark:bg-primary-900 dark:text-primary-200 dark:hover:bg-primary-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
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
                      d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  Download
                </button>

                <button
                  @click="deleteBackup(backup)"
                  class="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
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
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="!loading && backupList" class="px-4 py-8 text-center">
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
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            No backups found
          </h3>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Create your first backup to get started.
          </p>
        </div>

        <!-- Loading State -->
        <div v-else-if="loading" class="px-4 py-8 text-center">
          <svg
            class="animate-spin mx-auto h-8 w-8 text-gray-400"
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
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Loading backups...
          </p>
        </div>
      </div>
    </div>

    <!-- Create Backup Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
      @click="showCreateModal = false"
    >
      <div
        class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-dark-800"
        @click.stop
      >
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">
            Create Backup
          </h3>
          <div class="mt-4 space-y-4">
            <div>
              <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >Backup Name (optional)</label
              >
              <input
                v-model="newBackupName"
                type="text"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white"
                placeholder="Leave empty for auto-generated name"
              />
            </div>

            <div class="flex items-center">
              <input
                v-model="includeStorage"
                type="checkbox"
                class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label class="ml-2 block text-sm text-gray-900 dark:text-white">
                Include storage files (larger backup, longer time)
              </label>
            </div>
          </div>

          <div class="mt-6 flex justify-end space-x-3">
            <button
              @click="showCreateModal = false"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-dark-600 hover:bg-gray-200 dark:hover:bg-dark-500 rounded-md"
            >
              Cancel
            </button>
            <button
              @click="confirmCreateBackup"
              :disabled="creating"
              class="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-md disabled:opacity-50"
            >
              {{ creating ? "Creating..." : "Create Backup" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/services/api.js";

// Reactive state
const loading = ref(false);
const creating = ref(false);
const backupList = ref(null);
const error = ref(null);
const successMessage = ref(null);
const showCreateModal = ref(false);
const newBackupName = ref("");
const includeStorage = ref(true);
const fileInput = ref(null);
const retentionSettings = ref(null);
const retentionResult = ref(null);

// Methods
const refreshBackups = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await api.get("/v1/backup/list");
    backupList.value = response.data;
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to load backups";
    console.error("Backup list error:", err);
  } finally {
    loading.value = false;
  }
};

const createBackup = () => {
  showCreateModal.value = true;
  newBackupName.value = "";
  includeStorage.value = true;
};

const confirmCreateBackup = async () => {
  creating.value = true;
  error.value = null;

  try {
    const response = await api.post("/v1/backup/create", {
      backup_name: newBackupName.value || null,
      include_storage: includeStorage.value,
    });

    successMessage.value = response.data.message;
    showCreateModal.value = false;

    // Refresh list after a delay to show the new backup
    setTimeout(() => {
      refreshBackups();
    }, 2000);
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to create backup";
    console.error("Backup creation error:", err);
  } finally {
    creating.value = false;
  }
};

const downloadBackup = async (backup) => {
  try {
    const response = await api.get(`/v1/backup/download/${backup.filename}`, {
      responseType: "blob",
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", backup.filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    successMessage.value = `Downloaded ${backup.filename}`;
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to download backup";
    console.error("Backup download error:", err);
  }
};

const deleteBackup = async (backup) => {
  if (
    !confirm(
      `Are you sure you want to delete backup "${backup.filename}"? This action cannot be undone.`,
    )
  ) {
    return;
  }

  try {
    await api.delete(`/v1/backup/delete/${backup.filename}`);
    successMessage.value = `Deleted ${backup.filename}`;
    refreshBackups();
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to delete backup";
    console.error("Backup deletion error:", err);
  }
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  if (!file.name.endsWith(".tar.gz")) {
    error.value = "Please select a valid backup file (.tar.gz)";
    return;
  }

  if (
    !confirm(
      "This will restore the backup and overwrite all current data. Are you sure you want to continue?",
    )
  ) {
    fileInput.value.value = "";
    return;
  }

  const formData = new FormData();
  formData.append("backup_file", file);

  try {
    loading.value = true;
    const response = await api.post("/v1/backup/upload-restore", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    successMessage.value = response.data.message;

    // Clear file input
    fileInput.value.value = "";
  } catch (err) {
    error.value =
      err.response?.data?.detail || "Failed to upload and restore backup";
    console.error("Backup restore error:", err);
  } finally {
    loading.value = false;
  }
};

const loadRetentionSettings = async () => {
  try {
    const response = await api.get("/v1/backup/retention-settings");
    retentionSettings.value = response.data;
  } catch (err) {
    console.error("Failed to load retention settings:", err);
  }
};

const applyRetentionPolicy = async () => {
  loading.value = true;
  error.value = null;
  retentionResult.value = null;

  try {
    const response = await api.post("/v1/backup/apply-retention");
    retentionResult.value = response.data;

    // Refresh backup list to show updated counts
    await refreshBackups();

    // Clear result after 10 seconds
    setTimeout(() => {
      retentionResult.value = null;
    }, 10000);
  } catch (err) {
    console.error("Failed to apply retention policy:", err);
    error.value =
      err.response?.data?.detail || "Failed to apply retention policy";
  } finally {
    loading.value = false;
  }
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
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

// Load backups on mount
onMounted(() => {
  refreshBackups();
  loadRetentionSettings();
});
</script>
