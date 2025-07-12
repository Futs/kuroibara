<template>
  <div class="manga-details">
    <div v-if="loading" class="flex justify-center items-center py-12">
      <svg
        class="animate-spin h-10 w-10 text-primary-600"
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
    </div>

    <div v-else-if="error" class="bg-red-50 dark:bg-red-900 p-4 rounded-md">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg
            class="h-5 w-5 text-red-400 dark:text-red-300"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
            {{ error }}
          </h3>
          <div class="mt-2 text-sm text-red-700 dark:text-red-300">
            <button
              @click="fetchMangaDetails"
              class="font-medium underline hover:text-red-600 dark:hover:text-red-400"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-else-if="manga"
      class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden"
    >
      <!-- Manga Header -->
      <div class="relative">
        <div class="h-48 sm:h-64 w-full bg-gray-200 dark:bg-dark-700">
          <img
            v-if="manga.cover_image"
            :src="getCoverUrl(manga.id)"
            :alt="manga.title"
            class="w-full h-full object-cover"
            @error="onImageError"
          />
        </div>

        <div
          class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4"
        >
          <h1 class="text-2xl sm:text-3xl font-bold text-white">
            {{ manga.title }}
          </h1>
          <p
            v-if="manga.alternative_titles && manga.alternative_titles.length"
            class="text-sm text-gray-300 mt-1"
          >
            {{ manga.alternative_titles.join(" / ") }}
          </p>
        </div>
      </div>

      <!-- Manga Content -->
      <div class="p-4 sm:p-6">
        <div class="flex flex-col md:flex-row gap-6">
          <!-- Left Column - Cover and Actions -->
          <div class="w-full md:w-1/3 lg:w-1/4">
            <div
              class="aspect-w-2 aspect-h-3 rounded-lg overflow-hidden bg-gray-200 dark:bg-dark-700"
            >
              <img
                v-if="manga.cover_image"
                :src="getCoverUrl(manga.id)"
                :alt="manga.title"
                class="w-full h-full object-center object-cover"
                :class="{ 'blur-md': isNsfw && blurNsfw }"
                @error="onImageError"
              />
              <div
                v-else
                class="w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-500"
              >
                <svg
                  class="h-12 w-12"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>

              <!-- NSFW Badge -->
              <div
                v-if="isNsfw"
                class="absolute top-2 right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded"
              >
                NSFW
              </div>
            </div>

            <div class="mt-4 space-y-3">
              <!-- Remove from Library (only for library items) -->
              <button
                v-if="!isExternal && inLibrary"
                @click="removeFromLibrary"
                class="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <svg
                  class="h-5 w-5 mr-2"
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
                Remove from Library
              </button>

              <!-- Add to Library (only for external manga) -->
              <button
                v-else-if="isExternal && !inLibrary"
                @click="addToLibrary"
                class="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg
                  class="h-5 w-5 mr-2"
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
                Add to Library
              </button>

              <!-- Start Reading (always show if chapters exist) -->
              <button
                v-if="manga.chapters && manga.chapters.length > 0"
                @click="startReading"
                class="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg
                  class="h-5 w-5 mr-2"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                  />
                </svg>
                Start Reading
              </button>

              <!-- Download All (only for library items) -->
              <button
                v-if="
                  !isExternal && manga.chapters && manga.chapters.length > 0
                "
                @click="downloadManga"
                class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg
                  class="h-5 w-5 mr-2"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Download All
              </button>
            </div>
          </div>

          <!-- Right Column - Details and Chapters -->
          <div class="w-full md:w-2/3 lg:w-3/4">
            <!-- Manga Info -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div v-if="manga.author" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Author:</span
                >
                <span class="text-sm text-gray-900 dark:text-white">{{
                  manga.author
                }}</span>
              </div>

              <div v-if="manga.artist" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Artist:</span
                >
                <span class="text-sm text-gray-900 dark:text-white">{{
                  manga.artist
                }}</span>
              </div>

              <div v-if="manga.status" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Status:</span
                >
                <span
                  class="text-sm text-gray-900 dark:text-white capitalize"
                  >{{ manga.status }}</span
                >
              </div>

              <div v-if="manga.year" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Year:</span
                >
                <span class="text-sm text-gray-900 dark:text-white">{{
                  manga.year
                }}</span>
              </div>

              <div v-if="manga.provider" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Provider:</span
                >
                <span class="text-sm text-gray-900 dark:text-white">{{
                  manga.provider
                }}</span>
              </div>

              <div v-if="manga.last_updated" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Updated:</span
                >
                <span class="text-sm text-gray-900 dark:text-white">{{
                  formatDate(manga.last_updated)
                }}</span>
              </div>
            </div>

            <!-- Genres -->
            <div v-if="manga.genres && manga.genres.length" class="mt-4">
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Genres:
              </h3>
              <div class="mt-1 flex flex-wrap gap-2">
                <span
                  v-for="genre in manga.genres"
                  :key="genre"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200"
                >
                  {{ genre }}
                </span>
              </div>
            </div>

            <!-- Description -->
            <div v-if="manga.description" class="mt-4">
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Description:
              </h3>
              <div
                class="mt-1 text-sm text-gray-900 dark:text-white prose dark:prose-invert max-w-none"
                v-html="formatDescription(manga.description)"
              ></div>
            </div>

            <!-- Chapters -->
            <div v-if="manga.chapters && manga.chapters.length" class="mt-6">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white">
                  Chapters ({{ manga.chapters.length }})
                </h3>
                <div class="flex items-center space-x-4">
                  <!-- View Mode Toggle (for library items) -->
                  <div
                    v-if="!isExternal && libraryItemDetails"
                    class="flex items-center space-x-2"
                  >
                    <span class="text-sm text-gray-500 dark:text-gray-400"
                      >View:</span
                    >
                    <div class="flex rounded-md shadow-sm">
                      <button
                        @click="viewMode = 'chapters'"
                        :class="[
                          'px-3 py-1 text-sm font-medium rounded-l-md border',
                          viewMode === 'chapters'
                            ? 'bg-primary-600 text-white border-primary-600'
                            : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-dark-600 hover:bg-gray-50 dark:hover:bg-dark-700',
                        ]"
                      >
                        Chapters
                      </button>
                      <button
                        @click="viewMode = 'volumes'"
                        :class="[
                          'px-3 py-1 text-sm font-medium rounded-r-md border-t border-r border-b',
                          viewMode === 'volumes'
                            ? 'bg-primary-600 text-white border-primary-600'
                            : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-dark-600 hover:bg-gray-50 dark:hover:bg-dark-700',
                        ]"
                      >
                        Volumes
                      </button>
                    </div>
                  </div>

                  <!-- Download Summary (for library items) -->
                  <div
                    v-if="!isExternal && libraryItemDetails"
                    class="text-sm text-gray-500 dark:text-gray-400"
                  >
                    {{
                      libraryItemDetails.download_summary.downloaded_chapters
                    }}/{{
                      libraryItemDetails.download_summary.total_chapters
                    }}
                    downloaded
                  </div>

                  <label
                    for="sort-chapters"
                    class="text-sm text-gray-500 dark:text-gray-400"
                    >Sort:</label
                  >
                  <select
                    id="sort-chapters"
                    v-model="chapterSort"
                    class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white"
                  >
                    <option value="desc">Newest First</option>
                    <option value="asc">Oldest First</option>
                  </select>
                </div>
              </div>

              <!-- Chapter Filters (for library items) -->
              <div v-if="!isExternal && libraryItemDetails" class="mt-4">
                <ChapterFilters
                  :available-languages="availableLanguages"
                  :available-volumes="availableVolumes"
                  :filters="chapterFilters"
                  @update-filters="updateChapterFilters"
                />
              </div>

              <div class="mt-2 border-t border-gray-200 dark:border-dark-600">
                <!-- Volume View (for library items) -->
                <div
                  v-if="
                    !isExternal && libraryItemDetails && viewMode === 'volumes'
                  "
                  class="space-y-4 pt-4"
                >
                  <VolumeDownloadCard
                    v-for="volume in groupedVolumes"
                    :key="volume.number"
                    :volume="volume"
                    @download-volume="downloadVolume"
                    @download-chapter="downloadChapter"
                    @retry-failed="retryFailedChapters"
                  />
                </div>

                <!-- Chapter View (for library items) -->
                <ul
                  v-else-if="
                    !isExternal && libraryItemDetails && viewMode === 'chapters'
                  "
                  role="list"
                  class="divide-y divide-gray-200 dark:divide-dark-600"
                >
                  <EnhancedChapterCard
                    v-for="chapter in sortedEnhancedChapters"
                    :key="chapter.id"
                    :chapter="chapter"
                    @read-chapter="readChapter"
                    @download-chapter="downloadChapter"
                  />
                </ul>

                <!-- Basic chapters for external manga -->
                <ul
                  v-else
                  role="list"
                  class="divide-y divide-gray-200 dark:divide-dark-600"
                >
                  <li
                    v-for="chapter in sortedChapters"
                    :key="chapter.id"
                    class="py-4 flex items-center justify-between"
                  >
                    <div class="flex items-center">
                      <div>
                        <p
                          class="text-sm font-medium text-gray-900 dark:text-white"
                        >
                          Chapter {{ chapter.number
                          }}{{ chapter.title ? `: ${chapter.title}` : "" }}
                        </p>
                        <p
                          v-if="chapter.upload_date"
                          class="text-xs text-gray-500 dark:text-gray-400"
                        >
                          {{ formatDate(chapter.upload_date) }}
                        </p>
                      </div>
                    </div>
                    <div class="flex items-center space-x-2">
                      <button
                        @click="readChapter(chapter.id)"
                        class="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                      >
                        Read
                      </button>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useLibraryStore } from "../stores/library";
