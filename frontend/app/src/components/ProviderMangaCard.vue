<template>
  <div
    class="provider-manga-list-item border-b border-gray-200 dark:border-dark-600 last:border-b-0"
  >
    <div
      class="px-4 py-4 hover:bg-gray-50 dark:hover:bg-dark-700 transition-colors duration-200 cursor-pointer"
      @click="viewDetails"
    >
      <div class="flex items-start space-x-4">
        <!-- Cover Image -->
        <div class="flex-shrink-0">
          <div
            class="w-16 h-20 rounded-lg overflow-hidden bg-gray-200 dark:bg-dark-700"
          >
            <img
              v-if="manga.cover_image || manga.cover_url"
              :src="getCoverImageUrl()"
              :alt="manga.title"
              class="w-full h-full object-center object-cover"
              :class="{ 'blur-sm': isNsfw && blurNsfw }"
              @error="onImageError"
            />
            <div
              v-else
              class="w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-500"
            >
              <svg
                class="h-6 w-6"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
            </div>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <!-- Title and Badges -->
              <div class="flex items-start space-x-2 mb-2">
                <h3
                  class="text-base font-medium text-gray-900 dark:text-white line-clamp-2"
                >
                  {{ manga.title }}
                </h3>

                <!-- Status Badge -->
                <span
                  v-if="manga.status"
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 flex-shrink-0"
                >
                  {{ formatStatus(manga.status) }}
                </span>

                <!-- NSFW Badge -->
                <span
                  v-if="isNsfw"
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300 flex-shrink-0"
                >
                  NSFW
                </span>
              </div>

              <!-- Description -->
              <p
                v-if="manga.description"
                class="text-sm text-gray-600 dark:text-gray-300 line-clamp-2 mb-2"
              >
                {{ manga.description }}
              </p>

              <!-- Author and Year -->
              <div
                class="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400 mb-2"
              >
                <span v-if="manga.author">
                  <span class="font-medium">Author:</span> {{ manga.author }}
                </span>
                <span v-if="manga.year">
                  <span class="font-medium">Year:</span> {{ manga.year }}
                </span>
              </div>

              <!-- Tags/Genres -->
              <div
                v-if="manga.genres && manga.genres.length"
                class="flex flex-wrap gap-1"
              >
                <span
                  v-for="genre in manga.genres.slice(0, 5)"
                  :key="genre"
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                >
                  {{ genre }}
                </span>
                <span
                  v-if="manga.genres.length > 5"
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                >
                  +{{ manga.genres.length - 5 }} more
                </span>
              </div>
            </div>

            <!-- Action Button -->
            <div class="flex-shrink-0 ml-4">
              <button
                @click.stop="$emit('add-to-library')"
                class="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
                :disabled="adding"
              >
                <svg
                  v-if="adding"
                  class="animate-spin -ml-1 mr-1 h-4 w-4 text-current"
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
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                  />
                </svg>
                {{ adding ? "Adding..." : "Add to Library" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useSettingsStore } from "../stores/settings";
import { getCoverUrl, handleImageError } from "../utils/imageProxy";

const props = defineProps({
  manga: {
    type: Object,
    required: true,
  },
  providerId: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["add-to-library", "view-details"]);

const settingsStore = useSettingsStore();

const adding = ref(false);

const isNsfw = computed(() => {
  return props.manga.is_nsfw || props.manga.is_explicit;
});

const blurNsfw = computed(() => settingsStore.getNsfwBlur);

const viewDetails = (event) => {
  // Prevent navigation if clicking on action buttons
  if (event.target.closest("button") || event.target.closest("a")) {
    return;
  }

  // Emit event to parent to show details modal instead of navigating
  emit("view-details", props.manga);
};

const formatStatus = (status) => {
  if (!status) return "";

  // Capitalize first letter and replace underscores with spaces
  return status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

const getCoverImageUrl = () => {
  return getCoverUrl(props.manga);
};

const onImageError = (event) => {
  const originalUrl = props.manga.cover_image || props.manga.cover_url;
  handleImageError(event, originalUrl, (url) => {
    console.warn(`Failed to load cover image for ${props.manga.title}: ${url}`);
  });
};
</script>

<style scoped>
.provider-manga-list-item {
  transition: all 0.2s ease-in-out;
}

.provider-manga-list-item:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.dark .provider-manga-list-item:hover {
  background-color: rgba(255, 255, 255, 0.02);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
