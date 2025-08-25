<template>
  <div class="enhanced-search-result-card">
    <div class="relative group cursor-pointer bg-white dark:bg-dark-800 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200" @click="viewDetails">
      <!-- Cover Image Section -->
      <div class="aspect-[2/3] rounded-t-lg overflow-hidden bg-gray-200 dark:bg-dark-700 relative">
        <img
          v-if="coverUrl"
          :src="coverUrl"
          :alt="manga.title"
          class="w-full h-full object-center object-cover transition-transform duration-200 group-hover:scale-105"
          :class="{ 'blur-md': isNsfw && blurNsfw }"
          @error="onImageError"
        />
        <div
          v-else
          class="w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-500"
        >
          <svg class="h-12 w-12" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>

        <!-- Source Badge -->
        <div class="absolute top-2 left-2 flex flex-col gap-1">
          <div
            v-if="manga.provider"
            class="bg-gray-800 bg-opacity-90 text-white text-xs px-2 py-1 rounded flex items-center gap-1"
          >
            <div 
              class="w-2 h-2 rounded-full"
              :class="getSourceTierColor(manga.provider)"
            ></div>
            {{ formatProviderName(manga.provider) }}
          </div>
          
          <!-- Confidence Score Badge -->
          <div
            v-if="manga.confidence_score"
            class="bg-blue-600 bg-opacity-90 text-white text-xs px-2 py-1 rounded"
            :title="`Confidence: ${Math.round(manga.confidence_score * 100)}%`"
          >
            {{ formatConfidence(manga.confidence_score) }}
          </div>
        </div>

        <!-- Top Right Badges -->
        <div class="absolute top-2 right-2 flex flex-col gap-1">
          <!-- NSFW Badge -->
          <div
            v-if="isNsfw"
            class="bg-red-500 text-white text-xs font-bold px-2 py-1 rounded"
          >
            NSFW
          </div>

          <!-- In Library Badge -->
          <div
            v-if="manga.in_library"
            class="bg-green-500 text-white text-xs font-bold px-2 py-1 rounded"
          >
            IN LIBRARY
          </div>

          <!-- Rating Badge -->
          <div
            v-if="manga.rating"
            class="bg-yellow-500 text-white text-xs font-bold px-2 py-1 rounded flex items-center gap-1"
          >
            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            {{ formatRating(manga.rating) }}
          </div>
        </div>
      </div>

      <!-- Content Section -->
      <div class="p-4">
        <!-- Title -->
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
          {{ manga.title }}
        </h3>

        <!-- Alternative Titles -->
        <div v-if="hasAlternativeTitles" class="mb-2">
          <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-1">
            Also known as: {{ getAlternativeTitlesText() }}
          </p>
        </div>

        <!-- Description -->
        <div v-if="manga.description" class="mb-3">
          <p class="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
            {{ manga.description }}
          </p>
        </div>

        <!-- Rating and Statistics Row -->
        <div v-if="hasRatingOrStats" class="flex items-center gap-3 mb-3 text-xs text-gray-600 dark:text-gray-400">
          <!-- Rating -->
          <div v-if="manga.rating" class="flex items-center gap-1">
            <svg class="w-3 h-3 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            <span>{{ formatRating(manga.rating) }}</span>
            <span v-if="manga.rating_votes" class="text-gray-500">({{ formatNumber(manga.rating_votes) }})</span>
          </div>

          <!-- Latest Chapter -->
          <div v-if="manga.latest_chapter" class="flex items-center gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span>Ch. {{ manga.latest_chapter }}</span>
          </div>

          <!-- Popularity -->
          <div v-if="manga.popularity" class="flex items-center gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <span>#{{ formatNumber(manga.popularity) }}</span>
          </div>
        </div>

        <!-- Metadata Row -->
        <div class="flex flex-wrap gap-2 mb-3">
          <!-- Type -->
          <span v-if="manga.type" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
            {{ manga.type }}
          </span>

          <!-- Status -->
          <span v-if="manga.status" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
            {{ manga.status }}
          </span>

          <!-- Year -->
          <span v-if="manga.year" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
            {{ manga.year }}
          </span>
        </div>

        <!-- Genres -->
        <div v-if="manga.genres && manga.genres.length > 0" class="mb-3">
          <div class="flex flex-wrap gap-1">
            <span
              v-for="genre in displayGenres"
              :key="genre"
              class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
            >
              {{ genre }}
            </span>
            <span
              v-if="manga.genres.length > maxGenres"
              class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
            >
              +{{ manga.genres.length - maxGenres }} more
            </span>
          </div>
        </div>

        <!-- Authors -->
        <div v-if="manga.authors && manga.authors.length > 0" class="mb-3">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            <span class="font-medium">Authors:</span> {{ manga.authors.join(', ') }}
          </p>
        </div>

        <!-- Action Buttons -->
        <div class="flex justify-between items-center pt-2 border-t border-gray-200 dark:border-dark-600">
          <button
            @click.stop="viewDetails"
            class="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 text-sm font-medium"
          >
            View Details
          </button>
          
          <div class="flex gap-2">
            <button
              v-if="!manga.in_library"
              @click.stop="addToLibrary"
              class="bg-primary-600 hover:bg-primary-700 text-white text-xs px-3 py-1 rounded transition-colors duration-200"
            >
              Add to Library
            </button>
            
            <button
              @click.stop="openExternalLink"
              class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              :title="`View on ${formatProviderName(manga.provider)}`"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import enhancedSearchService from '../services/enhancedSearchService.js';

export default {
  name: 'EnhancedSearchResultCard',
  props: {
    manga: {
      type: Object,
      required: true
    },
    blurNsfw: {
      type: Boolean,
      default: true
    },
    maxGenres: {
      type: Number,
      default: 3
    }
  },
  
  emits: ['view-details', 'add-to-library'],
  
  data() {
    return {
      imageError: false
    };
  },
  
  computed: {
    coverUrl() {
      if (this.imageError) return null;
      return this.manga.cover_image || this.manga.cover_url || null;
    },
    
    isNsfw() {
      return this.manga.is_nsfw || false;
    },
    
    hasAlternativeTitles() {
      return this.manga.alternative_titles && 
             Object.keys(this.manga.alternative_titles).length > 0;
    },
    
    displayGenres() {
      if (!this.manga.genres) return [];
      return this.manga.genres.slice(0, this.maxGenres);
    },

    hasRatingOrStats() {
      return this.manga.rating || this.manga.rating_votes ||
             this.manga.popularity || this.manga.latest_chapter;
    }
  },
  
  methods: {
    onImageError() {
      this.imageError = true;
    },
    
    viewDetails() {
      this.$emit('view-details', this.manga);
    },
    
    addToLibrary() {
      this.$emit('add-to-library', this.manga);
    },
    
    openExternalLink() {
      if (this.manga.url || this.manga.source_url) {
        window.open(this.manga.url || this.manga.source_url, '_blank');
      }
    },
    
    formatProviderName(provider) {
      if (!provider) return 'Unknown';
      
      const nameMap = {
        'mangaupdates': 'MangaUpdates',
        'madaradex': 'MadaraDex',
        'mangadex': 'MangaDex'
      };
      
      return nameMap[provider.toLowerCase()] || provider;
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
    
    formatRating(rating) {
      if (typeof rating === 'number') {
        return rating.toFixed(1);
      }
      return rating;
    },
    
    getAlternativeTitlesText() {
      if (!this.hasAlternativeTitles) return '';

      const titles = Object.values(this.manga.alternative_titles);
      return titles.slice(0, 2).join(', ') + (titles.length > 2 ? '...' : '');
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

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
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