import { useSettingsStore } from "../stores/settings";
import EnhancedChapterCard from "../components/EnhancedChapterCard.vue";
import ChapterFilters from "../components/ChapterFilters.vue";
import VolumeDownloadCard from "../components/VolumeDownloadCard.vue";
import api from "../services/api";

const route = useRoute();
const router = useRouter();
const libraryStore = useLibraryStore();
const settingsStore = useSettingsStore();

const mangaId = computed(() => route.params.id);
const provider = computed(() => route.params.provider);
const isExternal = computed(() => !!provider.value);
const manga = ref(null);
const loading = ref(true);
const error = ref(null);
const inLibrary = ref(false);
const chapterSort = ref("desc");
const libraryItemDetails = ref(null);
const chapterFilters = ref({
  language: "",
  volume: "",
  downloadStatus: "",
  readingStatus: "",
});
const viewMode = ref("chapters"); // "chapters" or "volumes"

const isNsfw = computed(() => manga.value?.is_nsfw || manga.value?.is_explicit);
const blurNsfw = computed(() => settingsStore.getNsfwBlur);

const sortedChapters = computed(() => {
  if (!manga.value?.chapters) return [];

  return [...manga.value.chapters].sort((a, b) => {
    const aNum = parseFloat(a.number) || 0;
    const bNum = parseFloat(b.number) || 0;

    if (chapterSort.value === "asc") {
      return aNum - bNum;
    } else {
      return bNum - aNum;
    }
  });
});

