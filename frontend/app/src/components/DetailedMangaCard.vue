<template>
  <div class="bg-white dark:bg-dark-800 rounded-lg shadow-md overflow-hidden">
    <!-- Header Section -->
    <div class="p-6 border-b border-gray-200 dark:border-dark-600">
      <div class="flex items-start space-x-4">
        <!-- Cover Image -->
        <div class="flex-shrink-0">
          <img
            :src="getMangaCover"
            :alt="getMangaTitle"
            class="h-32 w-24 object-cover rounded-lg shadow-sm"
            @error="$event.target.src = '/placeholder-cover.jpg'"
          />
        </div>

        <!-- Manga Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
                {{ getMangaTitle }}
              </h3>
              <p v-if="getMangaAuthor" class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                by {{ getMangaAuthor }}
              </p>
              <div class="flex items-center space-x-4 mt-2">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getStatusBadgeClass(getMangaStatus)">
                  {{ getMangaStatus || 'Unknown' }}
                </span>
                <span class="text-sm text-gray-500 dark:text-gray-400">
                  {{ getMangaGenres }}
                </span>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center space-x-2 ml-4">
              <button
                @click="$emit('download', getLibraryItemId)"
                class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                title="Download All"
              >
                <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download
              </button>
              
              <router-link
                :to="`/manga/${getMangaId}`"
                class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                title="View Details"
              >
                <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                View
              </router-link>

              <button
                @click="$emit('import', getLibraryItemId)"
                class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 text-sm leading-4 font-medium rounded-md text-blue-600 dark:text-blue-400 bg-white dark:bg-dark-800 hover:bg-blue-50 dark:hover:bg-blue-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                title="Import Files"
              >
                <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                </svg>
                Import
              </button>

              <button
                @click="$emit('remove', getLibraryItemId)"
                class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 text-sm leading-4 font-medium rounded-md text-red-600 dark:text-red-400 bg-white dark:bg-dark-800 hover:bg-red-50 dark:hover:bg-red-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                title="Remove from Library"
              >
                <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Remove
              </button>
            </div>
          </div>

          <!-- Description -->
          <p v-if="getMangaDescription" class="text-sm text-gray-600 dark:text-gray-400 mt-3 line-clamp-2">
            {{ getMangaDescription }}
          </p>

          <!-- Stats -->
          <div class="flex items-center space-x-6 mt-4 text-sm text-gray-500 dark:text-gray-400">
            <span>Added: {{ formatDate(manga.added_date) }}</span>
            <span v-if="manga.last_read">Last Read: {{ formatDate(manga.last_read) }}</span>
            <span>{{ totalChapters }} chapters</span>
            <span>{{ downloadedChapters }} downloaded</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Volumes/Chapters Section -->
    <div class="p-6">
      <div class="flex items-center justify-between mb-4">
        <h4 class="text-lg font-medium text-gray-900 dark:text-white">
          Volumes & Chapters
        </h4>
        <button
          @click="showChapters = !showChapters"
          class="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
        >
          {{ showChapters ? 'Hide' : 'Show' }} Details
        </button>
      </div>

      <!-- Progress Bar -->
      <div class="mb-4">
        <div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
          <span>Download Progress</span>
          <span>{{ downloadProgress }}%</span>
        </div>
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            class="bg-primary-600 h-2 rounded-full transition-all duration-300"
            :style="{ width: `${downloadProgress}%` }"
          ></div>
        </div>
      </div>

      <!-- Volumes List (when expanded) -->
      <div v-if="showChapters && volumes.length > 0" class="space-y-4">
        <div
          v-for="volume in volumes"
          :key="volume.number"
          class="border border-gray-200 dark:border-dark-600 rounded-lg p-4"
        >
          <div class="flex items-center justify-between mb-3">
            <h5 class="font-medium text-gray-900 dark:text-white">
              Volume {{ volume.number }}
              <span v-if="volume.title" class="text-gray-500 dark:text-gray-400">
                - {{ volume.title }}
              </span>
            </h5>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-gray-500 dark:text-gray-400">
                {{ getVolumeDownloadedCount(volume) }}/{{ volume.chapters.length }} downloaded
              </span>
              <button
                v-if="!isVolumeFullyDownloaded(volume)"
                @click="downloadVolume(volume)"
                class="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
              >
                Download All
              </button>
            </div>
          </div>

          <!-- Chapters in Volume -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            <div
              v-for="chapter in volume.chapters"
              :key="chapter.id"
              class="flex items-center justify-between p-2 rounded border border-gray-100 dark:border-dark-700"
            >
              <div class="flex items-center space-x-2">
                <!-- Download Status Icon -->
                <div class="flex-shrink-0">
                  <div
                    v-if="chapter.download_status === 'downloaded'"
                    class="w-3 h-3 rounded-full bg-green-500"
                    title="Downloaded"
                  ></div>
                  <div
                    v-else-if="chapter.download_status === 'downloading'"
                    class="w-3 h-3 rounded-full bg-blue-500 animate-pulse"
                    title="Downloading"
                  ></div>
                  <div
                    v-else-if="chapter.download_status === 'error'"
                    class="w-3 h-3 rounded-full bg-red-500"
                    title="Download Error"
                  ></div>
                  <div
                    v-else
                    class="w-3 h-3 rounded-full bg-gray-300 dark:bg-gray-600"
                    title="Not Downloaded"
                  ></div>
                </div>

                <span class="text-sm text-gray-900 dark:text-white truncate">
                  Ch. {{ chapter.number }}
                  <span v-if="chapter.title" class="text-gray-500 dark:text-gray-400">
                    - {{ chapter.title }}
                  </span>
                </span>
              </div>

              <div class="flex items-center space-x-1">
                <button
                  v-if="chapter.download_status === 'downloaded'"
                  @click="readChapter(chapter)"
                  class="text-xs text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300"
                  title="Read Chapter"
                >
                  Read
                </button>
                <button
                  v-else-if="chapter.download_status !== 'downloading'"
                  @click="downloadChapter(chapter)"
                  class="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
                  title="Download Chapter"
                >
                  Download
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- No Volumes Message -->
      <div v-else-if="showChapters && volumes.length === 0" class="text-center py-8">
        <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No chapters available</h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          This manga doesn't have any chapters yet.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const props = defineProps({
  manga: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["remove", "download", "import"]);

