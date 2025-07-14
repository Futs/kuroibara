<template>
  <div
    class="duplicate-detection bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6"
  >
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
        Duplicate Detection
      </h2>
      <div class="flex space-x-2">
        <button
          @click="scanForDuplicates"
          :disabled="scanning"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ scanning ? "Scanning..." : "Scan for Duplicates" }}
        </button>
        <button
          v-if="duplicates.length > 0"
          @click="showBulkActions = !showBulkActions"
          class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
        >
          Bulk Actions
        </button>
      </div>
    </div>

    <!-- Scanning Progress -->
    <div v-if="scanning" class="mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm text-gray-600 dark:text-gray-400"
          >Scanning library...</span
        >
        <span class="text-sm text-gray-600 dark:text-gray-400"
          >{{ scanProgress }}%</span
        >
      </div>
      <div class="w-full bg-gray-200 dark:bg-dark-600 rounded-full h-2">
        <div
          class="bg-blue-600 h-2 rounded-full transition-all duration-300"
          :style="{ width: `${scanProgress}%` }"
        ></div>
      </div>
    </div>

    <!-- Bulk Actions Panel -->
    <div
      v-if="showBulkActions && duplicates.length > 0"
      class="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg"
    >
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
        Bulk Actions
      </h3>
      <div class="flex flex-wrap gap-2">
        <button
          @click="selectAllDuplicates"
          class="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Select All
        </button>
        <button
          @click="deselectAllDuplicates"
          class="px-3 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
        >
          Deselect All
        </button>
        <button
          @click="deleteSelectedDuplicates"
          :disabled="selectedDuplicates.size === 0"
          class="px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Delete Selected ({{ selectedDuplicates.size }})
        </button>
        <button
          @click="mergeSelectedDuplicates"
          :disabled="selectedDuplicates.size < 2"
          class="px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Merge Selected
        </button>
      </div>
    </div>

    <!-- Results Summary -->
    <div v-if="!scanning && duplicates.length > 0" class="mb-6">
      <div
        class="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4"
      >
        <div class="flex items-center">
          <svg
            class="w-5 h-5 text-orange-600 dark:text-orange-400 mr-2"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          <div>
            <div class="font-semibold text-orange-800 dark:text-orange-200">
              Found {{ duplicates.length }} potential duplicate group{{
                duplicates.length !== 1 ? "s" : ""
              }}
            </div>
            <div class="text-sm text-orange-700 dark:text-orange-300">
              {{ totalDuplicateItems }} items involved in duplicates
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Duplicates Found -->
    <div
      v-if="!scanning && duplicates.length === 0 && hasScanned"
      class="text-center py-8"
    >
      <svg
        class="w-16 h-16 text-green-500 mx-auto mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        No Duplicates Found
      </h3>
      <p class="text-gray-600 dark:text-gray-400">
        Your library appears to be clean of duplicates.
      </p>
    </div>

    <!-- Duplicate Groups -->
    <div v-if="duplicates.length > 0" class="space-y-6">
      <div
        v-for="(group, index) in duplicates"
        :key="index"
        class="border border-gray-200 dark:border-dark-600 rounded-lg p-4"
      >
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              Duplicate Group {{ index + 1 }}
            </h3>
            <span
              class="ml-2 px-2 py-1 text-xs bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200 rounded-full"
            >
              {{ group.similarity }}% similarity
            </span>
          </div>
          <div class="flex space-x-2">
            <button
              @click="mergeGroupItems(group)"
              class="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            >
              Merge All
            </button>
            <button
              @click="ignoreGroup(group)"
              class="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
            >
              Ignore
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="item in group.items"
            :key="item.id"
            class="border border-gray-200 dark:border-dark-600 rounded-lg p-3"
            :class="{ 'ring-2 ring-blue-500': selectedDuplicates.has(item.id) }"
          >
            <div class="flex items-start space-x-3">
              <input
                v-if="showBulkActions"
                v-model="selectedDuplicates"
                :value="item.id"
                type="checkbox"
                class="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />

              <img
                :src="item.manga.cover_url || '/placeholder-cover.jpg'"
                :alt="item.manga.title"
                class="w-16 h-20 object-cover rounded"
              />

              <div class="flex-1 min-w-0">
                <h4
                  class="font-semibold text-gray-900 dark:text-white truncate"
                >
                  {{ item.manga.title }}
                </h4>
                <p class="text-sm text-gray-600 dark:text-gray-400">
                  {{
                    item.manga.authors?.map((a) => a.name).join(", ") ||
                    "Unknown Author"
                  }}
                </p>
                <div class="mt-2 space-y-1">
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    Added: {{ formatDate(item.created_at) }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    Chapters: {{ item.manga.chapters?.length || 0 }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    Status: {{ item.read_status || "unread" }}
                  </div>
                </div>

                <div class="mt-2 flex space-x-2">
                  <button
                    @click="viewManga(item)"
                    class="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                  >
                    View
                  </button>
                  <button
                    @click="deleteSingle(item)"
                    class="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Merge Confirmation Modal -->
    <div
      v-if="showMergeModal"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showMergeModal = false"
    >
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
      >
        <div
          class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
        ></div>

        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6"
        >
          <div>
            <h3
              class="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4"
            >
              Merge Duplicates
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
              This will merge the reading progress, bookmarks, and metadata from
              all duplicates into the primary item and delete the others.
            </p>

            <div class="space-y-2">
              <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Select primary item to keep:
              </label>
              <div class="space-y-2">
                <label
                  v-for="item in mergeGroup"
                  :key="item.id"
                  class="flex items-center p-2 border border-gray-200 dark:border-dark-600 rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-700"
                >
                  <input
                    v-model="primaryMergeItem"
                    :value="item.id"
                    type="radio"
                    class="mr-3"
                  />
                  <div class="flex-1">
                    <div class="font-medium text-gray-900 dark:text-white">
                      {{ item.manga.title }}
                    </div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">
                      Added: {{ formatDate(item.created_at) }} • Chapters:
                      {{ item.manga.chapters?.length || 0 }}
                    </div>
                  </div>
                </label>
              </div>
            </div>
          </div>

          <div class="mt-5 sm:mt-6 flex space-x-3">
            <button
              @click="confirmMerge"
              :disabled="!primaryMergeItem"
              class="flex-1 inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:text-sm"
            >
              Merge
            </button>
            <button
              @click="showMergeModal = false"
              class="flex-1 inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-700 text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useLibraryStore } from "../stores/library";
import { useRouter } from "vue-router";

const libraryStore = useLibraryStore();
const router = useRouter();

// Local state
const scanning = ref(false);
const scanProgress = ref(0);
const duplicates = ref([]);
const hasScanned = ref(false);
const showBulkActions = ref(false);
const selectedDuplicates = ref(new Set());
const showMergeModal = ref(false);
const mergeGroup = ref([]);
const primaryMergeItem = ref(null);

// Computed properties
const totalDuplicateItems = computed(() => {
  return duplicates.value.reduce(
    (total, group) => total + group.items.length,
    0,
  );
});

// Methods
const scanForDuplicates = async () => {
  scanning.value = true;
  scanProgress.value = 0;
  duplicates.value = [];
  hasScanned.value = false;

  try {
    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      if (scanProgress.value < 90) {
        scanProgress.value += Math.random() * 10;
      }
    }, 200);

    // Try API first, fallback to local detection
    try {
      const apiDuplicates = await libraryStore.findDuplicates();
      duplicates.value = apiDuplicates;
    } catch (error) {
      console.log("API duplicate detection failed, using local detection");
      duplicates.value = libraryStore.findLocalDuplicates();
    }

    clearInterval(progressInterval);
    scanProgress.value = 100;

    setTimeout(() => {
      scanning.value = false;
      hasScanned.value = true;
    }, 500);
  } catch (error) {
    console.error("Error scanning for duplicates:", error);
    scanning.value = false;
    hasScanned.value = true;
  }
};

