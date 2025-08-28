<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto" @click="closeModal">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>

      <!-- Modal panel -->
      <div class="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-dark-800 rounded-lg shadow-xl z-50 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto" @click.stop>
        <!-- Header -->
        <div class="bg-white dark:bg-dark-800 px-6 pt-6 pb-4">
          <div class="flex items-start justify-between">
            <div class="flex items-center space-x-4">
              <!-- Cover Image -->
              <div class="flex-shrink-0">
                <div class="w-24 h-36 bg-gray-200 dark:bg-dark-700 rounded-lg overflow-hidden">
                  <img
                    v-if="manga.cover_image"
                    :src="manga.cover_image"
                    :alt="manga.title"
                    class="w-full h-full object-cover"
                    :class="{ 'blur-md': manga.is_nsfw && blurNsfw }"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                    <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
              </div>

              <!-- Title and Basic Info -->
              <div class="flex-1">
                <h3 class="text-xl font-bold text-gray-900 dark:text-white">
                  {{ manga.title }}
                </h3>
                
                <!-- Status Badges -->
                <div class="flex flex-wrap gap-2 mt-2">
                  <span v-if="manga.is_nsfw" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                    NSFW
                  </span>
                  <span v-if="manga.in_library" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                    In Library
                  </span>
                  <span v-if="manga.type" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                    {{ manga.type }}
                  </span>
                  <span v-if="manga.year" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                    {{ manga.year }}
                  </span>
                </div>

                <!-- Provider Info -->
                <div class="mt-3 flex items-center space-x-2">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Source:</span>
                  <span class="text-sm text-primary-600 dark:text-primary-400">
                    {{ formatProviderName(manga.provider) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Close Button -->
            <button
              @click="closeModal"
              class="bg-white dark:bg-dark-800 rounded-md text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <span class="sr-only">Close</span>
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="bg-white dark:bg-dark-800 px-6 pb-4">
          <!-- Additional Metadata -->
          <div v-if="hasAdditionalMetadata" class="mb-6">
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div v-if="manga.rating" class="text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white flex items-center justify-center">
                  <svg class="w-5 h-5 text-yellow-400 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  {{ formatRating(manga.rating) }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400">Rating</div>
              </div>

              <div v-if="manga.status" class="text-center">
                <div class="text-lg font-bold text-gray-900 dark:text-white">{{ formatStatus(manga.status) }}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">Status</div>
              </div>

              <div v-if="manga.latest_chapter" class="text-center">
                <div class="text-lg font-bold text-gray-900 dark:text-white">{{ manga.latest_chapter }}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">Latest Chapter</div>
              </div>

              <div v-if="manga.total_chapters" class="text-center">
                <div class="text-lg font-bold text-gray-900 dark:text-white">{{ manga.total_chapters }}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">Total Chapters</div>
              </div>
            </div>
          </div>

          <!-- Description -->
          <div v-if="manga.description" class="mb-6">
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-lg font-medium text-gray-900 dark:text-white">Description</h4>
              <button
                v-if="isDescriptionLong"
                @click="toggleDescription"
                class="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 flex items-center"
              >
                {{ showFullDescription ? 'Show Less' : 'Show More' }}
                <svg
                  class="ml-1 w-4 h-4 transition-transform duration-200"
                  :class="{ 'rotate-180': showFullDescription }"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
            <div class="prose prose-sm dark:prose-invert max-w-none">
              <p
                class="text-gray-700 dark:text-gray-300 leading-relaxed transition-all duration-300"
                :class="{ 'line-clamp-6': !showFullDescription && isDescriptionLong }"
              >
                {{ manga.description }}
              </p>
            </div>
          </div>

          <!-- Genres -->
          <div v-if="manga.genres && manga.genres.length > 0" class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Genres</h4>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="genre in manga.genres"
                :key="genre"
                class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
              >
                {{ genre }}
              </span>
            </div>
          </div>

          <!-- External Links -->
          <div v-if="manga.url" class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">External Links</h4>
            <div class="space-y-2">
              <a
                :href="manga.url"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
              >
                <span>View on {{ formatProviderName(manga.provider) }}</span>
                <svg class="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="bg-gray-50 dark:bg-dark-700 px-6 py-4 flex justify-end space-x-3">
          <button
            v-if="!manga.in_library"
            @click="addToLibrary"
            type="button"
            class="inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Add to Library
          </button>
          
          <button
            @click="closeModal"
            type="button"
            class="inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MangaDetailsModal',
  
  props: {
    manga: {
      type: Object,
      required: false,
      default: null
    },
    isOpen: {
      type: Boolean,
      default: false
    },
    blurNsfw: {
      type: Boolean,
      default: true
    }
  },
  
  emits: ['close', 'add-to-library'],
  
  data() {
    return {
      showDebugInfo: false,
      showFullDescription: false
    };
  },

  computed: {
    hasAdditionalMetadata() {
      return this.manga?.rating || this.manga?.status || this.manga?.latest_chapter || this.manga?.total_chapters;
    },

    isDescriptionLong() {
      if (!this.manga?.description) return false;
      // Consider description long if it's more than 300 characters or has more than 4 lines
      return this.manga.description.length > 300 || this.manga.description.split('\n').length > 4;
    }
  },

  methods: {
    closeModal() {
      this.$emit('close');
    },

    async addToLibrary() {
      try {
        this.$emit('add-to-library', this.manga);
      } catch (error) {
        console.error('Error adding to library:', error);
      }
    },

    formatProviderName(provider) {
      const nameMap = {
        'mangaupdates': 'MangaUpdates',
        'enhanced_mangaupdates': 'MangaUpdates',
        'madaradex': 'MadaraDex',
        'mangadex': 'MangaDex'
      };
      return nameMap[provider?.toLowerCase()] || provider || 'Unknown';
    },

    formatRating(rating) {
      if (typeof rating === 'number') {
        return rating.toFixed(1);
      }
      return rating || 'N/A';
    },

    formatStatus(status) {
      if (!status) return 'Unknown';
      return status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ');
    },

    toggleDescription() {
      this.showFullDescription = !this.showFullDescription;
    }
  }
};
</script>

<style scoped>
.prose {
  max-width: none;
}

.line-clamp-6 {
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
