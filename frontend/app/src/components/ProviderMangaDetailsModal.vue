<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-[9999] overflow-y-auto bg-black bg-opacity-75"
    aria-labelledby="modal-title"
    role="dialog"
    aria-modal="true"
  >
    <div
      class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
    >
      <!-- Background overlay -->
      <div
        class="fixed inset-0 bg-gray-900 bg-opacity-90 transition-opacity"
        aria-hidden="true"
        @click="$emit('close')"
      ></div>

      <!-- Modal panel -->
      <div
        class="relative inline-block align-middle bg-white dark:bg-dark-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all my-8 max-w-4xl w-full mx-4 z-[10000]"
      >
        <!-- Header -->
        <div class="bg-white dark:bg-dark-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
          <div class="flex items-start justify-between">
            <h3
              class="text-lg leading-6 font-medium text-gray-900 dark:text-white"
              id="modal-title"
            >
              Manga Details
            </h3>
            <button
              @click="$emit('close')"
              class="bg-white dark:bg-dark-800 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <span class="sr-only">Close</span>
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        <!-- Content -->
        <div v-if="loading" class="px-4 py-8 text-center">
          <div
            class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"
          ></div>
          <p class="mt-4 text-gray-500 dark:text-gray-400">
            Loading manga details...
          </p>
        </div>

        <div v-else-if="error" class="px-4 py-8 text-center">
          <div class="text-red-500 dark:text-red-400">
            <svg
              class="h-12 w-12 mx-auto mb-4"
              xmlns="http://www.w3.org/2000/svg"
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
            <p class="text-lg font-medium">Failed to load manga details</p>
            <p class="text-sm mt-2">{{ error }}</p>
          </div>
        </div>

        <div v-else-if="mangaDetails" class="px-4 pb-4 sm:px-6 sm:pb-6">
          <!-- Debug info (remove in production) -->
          <div
            v-if="false"
            class="mb-4 p-2 bg-yellow-100 dark:bg-yellow-900 rounded text-xs max-h-40 overflow-y-auto"
          >
            <strong>Data Structure:</strong>
            <pre>{{ JSON.stringify(mangaDetails, null, 2) }}</pre>
            <br />
            <strong>getMangaData() result:</strong>
            <pre>{{ JSON.stringify(getMangaData(), null, 2) }}</pre>
          </div>
          <div class="flex flex-col lg:flex-row gap-6">
            <!-- Cover Image -->
            <div class="lg:w-1/3">
              <div
                class="relative w-full h-96 rounded-lg overflow-hidden bg-gray-200 dark:bg-dark-700 flex items-center justify-center"
              >
                <img
                  v-if="
                    getMangaData()?.cover_image || getMangaData()?.cover_url
                  "
                  :src="getProxiedCoverUrl()"
                  :alt="getMangaData()?.title || 'Manga Cover'"
                  class="w-full h-full object-center object-cover"
                  :class="{ 'blur-md': isNsfw && blurNsfw }"
                  @error="onImageError"
                  @load="onImageLoad"
                />

                <div
                  v-else
                  class="w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-500"
                >
                  <svg
                    class="h-16 w-16"
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

            <!-- Details -->
            <div class="lg:w-2/3">
              <div class="space-y-4">
                <!-- Title and Basic Info -->
                <div>
                  <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
                    {{ getMangaData()?.title || "Unknown Title" }}
                  </h2>
                  <p
                    v-if="getMangaData()?.alternative_titles"
                    class="text-sm text-gray-500 dark:text-gray-400 mt-1"
                  >
                    {{
                      Array.isArray(getMangaData().alternative_titles)
                        ? getMangaData().alternative_titles.join(" / ")
                        : getMangaData().alternative_titles
                    }}
                  </p>
                </div>

                <!-- Metadata -->
                <div class="grid grid-cols-2 gap-4">
                  <div
                    v-if="
                      getMangaData()?.author ||
                      (getMangaData()?.authors && getMangaData().authors.length)
                    "
                  >
                    <dt
                      class="text-sm font-medium text-gray-500 dark:text-gray-400"
                    >
                      Author
                    </dt>
                    <dd class="text-sm text-gray-900 dark:text-white">
                      {{
                        getMangaData().author ||
                        (getMangaData().authors &&
                          getMangaData().authors.join(", "))
                      }}
                    </dd>
                  </div>
                  <div v-if="getMangaData()?.status">
                    <dt
                      class="text-sm font-medium text-gray-500 dark:text-gray-400"
                    >
                      Status
                    </dt>
                    <dd class="text-sm text-gray-900 dark:text-white">
                      {{ formatStatus(getMangaData().status) }}
                    </dd>
                  </div>
                  <div v-if="getMangaData()?.year">
                    <dt
                      class="text-sm font-medium text-gray-500 dark:text-gray-400"
                    >
                      Year
                    </dt>
                    <dd class="text-sm text-gray-900 dark:text-white">
                      {{ getMangaData().year }}
                    </dd>
                  </div>
                  <div v-if="mangaDetails.total_chapters">
                    <dt
                      class="text-sm font-medium text-gray-500 dark:text-gray-400"
                    >
                      Chapters
                    </dt>
                    <dd class="text-sm text-gray-900 dark:text-white">
                      {{ mangaDetails.total_chapters }}
                    </dd>
                  </div>
                </div>

                <!-- Description -->
                <div v-if="getMangaData()?.description">
                  <dt
                    class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2"
                  >
                    Description
                  </dt>
                  <dd
                    class="text-sm text-gray-900 dark:text-white leading-relaxed"
                  >
                    {{ getMangaData().description }}
                  </dd>
                </div>

                <!-- Genres -->
                <div
                  v-if="getMangaData()?.genres && getMangaData().genres.length"
                >
                  <dt
                    class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2"
                  >
                    Genres
                  </dt>
                  <dd class="flex flex-wrap gap-2">
                    <span
                      v-for="genre in getMangaData().genres"
                      :key="genre"
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-300"
                    >
                      {{ genre }}
                    </span>
                  </dd>
                </div>

                <!-- Action Buttons -->
                <div class="flex space-x-3 pt-4">
                  <button
                    @click="addToLibrary"
                    class="btn btn-primary"
                    :disabled="addingToLibrary"
                  >
                    <svg
                      v-if="addingToLibrary"
                      class="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
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
                    {{ addingToLibrary ? "Adding..." : "Add to Library" }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Chapters Section -->
          <div
            v-if="mangaDetails.chapters && mangaDetails.chapters.length"
            class="mt-8"
          >
            <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Available Chapters ({{ mangaDetails.chapters.length }})
            </h3>
            <div
              class="max-h-64 overflow-y-auto border border-gray-200 dark:border-dark-600 rounded-lg"
            >
              <div class="divide-y divide-gray-200 dark:divide-dark-600">
                <div
                  v-for="chapter in mangaDetails.chapters.slice(0, 20)"
                  :key="chapter.id"
                  class="px-4 py-3 hover:bg-gray-50 dark:hover:bg-dark-700"
                >
                  <div class="flex justify-between items-center">
                    <div>
                      <p
                        class="text-sm font-medium text-gray-900 dark:text-white"
                      >
                        Chapter {{ chapter.number
                        }}{{ chapter.title ? `: ${chapter.title}` : "" }}
                      </p>
                      <p class="text-xs text-gray-500 dark:text-gray-400">
                        {{ chapter.language }} •
                        {{ chapter.pages_count || "Unknown" }} pages
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <p
              v-if="mangaDetails.chapters.length > 20"
              class="text-xs text-gray-500 dark:text-gray-400 mt-2"
            >
              Showing first 20 chapters.
              {{ mangaDetails.chapters.length - 20 }} more available.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useSettingsStore } from "../stores/settings";

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  mangaDetails: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: null,
  },
});