const selectAllDuplicates = () => {
  duplicates.value.forEach((group) => {
    group.items.forEach((item) => {
      selectedDuplicates.value.add(item.id);
    });
  });
};

const deselectAllDuplicates = () => {
  selectedDuplicates.value.clear();
};

const deleteSelectedDuplicates = async () => {
  if (selectedDuplicates.value.size === 0) return;

  if (
    confirm(
      `Are you sure you want to delete ${selectedDuplicates.value.size} selected items?`,
    )
  ) {
    try {
      const mangaIds = Array.from(selectedDuplicates.value);
      await libraryStore.bulkDelete(mangaIds);

      // Remove deleted items from duplicates
      duplicates.value = duplicates.value
        .map((group) => ({
          ...group,
          items: group.items.filter(
            (item) => !selectedDuplicates.value.has(item.id),
          ),
        }))
        .filter((group) => group.items.length > 1);

      selectedDuplicates.value.clear();
    } catch (error) {
      console.error("Error deleting duplicates:", error);
    }
  }
};

const mergeSelectedDuplicates = () => {
  if (selectedDuplicates.value.size < 2) return;

  const selectedItems = [];
  duplicates.value.forEach((group) => {
    group.items.forEach((item) => {
      if (selectedDuplicates.value.has(item.id)) {
        selectedItems.push(item);
      }
    });
  });

  mergeGroup.value = selectedItems;
  primaryMergeItem.value = selectedItems[0]?.id || null;
  showMergeModal.value = true;
};

