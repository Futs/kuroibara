<template>
  <div class="bg-white dark:bg-dark-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
    <div class="sm:flex sm:items-start">
      <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
        <h3
          class="text-lg leading-6 font-medium text-gray-900 dark:text-white"
          id="modal-title"
        >
          {{ props.manga ? `Import Files for "${getMangaTitle}"` : 'Import Manga' }}
        </h3>
        <div class="mt-4">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
            {{ props.manga
              ? `Import additional chapters or volumes for "${getMangaTitle}".`
              : 'Import manga from CBZ/CBR archives or directories containing images.'
            }}
          </p>

          <!-- File Upload Area -->
          <div
            @drop="handleDrop"
            @dragover.prevent
            @dragenter.prevent
            class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-primary-500 dark:hover:border-primary-400 transition-colors"
            :class="{ 'border-primary-500 dark:border-primary-400': isDragging }"
          >
            <svg
              class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            <div class="mt-4">
              <label for="file-upload" class="cursor-pointer">
                <span class="mt-2 block text-sm font-medium text-gray-900 dark:text-white">
                  Drop files here or click to browse
                </span>
                <input
                  id="file-upload"
                  name="file-upload"
                  type="file"
                  class="sr-only"
                  multiple
                  accept=".cbz,.cbr,.zip,.rar,.7z"
                  @change="handleFileSelect"
                />
              </label>
              <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                CBZ, CBR, ZIP, RAR, 7Z files up to 100MB each
              </p>
            </div>
          </div>

          <!-- Selected Files List -->
          <div v-if="selectedFiles.length > 0" class="mt-4">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
              Selected Files ({{ selectedFiles.length }})
            </h4>
            <div class="max-h-40 overflow-y-auto">
              <div
                v-for="(file, index) in selectedFiles"
                :key="index"
                class="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-dark-700 rounded-md mb-2"
              >
                <div class="flex items-center">
                  <svg
                    class="h-5 w-5 text-gray-400 dark:text-gray-500 mr-2"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
                      clip-rule="evenodd"
                    />
                  </svg>
                  <span class="text-sm text-gray-900 dark:text-white truncate">
                    {{ file.name }}
                  </span>
                  <span class="text-xs text-gray-500 dark:text-gray-400 ml-2">
                    ({{ formatFileSize(file.size) }})
                  </span>
                </div>
                <button
                  @click="removeFile(index)"
                  class="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                >
                  <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fill-rule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Import Options -->
          <div v-if="selectedFiles.length > 0" class="mt-4">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
              Import Options
            </h4>
            <div class="space-y-2">
              <label class="flex items-center">
                <input
                  type="checkbox"
                  v-model="importOptions.extractMetadata"
                  class="rounded border-gray-300 dark:border-gray-600 text-primary-600 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Extract metadata from files
                </span>
              </label>
              <label class="flex items-center">
                <input
                  type="checkbox"
                  v-model="importOptions.createSeparateManga"
                  class="rounded border-gray-300 dark:border-gray-600 text-primary-600 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Create separate manga for each file
                </span>
              </label>
            </div>
          </div>

          <!-- Duplicate Warning -->
          <div v-if="duplicateWarning" class="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="ml-3">
                <h3 class="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Chapter Already Exists
                </h3>
                <div class="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
                  <p>{{ duplicateWarning.message }}</p>
                  <p class="mt-1">Would you like to replace the existing chapter?</p>
                </div>
                <div class="mt-4">
                  <div class="flex space-x-2">
                    <button
                      @click="proceedWithReplace"
                      class="bg-yellow-600 hover:bg-yellow-700 text-white text-xs font-medium py-1 px-3 rounded"
                    >
                      Replace Existing
                    </button>
                    <button
                      @click="skipDuplicate"
                      class="bg-gray-600 hover:bg-gray-700 text-white text-xs font-medium py-1 px-3 rounded"
                    >
                      Skip This File
                    </button>
                    <button
                      @click="cancelImport"
                      class="bg-red-600 hover:bg-red-700 text-white text-xs font-medium py-1 px-3 rounded"
                    >
                      Cancel Import
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Progress Bar -->
          <div v-if="importing" class="mt-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Importing... {{ importProgress.current }}/{{ importProgress.total }}
              </span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                {{ Math.round((importProgress.current / importProgress.total) * 100) }}%
              </span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                class="bg-primary-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${(importProgress.current / importProgress.total) * 100}%` }"
              ></div>
            </div>
          </div>

          <!-- Error Messages -->
          <div v-if="errors.length > 0" class="mt-4">
            <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
              <div class="flex">
                <svg
                  class="h-5 w-5 text-red-400 dark:text-red-300"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clip-rule="evenodd"
                  />
                </svg>
                <div class="ml-3">
                  <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
                    Import Errors
                  </h3>
                  <div class="mt-2 text-sm text-red-700 dark:text-red-300">
                    <ul class="list-disc pl-5 space-y-1">
                      <li v-for="error in errors" :key="error">{{ error }}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dialog Actions -->
    <div class="bg-gray-50 dark:bg-dark-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
      <button
        @click="startImport"
        :disabled="selectedFiles.length === 0 || importing"
        class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg
          v-if="importing"
          class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
        {{ importing ? 'Importing...' : 'Import' }}
      </button>
      <button
        @click="$emit('close')"
        :disabled="importing"
        class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-gray-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-800 text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ importing ? 'Cancel' : 'Close' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from "vue";
