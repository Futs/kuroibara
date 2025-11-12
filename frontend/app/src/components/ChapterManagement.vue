<template>
  <div
    class="bg-white dark:bg-dark-800 border border-gray-200 dark:border-dark-600 rounded-lg p-4 mb-6"
  >
    <!-- Management Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-medium text-gray-900 dark:text-white">
        Chapter Management
      </h3>
      <div class="flex space-x-2">
        <button
          @click="organizeChapters"
          :disabled="organizing"
          class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg
            v-if="organizing"
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
              d="M4 6h16M4 12h16M4 18h7"
            />
          </svg>
          {{ organizing ? "Organizing..." : "Organize Chapters" }}
        </button>
        <button
          @click="showRenameDialog = true"
          class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
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
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            />
          </svg>
          Rename Chapters
        </button>
      </div>
    </div>

    <!-- Organization Results -->
    <div
      v-if="organizationResults"
      class="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md"
    >
      <div class="flex">
        <div class="flex-shrink-0">
          <svg
            class="h-5 w-5 text-blue-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-blue-800 dark:text-blue-200">
            Organization Complete
          </h3>
          <div class="mt-2 text-sm text-blue-700 dark:text-blue-300">
            <p>{{ organizationResults.message }}</p>
            <ul
              v-if="organizationResults.changes.length > 0"
              class="mt-2 list-disc list-inside"
            >
              <li
                v-for="change in organizationResults.changes"
                :key="change.id"
              >
                {{ change.description }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Rename Dialog -->
    <div
      v-if="showRenameDialog"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
      @click="showRenameDialog = false"
    >
      <div
        class="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white dark:bg-dark-800"
        @click.stop
      >
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Rename Chapters
          </h3>

          <div class="space-y-4 max-h-96 overflow-y-auto">
            <div
              v-for="chapter in chapters"
              :key="chapter.id"
              class="flex items-center space-x-3 p-3 border border-gray-200 dark:border-dark-600 rounded-md"
            >
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-900 dark:text-white">
                  Chapter {{ chapter.number }}
                </p>
                <input
                  v-model="chapter.newTitle"
                  :placeholder="chapter.title || 'Enter chapter title'"
                  class="mt-1 block w-full border-gray-300 dark:border-dark-600 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white text-sm"
                />
              </div>
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button
              @click="showRenameDialog = false"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-700 border border-gray-300 dark:border-dark-600 rounded-md hover:bg-white dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Cancel
            </button>
            <button
              @click="applyRenames"
              :disabled="renaming"
              class="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ renaming ? "Applying..." : "Apply Changes" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import api from "../services/api";

const props = defineProps({
  mangaId: {
    type: String,
    required: true,
  },
  chapters: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(["chapters-updated"]);
const organizing = ref(false);
const renaming = ref(false);
const showRenameDialog = ref(false);
const organizationResults = ref(null);

// Create a reactive copy of chapters for editing
const editableChapters = ref([]);

onMounted(() => {
  resetEditableChapters();
});

const resetEditableChapters = () => {
  editableChapters.value = props.chapters.map((chapter) => ({
    ...chapter,
    newTitle: chapter.title || "",
  }));
};

const organizeChapters = async () => {
  organizing.value = true;
  organizationResults.value = null;

  try {
    const response = await api.post(
      `/v1/manga/${props.mangaId}/organize-chapters`,
    );
    organizationResults.value = response.data;
    emit("chapters-updated");
  } catch (error) {
    console.error("Error organizing chapters:", error);
    organizationResults.value = {
      message:
        "Failed to organize chapters: " +
        (error.response?.data?.detail || error.message),
      changes: [],
    };
  } finally {
    organizing.value = false;
  }
};

const applyRenames = async () => {
  renaming.value = true;

  try {
    const updates = editableChapters.value
      .filter((chapter) => chapter.newTitle !== chapter.title)
      .map((chapter) => ({
        id: chapter.id,
        title: chapter.newTitle,
      }));

    if (updates.length === 0) {
      showRenameDialog.value = false;
      return;
    }

    await api.patch(`/v1/manga/${props.mangaId}/chapters/batch-update`, {
      updates,
    });

    showRenameDialog.value = false;
    emit("chapters-updated");
  } catch (error) {
    console.error("Error renaming chapters:", error);
    alert(
      "Failed to rename chapters: " +
        (error.response?.data?.detail || error.message),
    );
  } finally {
    renaming.value = false;
  }
};
</script>

<style scoped>
/* Styles moved to inline Tailwind classes */
</style>