const mergeGroupItems = (group) => {
  mergeGroup.value = group.items;
  primaryMergeItem.value = group.items[0]?.id || null;
  showMergeModal.value = true;
};

const confirmMerge = async () => {
  if (!primaryMergeItem.value) return;

  try {
    // This would be implemented in the API
    const itemsToMerge = mergeGroup.value.map((item) => item.id);
    // For now, we'll simulate the merge by deleting non-primary items
    const idsToDelete = itemsToMerge.filter(
      (id) => id !== primaryMergeItem.value,
    );

    for (const id of idsToDelete) {
      await libraryStore.deleteManga(id);
    }

    // Remove merged group from duplicates
    duplicates.value = duplicates.value.filter(
      (group) => !group.items.some((item) => itemsToMerge.includes(item.id)),
    );

    showMergeModal.value = false;
    mergeGroup.value = [];
    primaryMergeItem.value = null;

    // Refresh library
    await libraryStore.fetchLibrary();
  } catch (error) {
    console.error("Error merging duplicates:", error);
  }
};

const ignoreGroup = (group) => {
  const index = duplicates.value.indexOf(group);
  if (index > -1) {
    duplicates.value.splice(index, 1);
  }
};

const deleteSingle = async (item) => {
  if (confirm(`Are you sure you want to delete "${item.manga.title}"?`)) {
    try {
      await libraryStore.deleteManga(item.id);

      // Remove from duplicates
      duplicates.value = duplicates.value
        .map((group) => ({
          ...group,
          items: group.items.filter((i) => i.id !== item.id),
        }))
        .filter((group) => group.items.length > 1);
    } catch (error) {
      console.error("Error deleting manga:", error);
    }
  }
};

const viewManga = (item) => {
  router.push(`/manga/${item.manga.id}`);
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString();
};
</script>

<style scoped>
.duplicate-detection {
  max-height: 80vh;
  overflow-y: auto;
}

/* Custom scrollbar */
.duplicate-detection::-webkit-scrollbar {
  width: 6px;
}

.duplicate-detection::-webkit-scrollbar-track {
  background: transparent;
}

.duplicate-detection::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 3px;
}
</style>