const availableLanguages = computed(() => {
  if (!libraryItemDetails.value?.chapters) return [];

  const languages = new Set();
  libraryItemDetails.value.chapters.forEach((chapter) => {
    if (chapter.language) {
      languages.add(chapter.language);
    }
  });

  return Array.from(languages).sort();
});

const availableVolumes = computed(() => {
  if (!libraryItemDetails.value?.chapters) return [];

  const volumes = new Set();
  libraryItemDetails.value.chapters.forEach((chapter) => {
    if (chapter.volume) {
      volumes.add(chapter.volume);
    }
  });

  return Array.from(volumes).sort((a, b) => {
    const aNum = parseFloat(a) || 0;
    const bNum = parseFloat(b) || 0;
    return aNum - bNum;
  });
});

const sortedEnhancedChapters = computed(() => {
  if (!libraryItemDetails.value?.chapters) return [];

  let chapters = [...libraryItemDetails.value.chapters];

  // Apply filters
  if (chapterFilters.value.language) {
    chapters = chapters.filter(
      (chapter) => chapter.language === chapterFilters.value.language,
    );
  }

  if (chapterFilters.value.volume) {
    chapters = chapters.filter(
      (chapter) => chapter.volume === chapterFilters.value.volume,
    );
  }

  if (chapterFilters.value.downloadStatus) {
    chapters = chapters.filter((chapter) => {
      switch (chapterFilters.value.downloadStatus) {
        case "downloaded":
          return chapter.download_status === "downloaded";
        case "not_downloaded":
          return chapter.download_status === "not_downloaded";
        case "error":
          return chapter.download_status === "error";
        default:
          return true;
      }
    });
  }

  if (chapterFilters.value.readingStatus) {
    chapters = chapters.filter((chapter) => {
      const progress = chapter.reading_progress;
      switch (chapterFilters.value.readingStatus) {
        case "unread":
          return !progress;
        case "in_progress":
          return progress && !progress.is_completed;
        case "completed":
          return progress && progress.is_completed;
        default:
          return true;
      }
    });
  }

  // Sort chapters
  return chapters.sort((a, b) => {
    const aNum = parseFloat(a.number) || 0;
    const bNum = parseFloat(b.number) || 0;

    if (chapterSort.value === "asc") {
      return aNum - bNum;
    } else {
      return bNum - aNum;
    }
  });
});

