<template>
  <div
    class="library-filters bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6"
  >
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
        Filters
      </h3>
      <div class="flex space-x-2">
        <button
          @click="resetFilters"
          class="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
        >
          Reset
        </button>
        <button
          @click="toggleAdvanced"
          class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          {{ showAdvanced ? "Simple" : "Advanced" }}
        </button>
      </div>
    </div>

    <!-- Search -->
    <div class="mb-4">
      <label
        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
      >
        Search
      </label>
      <input
        v-model="localFilters.search"
        @input="debounceSearch"
        type="text"
        placeholder="Search titles, authors, descriptions..."
        class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
      />
    </div>

    <!-- Read Status -->
    <div class="mb-4">
      <label
        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
      >
        Read Status
      </label>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="status in availableReadStatuses"
          :key="status.value"
          @click="toggleReadStatus(status.value)"
          class="px-3 py-1 text-sm rounded-full border transition-colors"
          :class="
            localFilters.readStatus.includes(status.value)
              ? `bg-${status.color}-500 text-white border-${status.color}-500`
              : 'bg-gray-100 dark:bg-dark-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-dark-600 hover:bg-gray-200 dark:hover:bg-dark-600'
          "
        >
          {{ status.label }}
        </button>
      </div>
    </div>

    <!-- Favorites -->
    <div class="mb-4">
      <label class="flex items-center">
        <input
          v-model="localFilters.isFavorite"
          type="checkbox"
          class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <span class="ml-2 text-sm text-gray-700 dark:text-gray-300"
          >Favorites only</span
        >
      </label>
    </div>

    <!-- Advanced Filters -->
    <div v-if="showAdvanced" class="space-y-4">
      <!-- Rating Range -->
      <div>
        <label
          class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >
          Rating: {{ localFilters.rating.min }} - {{ localFilters.rating.max }}
        </label>
        <div class="flex items-center space-x-4">
          <input
            v-model.number="localFilters.rating.min"
            type="range"
            min="0"
            max="10"
            step="0.5"
            class="flex-1"
            @input="updateFilters"
          />
          <input
            v-model.number="localFilters.rating.max"
            type="range"
            min="0"
            max="10"
            step="0.5"
            class="flex-1"
            @input="updateFilters"
          />
        </div>
      </div>

      <!-- Date Added -->
      <div>
        <label
          class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >
          Date Added
        </label>
        <div class="grid grid-cols-2 gap-2">
          <input
            v-model="localFilters.dateAdded.start"
            type="date"
            class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
            @change="updateFilters"
          />
          <input
            v-model="localFilters.dateAdded.end"
            type="date"
            class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
            @change="updateFilters"
          />
        </div>
      </div>

      <!-- Genres -->
      <div>
        <label
          class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >
          Genres
        </label>
        <div
          class="max-h-32 overflow-y-auto border border-gray-300 dark:border-dark-600 rounded-md p-2"
        >
          <div
            v-for="genre in availableGenres"
            :key="genre"
            class="flex items-center mb-1"
          >
            <input
              :id="`genre-${genre}`"
              v-model="localFilters.genres"
              :value="genre"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              @change="updateFilters"
            />
            <label
              :for="`genre-${genre}`"
              class="ml-2 text-sm text-gray-700 dark:text-gray-300"
            >
              {{ genre }}
            </label>
          </div>
        </div>
      </div>

      <!-- Authors -->
      <div>
        <label
          class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >
          Authors
        </label>
        <select
          v-model="selectedAuthor"
          @change="addAuthorFilter"
          class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
        >
          <option value="">Select an author...</option>
          <option
            v-for="author in availableAuthors"
            :key="author"
            :value="author"
          >
            {{ author }}
          </option>
        </select>
        <div
          v-if="localFilters.authors.length > 0"
          class="mt-2 flex flex-wrap gap-1"
        >
          <span
            v-for="author in localFilters.authors"
            :key="author"
            class="inline-flex items-center px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full"
          >
            {{ author }}
            <button
              @click="removeAuthorFilter(author)"
              class="ml-1 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
            >
              ×
            </button>
          </span>
        </div>
      </div>

      <!-- Custom Tags -->
      <div v-if="customTags.length > 0">
        <label
          class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >
          Custom Tags
        </label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="tag in customTags"
            :key="tag.id"
            @click="toggleCustomTag(tag.name)"
            class="px-3 py-1 text-sm rounded-full border transition-colors"
            :class="
              localFilters.customTags.includes(tag.name)
                ? 'text-white border-transparent'
                : 'bg-gray-100 dark:bg-dark-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-dark-600 hover:bg-gray-200 dark:hover:bg-dark-600'
            "
            :style="
              localFilters.customTags.includes(tag.name)
                ? { backgroundColor: tag.color }
                : {}
            "
          >
            {{ tag.name }}
          </button>
        </div>
      </div>

      <!-- Additional Options -->
      <div class="space-y-2">
        <label class="flex items-center">
          <input
            v-model="localFilters.hasUnreadChapters"
            type="checkbox"
            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            @change="updateFilters"
          />
          <span class="ml-2 text-sm text-gray-700 dark:text-gray-300"
            >Has unread chapters</span
          >
        </label>

        <label class="flex items-center">
          <input
            v-model="localFilters.isDownloaded"
            type="checkbox"
            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            @change="updateFilters"
          />
          <span class="ml-2 text-sm text-gray-700 dark:text-gray-300"
            >Downloaded</span
          >
        </label>

        <label class="flex items-center">
          <input
            v-model="localFilters.hasBookmarks"
            type="checkbox"
            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            @change="updateFilters"
          />
          <span class="ml-2 text-sm text-gray-700 dark:text-gray-300"
            >Has bookmarks</span
          >
        </label>

        <label class="flex items-center">
          <input
            v-model="localFilters.duplicatesOnly"
            type="checkbox"
            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            @change="updateFilters"
          />
          <span class="ml-2 text-sm text-gray-700 dark:text-gray-300"
            >Show duplicates only</span
          >
        </label>
      </div>
    </div>

    <!-- Active Filters Summary -->
    <div
      v-if="hasActiveFilters"
      class="mt-6 pt-4 border-t border-gray-200 dark:border-dark-600"
    >
      <div class="text-sm text-gray-600 dark:text-gray-400 mb-2">
        Active filters:
      </div>
      <div class="flex flex-wrap gap-1">
        <span
          v-for="filter in activeFiltersSummary"
          :key="filter.key"
          class="inline-flex items-center px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full"
        >
          {{ filter.label }}
          <button
            @click="removeFilter(filter.key, filter.value)"
            class="ml-1 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
          >
            ×
          </button>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useLibraryStore } from "../stores/library";
