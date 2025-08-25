<template>
  <div v-if="isOpen && manga" class="fixed inset-0 z-50 overflow-y-auto" @click="closeModal">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>

      <!-- Modal panel -->
      <div 
        class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full"
        @click.stop
      >
        <!-- Header -->
        <div class="bg-white dark:bg-dark-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
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
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
              </div>

              <!-- Title and Basic Info -->
              <div class="flex-1">
                <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                  {{ manga.title }}
                </h3>
                
                <!-- Alternative Titles -->
                <div v-if="hasAlternativeTitles" class="mt-2">
                  <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Alternative Titles:</h4>
                  <div class="space-y-1">
                    <div 
                      v-for="(title, lang) in manga.alternative_titles" 
                      :key="lang"
                      class="text-sm text-gray-600 dark:text-gray-400"
                    >
                      <span class="font-medium">{{ formatLanguage(lang) }}:</span> {{ title }}
                    </div>
                  </div>
                </div>

                <!-- Source and Confidence -->
                <div class="mt-3 flex items-center space-x-4">
                  <div class="flex items-center space-x-2">
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Source:</span>
                    <div class="flex items-center space-x-1">
                      <div 
                        class="w-2 h-2 rounded-full"
                        :class="getSourceTierColor(manga.provider)"
                      ></div>
                      <span class="text-sm text-gray-600 dark:text-gray-400">
                        {{ formatProviderName(manga.provider) }}
                      </span>
                    </div>
                  </div>
                  
                  <div v-if="manga.confidence_score" class="flex items-center space-x-2">
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Confidence:</span>
                    <span 
                      class="text-sm font-medium"
                      :class="getConfidenceColor(manga.confidence_score)"
                    >
                      {{ formatConfidence(manga.confidence_score) }} ({{ Math.round(manga.confidence_score * 100) }}%)
                    </span>
                  </div>
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
        <div class="bg-white dark:bg-dark-800 px-4 pb-4 sm:px-6 sm:pb-6">
          <!-- Status Badges -->
          <div class="flex flex-wrap gap-2 mb-4">
            <!-- NSFW Badge -->
            <span v-if="manga.is_nsfw" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
              NSFW
            </span>

            <!-- In Library Badge -->
            <span v-if="manga.in_library" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
              In Library
            </span>

            <!-- Type -->
            <span v-if="manga.type" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {{ manga.type }}
            </span>

            <!-- Status -->
            <span v-if="manga.status" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
              {{ manga.status }}
            </span>

            <!-- Year -->
            <span v-if="manga.year" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
              {{ manga.year }}
            </span>
          </div>

          <!-- Rating and Statistics -->
          <div v-if="hasRatingOrStats" class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <div v-if="manga.rating" class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white flex items-center justify-center">
                <svg class="w-5 h-5 text-yellow-400 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                {{ formatRating(manga.rating) }}
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Rating</div>
            </div>

            <div v-if="manga.rating_votes" class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ formatNumber(manga.rating_votes) }}</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Votes</div>
            </div>

            <div v-if="manga.popularity" class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ formatNumber(manga.popularity) }}</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Popularity</div>
            </div>

            <div v-if="manga.latest_chapter" class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ manga.latest_chapter }}</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Latest Chapter</div>
            </div>
          </div>

          <!-- Description -->
          <div v-if="manga.description" class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Description</h4>
            <div class="prose prose-sm dark:prose-invert max-w-none">
              <p class="text-gray-700 dark:text-gray-300 leading-relaxed">
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

          <!-- Authors -->
          <div v-if="manga.authors && manga.authors.length > 0" class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Authors</h4>
            <div class="space-y-1">
              <div 
                v-for="author in manga.authors" 
                :key="author.name || author"
                class="text-gray-700 dark:text-gray-300"
              >
                {{ typeof author === 'string' ? author : author.name }}
                <span v-if="author.role" class="text-sm text-gray-500 dark:text-gray-400 ml-1">({{ author.role }})</span>
              </div>
            </div>
          </div>

          <!-- External Links -->
          <div v-if="manga.url || manga.source_url" class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">External Links</h4>
            <div class="space-y-2">
              <a
                :href="manga.url || manga.source_url"
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

          <!-- Raw Metadata (Debug) -->
          <div v-if="showDebugInfo" class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Debug Information</h4>
            <div class="bg-gray-100 dark:bg-dark-700 rounded-lg p-4">
              <pre class="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">{{ JSON.stringify(manga, null, 2) }}</pre>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="bg-gray-50 dark:bg-dark-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
          <button
            v-if="!manga.in_library"
            @click="addToLibrary"
            type="button"
            class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
          >
            Add to Library
          </button>
          
          <button
            @click="toggleDebugInfo"
            type="button"
            class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
          >
            {{ showDebugInfo ? 'Hide' : 'Show' }} Debug Info
          </button>
          
          <button
            @click="closeModal"
            type="button"
            class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:w-auto sm:text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import enhancedSearchService from '../services/enhancedSearchService.js';

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
      showDebugInfo: false
    };
  },


  
  computed: {
    hasAlternativeTitles() {
      return this.manga.alternative_titles && 
             Object.keys(this.manga.alternative_titles).length > 0;
    },
    
    hasRatingOrStats() {
      return this.manga.rating || this.manga.rating_votes || 
             this.manga.popularity || this.manga.latest_chapter;
    }
  },
  
  methods: {
    closeModal() {
      this.$emit('close');
    },
    
    addToLibrary() {
      this.$emit('add-to-library', this.manga);
    },
    
    toggleDebugInfo() {
      this.showDebugInfo = !this.showDebugInfo;
    },
    
    formatProviderName(provider) {
      const nameMap = {
        'mangaupdates': 'MangaUpdates',
        'madaradex': 'MadaraDex',
        'mangadex': 'MangaDex'
      };
      return nameMap[provider?.toLowerCase()] || provider || 'Unknown';
    },
    
    formatLanguage(lang) {
      const langMap = {
        'en': 'English',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian'
      };
      return langMap[lang] || lang.toUpperCase();
    },
    
    getSourceTierColor(provider) {
      const tier = enhancedSearchService.getSourceTier(provider);
      const colorMap = {
        'primary': 'bg-green-400',
        'secondary': 'bg-yellow-400',
        'tertiary': 'bg-blue-400',
        'unknown': 'bg-gray-400'
      };
      return colorMap[tier] || 'bg-gray-400';
    },
    
    formatConfidence(score) {
      return enhancedSearchService.formatConfidence(score);
    },
    
    getConfidenceColor(score) {
      return enhancedSearchService.getConfidenceColor(score);
    },
    
    formatRating(rating) {
      if (typeof rating === 'number') {
        return rating.toFixed(1);
      }
      return rating;
    },
    
    formatNumber(num) {
      if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
      }
      return num.toString();
    }
  }
};
</script>

<style scoped>
.prose {
  max-width: none;
}
</style>