const groupedVolumes = computed(() => {
  if (!libraryItemDetails.value?.chapters) return [];

  const volumeMap = new Map();

  libraryItemDetails.value.chapters.forEach((chapter) => {
    const volumeNumber = chapter.volume || "Unknown";

    if (!volumeMap.has(volumeNumber)) {
      volumeMap.set(volumeNumber, {
        number: volumeNumber,
        chapters: [],
        language: chapter.language,
      });
    }

    volumeMap.get(volumeNumber).chapters.push(chapter);
  });

  // Sort volumes and chapters within each volume
  const volumes = Array.from(volumeMap.values()).sort((a, b) => {
    const aNum = parseFloat(a.number) || 0;
    const bNum = parseFloat(b.number) || 0;
    return aNum - bNum;
  });

  volumes.forEach((volume) => {
    volume.chapters.sort((a, b) => {
      const aNum = parseFloat(a.number) || 0;
      const bNum = parseFloat(b.number) || 0;
      return aNum - bNum;
    });
  });

  return volumes;
});

const getCoverUrl = (mangaId) => {
  // For external manga, use the cover_image URL directly
  if (isExternal.value && manga.value && manga.value.cover_image) {
    return manga.value.cover_image;
  }
  // For internal manga, use the cover endpoint
  return `/api/v1/manga/${mangaId}/cover`;
};

const fetchMangaDetails = async () => {
  loading.value = true;
  error.value = null;

  try {
    let response;
    if (isExternal.value) {
      // For external manga, use the external endpoint
      response = await api.get(
        `/v1/manga/external/${provider.value}/${mangaId.value}`,
      );
    } else {
      // For internal manga, use the regular endpoint
      response = await api.get(`/v1/manga/${mangaId.value}`);
    }

    manga.value = response.data;

    // Check if manga is in library and load enhanced details
    if (isExternal.value) {
      // For external manga, we might need to implement a different library check
      // For now, set to false
      inLibrary.value = false;
      libraryItemDetails.value = null;
    } else {
      // For library items, load enhanced details
      await checkLibraryStatus();
      if (inLibrary.value) {
        await loadLibraryItemDetails();
      }
    }
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to load manga details";
    console.error("Error fetching manga details:", err);
  } finally {
    loading.value = false;
  }
};

const checkLibraryStatus = async () => {
  try {
    const response = await api.get(`/v1/library/check/${mangaId.value}`);
    inLibrary.value = response.data.in_library;
  } catch (err) {
    console.error("Error checking library status:", err);
  }
};

const loadLibraryItemDetails = async () => {
  try {
    // Find the library item ID for this manga
    const libraryResponse = await api.get("/v1/library", {
      params: { manga_id: mangaId.value },
    });

    if (libraryResponse.data.length > 0) {
      const libraryItemId = libraryResponse.data[0].id;
      libraryItemDetails.value =
        await libraryStore.fetchLibraryItemDetailed(libraryItemId);
    }
  } catch (err) {
    console.error("Error loading library item details:", err);
  }
};

const addToLibrary = async () => {
  try {
    let actualMangaId = mangaId.value;

    // If this is an external manga, create a local record first
    if (isExternal.value) {
      const response = await api.post(
        "/v1/manga/from-external",
        {},
        {
          params: {
            provider: provider.value,
            external_id: mangaId.value,
          },
        },
      );
      actualMangaId = response.data.id;
    }

    await libraryStore.addToLibrary(actualMangaId);
    inLibrary.value = true;
  } catch (err) {
    console.error("Error adding to library:", err);
    alert(
      "Failed to add manga to library: " +
        (err.response?.data?.detail || err.message),
    );
  }
};

const removeFromLibrary = async () => {
  if (
    confirm("Are you sure you want to remove this manga from your library?")
  ) {
    try {
      await libraryStore.removeFromLibrary(mangaId.value);
      inLibrary.value = false;
    } catch (err) {
      console.error("Error removing from library:", err);
    }
  }
};

const startReading = () => {
  if (manga.value?.chapters && manga.value.chapters.length > 0) {
    const firstChapter =
      sortedChapters.value[
        chapterSort.value === "asc" ? 0 : sortedChapters.value.length - 1
      ];
    readChapter(firstChapter.id);
  }
};