import { debounce } from "lodash-es";

const libraryStore = useLibraryStore();

// Local state
const showAdvanced = ref(false);
const selectedAuthor = ref("");

// Local filters (for immediate UI updates)
const localFilters = ref({ ...libraryStore.filters });

// Computed properties
const availableReadStatuses = computed(
  () => libraryStore.getAvailableReadStatuses,
);
const availableGenres = computed(() => libraryStore.getAvailableGenres);
const availableAuthors = computed(() => libraryStore.getAvailableAuthors);
const customTags = computed(() => libraryStore.getCustomTags);

const hasActiveFilters = computed(() => {
  return (
    localFilters.value.search ||
    localFilters.value.readStatus.length > 0 ||
    localFilters.value.genres.length > 0 ||
    localFilters.value.authors.length > 0 ||
    localFilters.value.customTags.length > 0 ||
    localFilters.value.isFavorite ||
    localFilters.value.rating.min > 0 ||
    localFilters.value.rating.max < 10
  );
});

const activeFiltersSummary = computed(() => {
  const summary = [];

  if (localFilters.value.search) {
    summary.push({
      key: "search",
      label: `Search: ${localFilters.value.search}`,
      value: null,
    });
  }

  localFilters.value.readStatus.forEach((status) => {
    const statusObj = availableReadStatuses.value.find(
      (s) => s.value === status,
    );
    summary.push({
      key: "readStatus",
      label: statusObj?.label || status,
      value: status,
    });
  });

  localFilters.value.genres.forEach((genre) => {
    summary.push({ key: "genres", label: `Genre: ${genre}`, value: genre });
  });

  localFilters.value.authors.forEach((author) => {
    summary.push({ key: "authors", label: `Author: ${author}`, value: author });
  });

  localFilters.value.customTags.forEach((tag) => {
    summary.push({ key: "customTags", label: `Tag: ${tag}`, value: tag });
  });

  if (localFilters.value.isFavorite) {
    summary.push({ key: "isFavorite", label: "Favorites", value: null });
  }

  return summary;
});

// Methods
const toggleAdvanced = () => {
  showAdvanced.value = !showAdvanced.value;
};

const updateFilters = () => {
  libraryStore.setFilters(localFilters.value);
};

const debounceSearch = debounce(() => {
  updateFilters();
}, 300);

const resetFilters = () => {
  libraryStore.resetFilters();
  localFilters.value = { ...libraryStore.filters };
};

const toggleReadStatus = (status) => {
  const index = localFilters.value.readStatus.indexOf(status);
  if (index > -1) {
    localFilters.value.readStatus.splice(index, 1);
  } else {
    localFilters.value.readStatus.push(status);
  }
  updateFilters();
};

const addAuthorFilter = () => {
  if (
    selectedAuthor.value &&
    !localFilters.value.authors.includes(selectedAuthor.value)
  ) {
    localFilters.value.authors.push(selectedAuthor.value);
    selectedAuthor.value = "";
    updateFilters();
  }
};

const removeAuthorFilter = (author) => {
  const index = localFilters.value.authors.indexOf(author);
  if (index > -1) {
    localFilters.value.authors.splice(index, 1);
    updateFilters();
  }
};

const toggleCustomTag = (tagName) => {
  const index = localFilters.value.customTags.indexOf(tagName);
  if (index > -1) {
    localFilters.value.customTags.splice(index, 1);
  } else {
    localFilters.value.customTags.push(tagName);
  }
  updateFilters();
};

const removeFilter = (key, value) => {
  if (value !== null) {
    const index = localFilters.value[key].indexOf(value);
    if (index > -1) {
      localFilters.value[key].splice(index, 1);
    }
  } else {
    if (key === "search") {
      localFilters.value.search = "";
    } else if (key === "isFavorite") {
      localFilters.value.isFavorite = null;
    }
  }
  updateFilters();
};

// Watch for external filter changes
watch(
  () => libraryStore.filters,
  (newFilters) => {
    localFilters.value = { ...newFilters };
  },
  { deep: true },
);
</script>

<style scoped>
.library-filters {
  max-height: 80vh;
  overflow-y: auto;
}

/* Custom scrollbar */
.library-filters::-webkit-scrollbar {
  width: 6px;
}

.library-filters::-webkit-scrollbar-track {
  background: transparent;
}

.library-filters::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 3px;
}
</style>
