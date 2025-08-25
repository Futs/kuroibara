<template>
  <div class="search-results-grid">
    <!-- View Controls -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-4">
        <!-- View Mode Toggle -->
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-600 dark:text-gray-400">View:</span>
          <div class="flex rounded-lg border border-gray-300 dark:border-dark-600">
            <button
              @click="setViewMode('grid')"
              class="px-3 py-1 text-sm rounded-l-lg transition-colors"
              :class="viewMode === 'grid' 
                ? 'bg-primary-600 text-white' 
                : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700'"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              @click="setViewMode('list')"
              class="px-3 py-1 text-sm transition-colors"
              :class="viewMode === 'list' 
                ? 'bg-primary-600 text-white' 
                : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700'"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </button>
            <button
              @click="setViewMode('detailed')"
              class="px-3 py-1 text-sm rounded-r-lg transition-colors"
              :class="viewMode === 'detailed' 
                ? 'bg-primary-600 text-white' 
                : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700'"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Sort Options -->
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-600 dark:text-gray-400">Sort:</span>
          <select
            v-model="sortBy"
            @change="handleSortChange"
            class="text-sm border border-gray-300 dark:border-dark-600 rounded-md px-2 py-1 bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-300"
          >
            <option value="relevance">Relevance</option>
            <option value="confidence">Confidence</option>
            <option value="rating">Rating</option>
            <option value="title">Title</option>
            <option value="year">Year</option>
            <option value="source">Source</option>
          </select>
        </div>

        <!-- Metadata Toggle -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-gray-600 dark:text-gray-400">Show Metadata:</label>
          <button
            @click="toggleMetadataDisplay"
            class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            :class="showMetadata ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'"
          >
            <span
              class="inline-block h-3 w-3 transform rounded-full bg-white transition-transform"
              :class="showMetadata ? 'translate-x-5' : 'translate-x-1'"
            ></span>
          </button>
        </div>
      </div>

      <!-- Results Count -->
      <div class="text-sm text-gray-600 dark:text-gray-400">
        {{ sortedResults.length }} results
      </div>
    </div>

    <!-- Results Grid/List -->
    <div v-if="sortedResults.length > 0">
      <!-- Grid View -->
      <div 
        v-if="viewMode === 'grid'"
        class="grid gap-4"
        :class="gridCols"
      >
        <EnhancedSearchResultCard
          v-for="result in sortedResults"
          :key="result.id"
          :manga="result"
          :blur-nsfw="blurNsfw"
          :max-genres="showMetadata ? 5 : 3"
          @view-details="$emit('view-details', result)"
          @add-to-library="$emit('add-to-library', result)"
        />
      </div>

      <!-- List View -->
      <div 
        v-else-if="viewMode === 'list'"
        class="space-y-2"
      >
        <div
          v-for="result in sortedResults"
          :key="result.id"
          class="flex items-center gap-4 p-4 bg-white dark:bg-dark-800 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
          @click="$emit('view-details', result)"
        >
          <!-- Cover Image -->
          <div class="flex-shrink-0 w-12 h-18 bg-gray-200 dark:bg-dark-700 rounded overflow-hidden">
            <img
              v-if="result.cover_image"
              :src="result.cover_image"
              :alt="result.title"
              class="w-full h-full object-cover"
              :class="{ 'blur-sm': result.is_nsfw && blurNsfw }"
            />
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h3 class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ result.title }}
                </h3>
                <p v-if="result.description" class="text-xs text-gray-600 dark:text-gray-400 line-clamp-1 mt-1">
                  {{ result.description }}
                </p>
              </div>
              
              <!-- Metadata -->
              <div class="flex items-center gap-2 ml-4">
                <!-- Source -->
                <div class="flex items-center gap-1">
                  <div 
                    class="w-2 h-2 rounded-full"
                    :class="getSourceTierColor(result.provider)"
                  ></div>
                  <span class="text-xs text-gray-500">{{ formatProviderName(result.provider) }}</span>
                </div>

                <!-- Confidence -->
                <span 
                  v-if="result.confidence_score"
                  class="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                >
                  {{ Math.round(result.confidence_score * 100) }}%
                </span>

                <!-- Rating -->
                <div v-if="result.rating" class="flex items-center gap-1">
                  <svg class="w-3 h-3 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  <span class="text-xs">{{ formatRating(result.rating) }}</span>
                </div>

                <!-- NSFW Badge -->
                <span v-if="result.is_nsfw" class="text-xs px-2 py-1 rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                  NSFW
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Detailed View -->
      <div 
        v-else-if="viewMode === 'detailed'"
        class="space-y-6"
      >
        <div
          v-for="result in sortedResults"
          :key="result.id"
          class="bg-white dark:bg-dark-800 rounded-lg shadow-sm p-6"
        >
          <div class="flex gap-6">
            <!-- Cover Image -->
            <div class="flex-shrink-0 w-24 h-36 bg-gray-200 dark:bg-dark-700 rounded-lg overflow-hidden">
              <img
                v-if="result.cover_image"
                :src="result.cover_image"
                :alt="result.title"
                class="w-full h-full object-cover"
                :class="{ 'blur-md': result.is_nsfw && blurNsfw }"
              />
            </div>

            <!-- Content -->
            <div class="flex-1">
              <div class="flex items-start justify-between mb-4">
                <div>
                  <h3 class="text-lg font-medium text-gray-900 dark:text-white">
                    {{ result.title }}
                  </h3>
                  <div class="flex items-center gap-4 mt-2">
                    <!-- Source -->
                    <div class="flex items-center gap-2">
                      <div 
                        class="w-3 h-3 rounded-full"
                        :class="getSourceTierColor(result.provider)"
                      ></div>
                      <span class="text-sm text-gray-600 dark:text-gray-400">
                        {{ formatProviderName(result.provider) }}
                      </span>
                    </div>

                    <!-- Confidence -->
                    <div v-if="result.confidence_score" class="flex items-center gap-2">
                      <span class="text-sm text-gray-600 dark:text-gray-400">Confidence:</span>
                      <span 
                        class="text-sm font-medium"
                        :class="getConfidenceColor(result.confidence_score)"
                      >
                        {{ Math.round(result.confidence_score * 100) }}%
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Actions -->
                <div class="flex gap-2">
                  <button
                    @click="$emit('view-details', result)"
                    class="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 text-sm font-medium"
                  >
                    View Details
                  </button>
                  <button
                    v-if="!result.in_library"
                    @click="$emit('add-to-library', result)"
                    class="bg-primary-600 hover:bg-primary-700 text-white text-sm px-3 py-1 rounded transition-colors"
                  >
                    Add to Library
                  </button>
                </div>
              </div>

              <!-- Description -->
              <p v-if="result.description" class="text-sm text-gray-700 dark:text-gray-300 mb-4 line-clamp-3">
                {{ result.description }}
              </p>

              <!-- Metadata -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <!-- Type & Status -->
                <div v-if="result.type || result.status">
                  <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Type & Status</div>
                  <div class="space-y-1">
                    <span v-if="result.type" class="inline-block text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                      {{ result.type }}
                    </span>
                    <span v-if="result.status" class="inline-block text-xs px-2 py-1 rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                      {{ result.status }}
                    </span>
                  </div>
                </div>

                <!-- Rating -->
                <div v-if="result.rating">
                  <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Rating</div>
                  <div class="flex items-center gap-1">
                    <svg class="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    <span class="text-sm font-medium">{{ formatRating(result.rating) }}</span>
                    <span v-if="result.rating_votes" class="text-xs text-gray-500">({{ formatNumber(result.rating_votes) }})</span>
                  </div>
                </div>

                <!-- Year -->
                <div v-if="result.year">
                  <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Year</div>
                  <div class="text-sm">{{ result.year }}</div>
                </div>

                <!-- Latest Chapter -->
                <div v-if="result.latest_chapter">
                  <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Latest Chapter</div>
                  <div class="text-sm">{{ result.latest_chapter }}</div>
                </div>
              </div>

              <!-- Genres -->
              <div v-if="result.genres && result.genres.length > 0" class="mt-4">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-2">Genres</div>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="genre in result.genres.slice(0, showMetadata ? 10 : 5)"
                    :key="genre"
                    class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                  >
                    {{ genre }}
                  </span>
                  <span
                    v-if="result.genres.length > (showMetadata ? 10 : 5)"
                    class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
                  >
                    +{{ result.genres.length - (showMetadata ? 10 : 5) }} more
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No results found</h3>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Try adjusting your search query or filters.</p>
    </div>
  </div>