// Reactive data
const showChapters = ref(false);

// Computed properties
const getMangaId = computed(() => {
  return props.manga.manga_id || props.manga.id;
});

const getLibraryItemId = computed(() => {
  return props.manga.id;
});

const getMangaTitle = computed(() => {
  return props.manga.title || props.manga.manga?.title || "Unknown Title";
});

const getMangaAuthor = computed(() => {
  return props.manga.author || props.manga.manga?.author;
});

const getMangaCover = computed(() => {
  // Check for custom cover first (library items)
  if (props.manga.custom_cover) {
    return props.manga.custom_cover;
  }
  // Check nested manga object
  if (props.manga.manga && props.manga.manga.cover_image) {
    return props.manga.manga.cover_image;
  }
  // Direct manga object
  return props.manga.cover_image || props.manga.cover_url || "/placeholder-cover.jpg";
});

const getMangaDescription = computed(() => {
  return props.manga.description || props.manga.manga?.description;
});

const getMangaStatus = computed(() => {
  return props.manga.status || props.manga.manga?.status;
});

const getMangaGenres = computed(() => {
  const genres = props.manga.genres || props.manga.manga?.genres;
  if (Array.isArray(genres)) {
    // Handle array of genre objects or strings
    return genres.map(genre => {
      if (typeof genre === 'object' && genre.name) {
        return genre.name;
      }
      return genre;
    }).join(", ");
  }
  return genres || "";
});

const volumes = computed(() => {
  return props.manga.volumes || props.manga.manga?.volumes || [];
});

const totalChapters = computed(() => {
  return volumes.value.reduce((total, volume) => total + (volume.chapters?.length || 0), 0);
});

const downloadedChapters = computed(() => {
  return volumes.value.reduce((total, volume) => {
    return total + (volume.chapters?.filter(ch => ch.download_status === 'downloaded').length || 0);
  }, 0);
});

const downloadProgress = computed(() => {
  if (totalChapters.value === 0) return 0;
  return Math.round((downloadedChapters.value / totalChapters.value) * 100);
});

// Methods
const formatDate = (dateString) => {
  if (!dateString) return 'Unknown';
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

const getStatusBadgeClass = (status) => {
  switch (status?.toLowerCase()) {
    case 'ongoing':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'completed':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case 'hiatus':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'cancelled':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

const getVolumeDownloadedCount = (volume) => {
  return volume.chapters?.filter(ch => ch.download_status === 'downloaded').length || 0;
};

const isVolumeFullyDownloaded = (volume) => {
  return getVolumeDownloadedCount(volume) === (volume.chapters?.length || 0);
};

const downloadVolume = (volume) => {
  // Emit download event for each chapter in the volume
  volume.chapters?.forEach(chapter => {
    if (chapter.download_status !== 'downloaded') {
      downloadChapter(chapter);
    }
  });
};

const downloadChapter = (chapter) => {
  // This would typically call an API to download the chapter
  console.log('Downloading chapter:', chapter);
  // For now, just emit a download event
  emit('download', getLibraryItemId.value, chapter);
};

const readChapter = (chapter) => {
  router.push(`/read/${getMangaId.value}/${chapter.id}`);
};
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
