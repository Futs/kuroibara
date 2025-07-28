<template>
  <div class="bulk-operations">
    <!-- Bulk Mode Toggle -->
    <div class="flex items-center justify-between mb-4">
      <button
        @click="toggleBulkMode"
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
      >
        {{ bulkMode ? "Exit Bulk Mode" : "Bulk Operations" }}
      </button>

      <div v-if="bulkMode" class="text-sm text-gray-600 dark:text-gray-400">
        {{ selectedCount }} item{{ selectedCount !== 1 ? "s" : "" }} selected
      </div>
    </div>

    <!-- Bulk Operations Bar -->
    <div
      v-if="bulkMode"
      class="bulk-operations-bar bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4"
    >
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center space-x-4">
          <button
            @click="selectAll"
            class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
          >
            Select All
          </button>
          <button
            @click="deselectAll"
            class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
          >
            Deselect All
          </button>
        </div>

        <button
          @click="toggleBulkMode"
          class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
      </div>

      <!-- Bulk Actions -->
      <div
        v-if="selectedCount > 0"
        class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2"
      >
        <button
          @click="markAsRead"
          class="px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
        >
          Mark Read
        </button>

        <button
          @click="markAsUnread"
          class="px-3 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
        >
          Mark Unread
        </button>

        <button
          @click="addToFavorites"
          class="px-3 py-2 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
        >
          Add to Favorites
        </button>

        <button
          @click="removeFromFavorites"
          class="px-3 py-2 text-sm bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors"
        >
          Remove Favorites
        </button>

        <button
          @click="showTagEditor = true"
          class="px-3 py-2 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
        >
          Edit Tags
        </button>

        <button
          @click="confirmDelete"
          class="px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Delete
        </button>
      </div>

      <div
        v-else
        class="text-sm text-gray-500 dark:text-gray-400 text-center py-2"
      >
        Select items to perform bulk operations
      </div>
    </div>

    <!-- Tag Editor Modal -->
    <div
      v-if="showTagEditor"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showTagEditor = false"
    >
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
      >
        <div
          class="fixed inset-0 bg-white0 bg-opacity-75 transition-opacity"
        ></div>

        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6"
        >
          <div>
            <h3
              class="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4"
            >
              Edit Tags for {{ selectedCount }} item{{
                selectedCount !== 1 ? "s" : ""
              }}
            </h3>

            <div class="space-y-4">
              <!-- Existing Tags -->
              <div>
                <label
                  class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Available Tags
                </label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="tag in customTags"
                    :key="tag.id"
                    @click="toggleTagSelection(tag.name)"
                    class="px-3 py-1 text-sm rounded-full border transition-colors"
                    :class="
                      selectedTags.includes(tag.name)
                        ? 'text-white border-transparent'
                        : 'bg-white dark:bg-dark-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-dark-600 hover:bg-gray-50 dark:hover:bg-dark-600'
                    "
                    :style="
                      selectedTags.includes(tag.name)
                        ? { backgroundColor: tag.color }
                        : {}
                    "
                  >
                    {{ tag.name }}
                  </button>
                </div>
              </div>

              <!-- Create New Tag -->
              <div>
                <label
                  class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Create New Tag
                </label>
                <div class="flex space-x-2">
                  <input
                    v-model="newTagName"
                    type="text"
                    placeholder="Tag name"
                    class="flex-1 px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                  />
                  <input
                    v-model="newTagColor"
                    type="color"
                    class="w-12 h-10 border border-gray-300 dark:border-dark-600 rounded-md cursor-pointer"
                  />
                  <button
                    @click="createAndSelectTag"
                    class="px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                  >
                    Create
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-5 sm:mt-6 flex space-x-3">
            <button
              @click="applyTags"
              class="flex-1 inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
            >
              Apply Tags
            </button>
            <button
              @click="showTagEditor = false"
              class="flex-1 inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-700 text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-white dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteConfirm"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showDeleteConfirm = false"
    >
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
      >
        <div
          class="fixed inset-0 bg-white0 bg-opacity-75 transition-opacity"
        ></div>

        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6"
        >
          <div class="sm:flex sm:items-start">
            <div
              class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10"
            >
              <svg
                class="h-6 w-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3
                class="text-lg leading-6 font-medium text-gray-900 dark:text-white"
              >
                Delete {{ selectedCount }} item{{
                  selectedCount !== 1 ? "s" : ""
                }}
              </h3>
              <div class="mt-2">
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Are you sure you want to delete the selected manga? This
                  action cannot be undone.
                </p>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              @click="performDelete"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Delete
            </button>
            <button
              @click="showDeleteConfirm = false"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-700 text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-white dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm"
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

const libraryStore = useLibraryStore();

// Local state
const showTagEditor = ref(false);
const showDeleteConfirm = ref(false);
const selectedTags = ref([]);
const newTagName = ref("");
const newTagColor = ref("#3B82F6");

// Computed properties
const bulkMode = computed(() => libraryStore.bulkOperationMode);
const selectedCount = computed(() => libraryStore.getSelectedCount);
const customTags = computed(() => libraryStore.getCustomTags);

// Methods
const toggleBulkMode = () => {
  libraryStore.toggleBulkMode();
};

const selectAll = () => {
  libraryStore.selectAllManga();
};

const deselectAll = () => {
  libraryStore.deselectAllManga();
};

const markAsRead = async () => {
  try {
    await libraryStore.bulkMarkAsRead();
  } catch (error) {
    console.error("Failed to mark as read:", error);
  }
};

const markAsUnread = async () => {
  try {
    await libraryStore.bulkMarkAsUnread();
  } catch (error) {
    console.error("Failed to mark as unread:", error);
  }
};

const addToFavorites = async () => {
  try {
    await libraryStore.bulkAddToFavorites();
  } catch (error) {
    console.error("Failed to add to favorites:", error);
  }
};

const removeFromFavorites = async () => {
  try {
    await libraryStore.bulkRemoveFromFavorites();
  } catch (error) {
    console.error("Failed to remove from favorites:", error);
  }
};

const confirmDelete = () => {
  showDeleteConfirm.value = true;
};

const performDelete = async () => {
  try {
    await libraryStore.bulkDelete();
    showDeleteConfirm.value = false;
  } catch (error) {
    console.error("Failed to delete:", error);
  }
};

const toggleTagSelection = (tagName) => {
  const index = selectedTags.value.indexOf(tagName);
  if (index > -1) {
    selectedTags.value.splice(index, 1);
  } else {
    selectedTags.value.push(tagName);
  }
};

const createAndSelectTag = () => {
  if (newTagName.value.trim()) {
    libraryStore.createCustomTag({
      name: newTagName.value.trim(),
      color: newTagColor.value,
    });
    selectedTags.value.push(newTagName.value.trim());
    newTagName.value = "";
    newTagColor.value = "#3B82F6";
  }
};

const applyTags = async () => {
  try {
    await libraryStore.bulkUpdateTags(selectedTags.value);
    showTagEditor.value = false;
    selectedTags.value = [];
  } catch (error) {
    console.error("Failed to update tags:", error);
  }
};
</script>

<style scoped>
.bulk-operations-bar {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