const readChapter = (chapterOrId) => {
  const chapterId =
    typeof chapterOrId === "object" ? chapterOrId.id : chapterOrId;
  router.push(`/read/${mangaId.value}/${chapterId}`);
};

const updateChapterFilters = (newFilters) => {
  chapterFilters.value = { ...newFilters };
};

const downloadVolume = async (volumeData) => {
  try {
    const libraryResponse = await api.get("/v1/library", {
      params: { manga_id: mangaId.value },
    });

    if (libraryResponse.data.length === 0) {
      throw new Error("Manga not found in library");
    }

    const libraryItemId = libraryResponse.data[0].id;

    // Download all chapters in the volume
    for (const chapter of volumeData.chapters) {
      if (chapter.download_status !== "downloaded") {
        await libraryStore.downloadChapter(
          libraryItemId,
          chapter.id,
          manga.value.provider || "mangadx",
          manga.value.external_id || mangaId.value,
          chapter.id,
        );
      }
    }

    // Reload library item details to update download status
    await loadLibraryItemDetails();

    console.log("Volume download started successfully");
  } catch (err) {
    console.error("Error downloading volume:", err);
    alert(
      "Failed to download volume: " +
        (err.response?.data?.detail || err.message),
    );
  }
};

const retryFailedChapters = async (volumeData) => {
  try {
    const libraryResponse = await api.get("/v1/library", {
      params: { manga_id: mangaId.value },
    });

    if (libraryResponse.data.length === 0) {
      throw new Error("Manga not found in library");
    }

    const libraryItemId = libraryResponse.data[0].id;

    // Retry failed chapters in the volume
    for (const chapter of volumeData.chapters) {
      if (chapter.download_status === "error") {
        await libraryStore.downloadChapter(
          libraryItemId,
          chapter.id,
          manga.value.provider || "mangadx",
          manga.value.external_id || mangaId.value,
          chapter.id,
        );
      }
    }

    // Reload library item details to update download status
    await loadLibraryItemDetails();

    console.log("Failed chapters retry started successfully");
  } catch (err) {
    console.error("Error retrying failed chapters:", err);
    alert(
      "Failed to retry chapters: " +
        (err.response?.data?.detail || err.message),
    );
  }
};

const downloadManga = async () => {
  try {
    // First, we need to add the manga to library if it's not already there
    if (!inLibrary.value) {
      await addToLibrary();
    }

    // Get the library item ID
    const libraryResponse = await api.get("/v1/library");
    const libraryItem = libraryResponse.data.find(
      (item) => item.manga_id === mangaId.value,
    );

    if (!libraryItem) {
      throw new Error("Manga not found in library");
    }

    // Start the download
    await api.post(
      `/v1/library/${libraryItem.id}/download`,
      {},
      {
        params: {
          provider: manga.value.provider || "mangadex",
          external_id: manga.value.external_id || mangaId.value,
        },
      },
    );

    alert("Download started! Check your downloads page for progress.");
  } catch (err) {
    console.error("Error downloading manga:", err);
    alert(
      "Failed to download manga: " +
        (err.response?.data?.detail || err.message),
    );
  }
};

const downloadChapter = async (chapter) => {
  try {
    if (!libraryItemDetails.value) {
      throw new Error("Library item details not available");
    }

    // Find the library item ID
    const libraryResponse = await api.get("/v1/library", {
      params: { manga_id: mangaId.value },
    });

    if (libraryResponse.data.length === 0) {
      throw new Error("Manga not found in library");
    }

    const libraryItemId = libraryResponse.data[0].id;

    // Download the specific chapter
    await libraryStore.downloadChapter(
      libraryItemId,
      chapter.id,
      manga.value.provider || "mangadex",
      manga.value.external_id || mangaId.value,
      chapter.id,
    );

    // Reload library item details to update download status
    await loadLibraryItemDetails();

    console.log("Chapter download started successfully");
  } catch (err) {
    console.error("Error downloading chapter:", err);
    alert(
      "Failed to download chapter: " +
        (err.response?.data?.detail || err.message),
    );
  }
};

const formatDate = (dateString) => {
  if (!dateString) return "N/A";

  const date = new Date(dateString);
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
};

const formatDescription = (description) => {
  if (!description) return "";

  // Convert newlines to <br> tags
  return description.replace(/\n/g, "<br>");
};

const onImageError = (event) => {
  // Hide the image if it fails to load
  event.target.style.display = "none";
  console.warn(
    `Failed to load cover image for ${manga.value?.title}: ${event.target.src}`,
  );
};

onMounted(() => {
  fetchMangaDetails();
});
</script>