import api from "../services/api";

const props = defineProps({
  manga: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["close", "imported"]);

// Computed properties
const getMangaTitle = computed(() => {
  if (!props.manga) return '';
  return props.manga.title || props.manga.manga?.title || 'Unknown Title';
});

// Reactive data
const selectedFiles = ref([]);
const importing = ref(false);
const isDragging = ref(false);
const errors = ref([]);
const duplicateWarning = ref(null);
const currentFileIndex = ref(0);
const pendingImport = ref(null);

const importProgress = reactive({
  current: 0,
  total: 0,
});

const importOptions = reactive({
  extractMetadata: true,
  createSeparateManga: false,
});

// Methods
const handleDrop = (event) => {
  event.preventDefault();
  isDragging.value = false;
  const files = Array.from(event.dataTransfer.files);
  addFiles(files);
};

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files);
  addFiles(files);
};

const addFiles = (files) => {
  const validFiles = files.filter(file => {
    const validExtensions = ['.cbz', '.cbr', '.zip', '.rar', '.7z'];
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    return validExtensions.includes(extension) && file.size <= 100 * 1024 * 1024; // 100MB limit
  });
  
  selectedFiles.value.push(...validFiles);
  
  if (validFiles.length !== files.length) {
    errors.value.push("Some files were skipped (unsupported format or too large)");
  }
};

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1);
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Duplicate handling functions
const checkForDuplicate = async (file, chapterNumber) => {
  if (!props.manga) return false;

  try {
    const response = await api.get(`/v1/import/chapter/${props.manga.id}/check`, {
      params: {
        chapter_number: chapterNumber,
        language: 'en'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error checking for duplicate:', error);
    return false;
  }
};

const proceedWithReplace = async () => {
  if (pendingImport.value) {
    await importSingleFile(pendingImport.value.file, pendingImport.value.index, true);
    duplicateWarning.value = null;
    pendingImport.value = null;
    await continueImport();
  }
};

const skipDuplicate = async () => {
  if (pendingImport.value) {
    importProgress.current++;
    duplicateWarning.value = null;
    pendingImport.value = null;
    await continueImport();
  }
};

const cancelImport = () => {
  importing.value = false;
  duplicateWarning.value = null;
  pendingImport.value = null;
  importProgress.current = 0;
};

const continueImport = async () => {
  currentFileIndex.value++;
  if (currentFileIndex.value < selectedFiles.value.length) {
    await processNextFile();
  } else {
    // Import complete
    importing.value = false;
    if (errors.value.length === 0) {
      emit('imported');
    }
  }
};

const processNextFile = async () => {
  const file = selectedFiles.value[currentFileIndex.value];
  await importSingleFile(file, currentFileIndex.value, false);
};

const importSingleFile = async (file, index, replaceExisting = false) => {
  try {
    const formData = new FormData();

    if (props.manga) {
      // Import chapter for existing manga
      formData.append('chapter_file', file);
      formData.append('language', 'en');

      // Try to extract chapter info from filename
      const filename = file.name;
      const chapterMatch = filename.match(/ch\.?\s*(\d+(?:\.\d+)?)/i);
      const volumeMatch = filename.match(/vol\.?\s*(\d+)/i);

      // Extract chapter number (required field)
      let chapterNumber = '1'; // Default fallback
      if (chapterMatch) {
        chapterNumber = chapterMatch[1];
      } else {
        // Try to extract any number from filename as chapter number
        const numberMatch = filename.match(/(\d+(?:\.\d+)?)/);
        if (numberMatch) {
          chapterNumber = numberMatch[1];
        }
      }
      formData.append('chapter_number', chapterNumber);

      // Add volume if found
      if (volumeMatch) {
        formData.append('volume', volumeMatch[1]);
      }

      // Try to extract title from filename (remove extension and common patterns)
      let chapterTitle = filename.replace(/\.[^/.]+$/, ""); // Remove extension
      chapterTitle = chapterTitle.replace(/vol\.?\s*\d+/i, "").trim(); // Remove volume info
      chapterTitle = chapterTitle.replace(/ch\.?\s*\d+(?:\.\d+)?/i, "").trim(); // Remove chapter info
      chapterTitle = chapterTitle.replace(/^\s*-\s*/, "").trim(); // Remove leading dash
      if (chapterTitle) {
        formData.append('title', chapterTitle);
      }

      // Add replace_existing flag
      formData.append('replace_existing', replaceExisting.toString());

      // Check for duplicates if not replacing
      if (!replaceExisting) {
        const duplicateCheck = await checkForDuplicate(file, chapterNumber);
        if (duplicateCheck && duplicateCheck.exists) {
          // Show duplicate warning
          duplicateWarning.value = {
            message: `Chapter ${chapterNumber} already exists (${duplicateCheck.chapter.pages_count} pages, created ${new Date(duplicateCheck.chapter.created_at).toLocaleDateString()})`,
            file: file,
            chapterNumber: chapterNumber
          };
          pendingImport.value = { file, index };
          return; // Stop processing and wait for user decision
        }
      }

      await api.post(`/v1/import/chapter/${props.manga.id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    } else {
      // Import new manga
      formData.append('title', file.name.replace(/\.[^/.]+$/, "")); // Remove extension
      formData.append('cover', file);

      await api.post('/v1/import/manga', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    }

    importProgress.current++;
    await continueImport();
  } catch (error) {
    console.error(`Error importing ${file.name}:`, error);
    if (error.response?.status === 409) {
      // Conflict error (duplicate)
      errors.value.push(`Chapter already exists: ${file.name}`);
    } else {
      errors.value.push(`Failed to import ${file.name}: ${error.response?.data?.detail || error.message}`);
    }
    importProgress.current++;
    await continueImport();
  }
};

const startImport = async () => {
  if (selectedFiles.value.length === 0) return;

  importing.value = true;
  errors.value = [];
  duplicateWarning.value = null;
  importProgress.current = 0;
  importProgress.total = selectedFiles.value.length;
  currentFileIndex.value = 0;

  try {
    await processNextFile();
  } catch (error) {
    console.error('Import error:', error);
    errors.value.push('An unexpected error occurred during import');
    importing.value = false;
  }
};
</script>