const emit = defineEmits(["close", "add-to-library"]);

const settingsStore = useSettingsStore();
const addingToLibrary = ref(false);

const isNsfw = computed(() => {
  const mangaData = getMangaData();
  if (!mangaData) return false;
  return mangaData.is_nsfw || mangaData.is_explicit;
});

const blurNsfw = computed(() => settingsStore.getNsfwBlur);

const formatStatus = (status) => {
  if (!status) return "";
  return status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

const addToLibrary = async () => {
  if (addingToLibrary.value) return;

  addingToLibrary.value = true;
  try {
    emit("add-to-library", getMangaData());
  } finally {
    addingToLibrary.value = false;
  }
};

const onImageError = (event) => {
  console.error("Failed to load manga cover image:", event.target.src);
  event.target.style.display = "none";
};

const onImageLoad = (event) => {
  console.log("Successfully loaded manga cover image:", event.target.src);
};

const getProxiedCoverUrl = () => {
  const mangaData = getMangaData();
  if (!mangaData) {
    console.log("No manga data available for cover");
    return "/placeholder-cover.jpg";
  }

  const coverUrl = mangaData.cover_image || mangaData.cover_url;
  if (!coverUrl) {
    console.log("No cover URL available");
    return "/placeholder-cover.jpg";
  }

  // For external provider manga, use image proxy
  console.log("Using image proxy for external manga cover:", coverUrl);
  const encodedUrl = encodeURIComponent(coverUrl);
  return `/api/v1/providers/image-proxy?url=${encodedUrl}`;
};

const getMangaData = () => {
  if (!props.mangaDetails) return null;

  // Try different possible data structures
  if (props.mangaDetails.manga) {
    return props.mangaDetails.manga;
  }

  // If the data is directly in mangaDetails (not nested under manga)
  if (props.mangaDetails.title) {
    return props.mangaDetails;
  }

  return null;
};
</script>

<style scoped>
.aspect-w-2 {
  position: relative;
  padding-bottom: 150%; /* 2:3 aspect ratio */
}

.aspect-w-2 > * {
  position: absolute;
  height: 100%;
  width: 100%;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}
</style>