</template>

<script>
import EnhancedSearchResultCard from './EnhancedSearchResultCard.vue';
import enhancedSearchService from '../services/enhancedSearchService.js';

export default {
  name: 'SearchResultsGrid',
  
  components: {
    EnhancedSearchResultCard
  },
  
  props: {
    results: {
      type: Array,
      default: () => []
    },
    blurNsfw: {
      type: Boolean,
      default: true
    }
  },
  
  emits: ['view-details', 'add-to-library'],
  
  data() {
    return {
      viewMode: 'grid', // 'grid', 'list', 'detailed'
      sortBy: 'relevance',
      showMetadata: false
    };
  },
  
  computed: {
    gridCols() {
      switch (this.viewMode) {
        case 'grid':
          return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4';
        default:
          return 'grid-cols-1';
      }
    },
    
    sortedResults() {
      const sorted = [...this.results];
      
      switch (this.sortBy) {
        case 'confidence':
          return sorted.sort((a, b) => (b.confidence_score || 0) - (a.confidence_score || 0));
        case 'rating':
          return sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0));
        case 'title':
          return sorted.sort((a, b) => a.title.localeCompare(b.title));
        case 'year':
          return sorted.sort((a, b) => (b.year || 0) - (a.year || 0));
        case 'source':
          return sorted.sort((a, b) => {
            const tierA = this.getSourceTierOrder(a.provider);
            const tierB = this.getSourceTierOrder(b.provider);
            return tierA - tierB;
          });
        case 'relevance':
        default:
          return sorted; // Keep original order (relevance from search)
      }
    }
  },
  
  methods: {
    setViewMode(mode) {
      this.viewMode = mode;
    },
    
    toggleMetadataDisplay() {
      this.showMetadata = !this.showMetadata;
    },
    
    handleSortChange() {
      // Sort change is handled by computed property
    },
    
    formatProviderName(provider) {
      const nameMap = {
        'mangaupdates': 'MangaUpdates',
        'madaradex': 'MadaraDex',
        'mangadex': 'MangaDex'
      };
      return nameMap[provider?.toLowerCase()] || provider || 'Unknown';
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
    
    getSourceTierOrder(provider) {
      const tier = enhancedSearchService.getSourceTier(provider);
      const orderMap = {
        'primary': 1,
        'secondary': 2,
        'tertiary': 3,
        'unknown': 4
      };
      return orderMap[tier] || 4;
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
      if (!num) return '';
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
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
