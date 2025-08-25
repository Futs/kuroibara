<template>
  <div class="metadata-comparison bg-white dark:bg-dark-800 rounded-lg shadow-md p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-medium text-gray-900 dark:text-white">
        Metadata Comparison
      </h3>
      <button
        @click="$emit('close')"
        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div class="space-y-6">
      <!-- Title Comparison -->
      <div v-if="hasMultipleTitles" class="comparison-section">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Titles</h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            v-for="source in sources" 
            :key="source.name"
            class="source-column"
          >
            <div class="source-header">
              <div class="flex items-center gap-2 mb-2">
                <div 
                  class="w-3 h-3 rounded-full"
                  :class="getSourceTierColor(source.name)"
                ></div>
                <span class="text-sm font-medium">{{ formatSourceName(source.name) }}</span>
              </div>
            </div>
            <div class="source-content">
              <p class="text-sm text-gray-900 dark:text-white font-medium">
                {{ source.data.title || 'N/A' }}
              </p>
              <div v-if="source.data.alternative_titles" class="mt-1">
                <div 
                  v-for="(title, lang) in source.data.alternative_titles" 
                  :key="lang"
                  class="text-xs text-gray-600 dark:text-gray-400"
                >
                  {{ lang }}: {{ title }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Description Comparison -->
      <div v-if="hasMultipleDescriptions" class="comparison-section">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Descriptions</h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            v-for="source in sources" 
            :key="source.name"
            class="source-column"
          >
            <div class="source-header">
              <div class="flex items-center gap-2 mb-2">
                <div 
                  class="w-3 h-3 rounded-full"
                  :class="getSourceTierColor(source.name)"
                ></div>
                <span class="text-sm font-medium">{{ formatSourceName(source.name) }}</span>
              </div>
            </div>
            <div class="source-content">
              <p class="text-sm text-gray-700 dark:text-gray-300 line-clamp-4">
                {{ source.data.description || 'No description available' }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Genres Comparison -->
      <div v-if="hasMultipleGenres" class="comparison-section">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Genres</h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            v-for="source in sources" 
            :key="source.name"
            class="source-column"
          >
            <div class="source-header">
              <div class="flex items-center gap-2 mb-2">
                <div 
                  class="w-3 h-3 rounded-full"
                  :class="getSourceTierColor(source.name)"
                ></div>
                <span class="text-sm font-medium">{{ formatSourceName(source.name) }}</span>
              </div>
            </div>
            <div class="source-content">
              <div v-if="source.data.genres && source.data.genres.length > 0" class="flex flex-wrap gap-1">
                <span
                  v-for="genre in source.data.genres"
                  :key="genre"
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                >
                  {{ genre }}
                </span>
              </div>
              <span v-else class="text-sm text-gray-500 dark:text-gray-400">No genres available</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Rating Comparison -->
      <div v-if="hasMultipleRatings" class="comparison-section">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Ratings</h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            v-for="source in sources" 
            :key="source.name"
            class="source-column"
          >
            <div class="source-header">
              <div class="flex items-center gap-2 mb-2">
                <div 
                  class="w-3 h-3 rounded-full"
                  :class="getSourceTierColor(source.name)"
                ></div>
                <span class="text-sm font-medium">{{ formatSourceName(source.name) }}</span>
              </div>
            </div>
            <div class="source-content">
              <div v-if="source.data.rating" class="flex items-center gap-2">
                <div class="flex items-center">
                  <svg class="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  <span class="text-sm font-medium">{{ formatRating(source.data.rating) }}</span>
                </div>
                <span v-if="source.data.rating_votes" class="text-xs text-gray-500 dark:text-gray-400">
                  ({{ formatNumber(source.data.rating_votes) }} votes)
                </span>
              </div>
              <span v-else class="text-sm text-gray-500 dark:text-gray-400">No rating available</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Status and Type Comparison -->
      <div v-if="hasMultipleStatusOrType" class="comparison-section">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status & Type</h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            v-for="source in sources" 
            :key="source.name"
            class="source-column"
          >
            <div class="source-header">
              <div class="flex items-center gap-2 mb-2">
                <div 
                  class="w-3 h-3 rounded-full"
                  :class="getSourceTierColor(source.name)"
                ></div>
                <span class="text-sm font-medium">{{ formatSourceName(source.name) }}</span>
              </div>
            </div>
            <div class="source-content space-y-1">
              <div v-if="source.data.type" class="flex items-center gap-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">Type:</span>
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  {{ source.data.type }}
                </span>
              </div>
              <div v-if="source.data.status" class="flex items-center gap-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">Status:</span>
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  {{ source.data.status }}
                </span>
              </div>
              <div v-if="source.data.year" class="flex items-center gap-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">Year:</span>
                <span class="text-sm">{{ source.data.year }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Confidence Scores -->
      <div class="comparison-section">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Confidence Scores</h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            v-for="source in sources" 
            :key="source.name"
            class="source-column"
          >
            <div class="source-header">
              <div class="flex items-center gap-2 mb-2">
                <div 
                  class="w-3 h-3 rounded-full"
                  :class="getSourceTierColor(source.name)"
                ></div>
                <span class="text-sm font-medium">{{ formatSourceName(source.name) }}</span>
              </div>
            </div>
            <div class="source-content">
              <div class="flex items-center gap-2">
                <div class="flex-1 bg-gray-200 dark:bg-dark-600 rounded-full h-2">
                  <div 
                    class="h-2 rounded-full transition-all duration-300"
                    :class="getConfidenceBarColor(source.data.confidence_score)"
                    :style="{ width: `${(source.data.confidence_score || 0) * 100}%` }"
                  ></div>
                </div>
                <span 
                  class="text-sm font-medium"
                  :class="getConfidenceColor(source.data.confidence_score)"
                >
                  {{ Math.round((source.data.confidence_score || 0) * 100) }}%
                </span>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {{ formatConfidence(source.data.confidence_score) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import enhancedSearchService from '../services/enhancedSearchService.js';

export default {
  name: 'MetadataComparison',
  
  props: {
    sources: {
      type: Array,
      required: true
    }
  },
  
  emits: ['close'],
  
  computed: {
    hasMultipleTitles() {
      return this.sources.some(source => 
        source.data.title && source.data.title !== this.sources[0].data.title
      );
    },
    
    hasMultipleDescriptions() {
      return this.sources.some(source => 
        source.data.description && source.data.description !== this.sources[0].data.description
      );
    },
    
    hasMultipleGenres() {
      return this.sources.some(source => 
        source.data.genres && source.data.genres.length > 0
      );
    },
    
    hasMultipleRatings() {
      return this.sources.some(source => source.data.rating);
    },
    
    hasMultipleStatusOrType() {
      return this.sources.some(source => 
        source.data.status || source.data.type || source.data.year
      );
    }
  },
  
  methods: {
    formatSourceName(name) {
      const nameMap = {
        'mangaupdates': 'MangaUpdates',
        'madaradex': 'MadaraDex',
        'mangadex': 'MangaDex'
      };
      return nameMap[name?.toLowerCase()] || name || 'Unknown';
    },
    
    getSourceTierColor(source) {
      const tier = enhancedSearchService.getSourceTier(source);
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
    
    getConfidenceBarColor(score) {
      if (!score) return 'bg-gray-300';
      const percentage = Math.round(score * 100);
      if (percentage >= 90) return 'bg-green-500';
      if (percentage >= 80) return 'bg-green-400';
      if (percentage >= 70) return 'bg-yellow-400';
      if (percentage >= 60) return 'bg-orange-400';
      return 'bg-red-400';
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
.comparison-section {
  @apply border-b border-gray-200 dark:border-dark-600 pb-4 last:border-b-0;
}

.source-column {
  @apply bg-gray-50 dark:bg-dark-700 rounded-lg p-3;
}

.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
