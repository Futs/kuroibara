# Frontend Integration Guide

This guide provides examples and recommendations for integrating the new provider monitoring and favorites features into the Vue.js frontend.

## 🔧 Provider Status Integration

### 1. Provider Status Component

Create a component to display provider health status:

```vue
<template>
  <div class="provider-status">
    <div class="provider-grid">
      <div 
        v-for="provider in providers" 
        :key="provider.id"
        :class="getProviderClass(provider)"
        class="provider-card"
      >
        <div class="provider-header">
          <h3>{{ provider.name }}</h3>
          <span :class="getStatusClass(provider.status)" class="status-badge">
            {{ provider.status.toUpperCase() }}
          </span>
        </div>
        
        <div class="provider-details">
          <div class="detail-item">
            <span class="label">Uptime:</span>
            <span class="value">{{ provider.uptime_percentage }}%</span>
          </div>
          
          <div class="detail-item" v-if="provider.response_time">
            <span class="label">Response:</span>
            <span class="value">{{ provider.response_time }}ms</span>
          </div>
          
          <div class="detail-item" v-if="provider.last_check">
            <span class="label">Last Check:</span>
            <span class="value">{{ formatDate(provider.last_check) }}</span>
          </div>
        </div>
        
        <div class="provider-actions">
          <button 
            @click="testProvider(provider.id)"
            :disabled="testing[provider.id]"
            class="test-btn"
          >
            {{ testing[provider.id] ? 'Testing...' : 'Test Now' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProviderStatus',
  data() {
    return {
      providers: [],
      testing: {},
      loading: false
    }
  },
  
  async mounted() {
    await this.loadProviders()
    // Auto-refresh every 5 minutes
    this.refreshInterval = setInterval(this.loadProviders, 300000)
  },
  
  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  },
  
  methods: {
    async loadProviders() {
      try {
        this.loading = true
        const response = await this.$api.get('/providers/')
        this.providers = response.data
      } catch (error) {
        this.$toast.error('Failed to load provider status')
      } finally {
        this.loading = false
      }
    },
    
    async testProvider(providerId) {
      try {
        this.$set(this.testing, providerId, true)
        await this.$api.post(`/providers/${providerId}/test`)
        this.$toast.success('Provider test completed')
        await this.loadProviders() // Refresh status
      } catch (error) {
        this.$toast.error('Provider test failed')
      } finally {
        this.$set(this.testing, providerId, false)
      }
    },
    
    getProviderClass(provider) {
      return {
        'provider-card': true,
        'provider-healthy': provider.is_healthy,
        'provider-unhealthy': !provider.is_healthy,
        'provider-disabled': !provider.is_enabled
      }
    },
    
    getStatusClass(status) {
      return {
        'status-active': status === 'active',
        'status-down': status === 'down',
        'status-unknown': status === 'unknown',
        'status-testing': status === 'testing'
      }
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleString()
    }
  }
}
</script>

<style scoped>
.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.provider-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.2s;
}

.provider-healthy {
  border-color: #10b981;
  background-color: #f0fdf4;
}

.provider-unhealthy {
  border-color: #ef4444;
  background-color: #fef2f2;
  opacity: 0.7;
}

.provider-disabled {
  opacity: 0.5;
  filter: grayscale(100%);
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: bold;
}

.status-active { background-color: #10b981; color: white; }
.status-down { background-color: #ef4444; color: white; }
.status-unknown { background-color: #6b7280; color: white; }
.status-testing { background-color: #f59e0b; color: white; }
</style>
```

### 2. Search Provider Filter

Integrate provider status into search results:

```vue
<template>
  <div class="search-providers">
    <h3>Search Providers</h3>
    <div class="provider-list">
      <label 
        v-for="provider in providers" 
        :key="provider.id"
        :class="getProviderLabelClass(provider)"
        class="provider-option"
      >
        <input 
          type="checkbox" 
          :value="provider.id"
          v-model="selectedProviders"
          :disabled="!provider.is_healthy"
        />
        <span class="provider-name">{{ provider.name }}</span>
        <span :class="getStatusIndicatorClass(provider)" class="status-indicator"></span>
        <span v-if="provider.response_time" class="response-time">
          {{ provider.response_time }}ms
        </span>
      </label>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SearchProviders',
  props: {
    modelValue: {
      type: Array,
      default: () => []
    }
  },
  
  emits: ['update:modelValue'],
  
  computed: {
    selectedProviders: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    }
  },
  
  methods: {
    getProviderLabelClass(provider) {
      return {
        'provider-option': true,
        'provider-disabled': !provider.is_healthy,
        'provider-slow': provider.response_time > 5000
      }
    },
    
    getStatusIndicatorClass(provider) {
      return {
        'status-indicator': true,
        'status-green': provider.status === 'active',
        'status-red': provider.status === 'down',
        'status-gray': provider.status === 'unknown'
      }
    }
  }
}
</script>
```

## ⭐ Favorites Integration

### 1. Favorites Button Component

```vue
<template>
  <button 
    @click="toggleFavorite"
    :disabled="loading"
    :class="favoriteClass"
    class="favorite-btn"
    :title="favoriteTitle"
  >
    <svg class="star-icon" viewBox="0 0 24 24">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
    </svg>
  </button>
</template>

<script>
export default {
  name: 'FavoriteButton',
  props: {
    mangaId: {
      type: String,
      required: true
    },
    initialFavorite: {
      type: Boolean,
      default: false
    }
  },
  
  data() {
    return {
      isFavorite: this.initialFavorite,
      loading: false
    }
  },
  
  computed: {
    favoriteClass() {
      return {
        'favorite-btn': true,
        'favorite-active': this.isFavorite,
        'favorite-loading': this.loading
      }
    },
    
    favoriteTitle() {
      return this.isFavorite ? 'Remove from favorites' : 'Add to favorites'
    }
  },
  
  methods: {
    async toggleFavorite() {
      try {
        this.loading = true
        
        if (this.isFavorite) {
          await this.$api.delete(`/favorites/${this.mangaId}`)
          this.isFavorite = false
          this.$toast.success('Removed from favorites')
        } else {
          await this.$api.post(`/favorites/${this.mangaId}`)
          this.isFavorite = true
          this.$toast.success('Added to favorites')
        }
        
        this.$emit('favoriteChanged', {
          mangaId: this.mangaId,
          isFavorite: this.isFavorite
        })
        
      } catch (error) {
        this.$toast.error('Failed to update favorites')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.favorite-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.2s;
}

.star-icon {
  width: 24px;
  height: 24px;
  fill: #d1d5db;
  stroke: #6b7280;
  stroke-width: 1;
}

.favorite-active .star-icon {
  fill: #fbbf24;
  stroke: #f59e0b;
}

.favorite-btn:hover .star-icon {
  fill: #fbbf24;
  transform: scale(1.1);
}

.favorite-loading {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

### 2. Favorites Page Component

```vue
<template>
  <div class="favorites-page">
    <div class="favorites-header">
      <h1>My Favorites</h1>
      <div class="favorites-controls">
        <input 
          v-model="searchQuery"
          placeholder="Search favorites..."
          class="search-input"
        />
        <select v-model="sortBy" class="sort-select">
          <option value="updated_at">Recently Updated</option>
          <option value="created_at">Recently Added</option>
          <option value="title">Title</option>
          <option value="rating">Rating</option>
        </select>
        <button @click="exportFavorites" class="export-btn">
          Export
        </button>
      </div>
    </div>
    
    <div v-if="loading" class="loading">
      Loading favorites...
    </div>
    
    <div v-else-if="favorites.length === 0" class="empty-state">
      <p>No favorites found</p>
      <router-link to="/search" class="search-link">
        Browse manga to add favorites
      </router-link>
    </div>
    
    <div v-else class="favorites-grid">
      <div 
        v-for="favorite in favorites" 
        :key="favorite.id"
        class="favorite-card"
      >
        <img 
          :src="favorite.manga.cover_image || '/placeholder.jpg'"
          :alt="favorite.manga.title"
          class="manga-cover"
        />
        <div class="manga-info">
          <h3>{{ favorite.manga.title }}</h3>
          <p class="manga-description">
            {{ truncateDescription(favorite.manga.description) }}
          </p>
          <div class="manga-meta">
            <span v-if="favorite.rating" class="rating">
              ⭐ {{ favorite.rating }}
            </span>
            <span class="added-date">
              Added {{ formatDate(favorite.created_at) }}
            </span>
          </div>
        </div>
        <div class="card-actions">
          <FavoriteButton 
            :manga-id="favorite.manga_id"
            :initial-favorite="true"
            @favorite-changed="onFavoriteChanged"
          />
          <router-link 
            :to="`/manga/${favorite.manga_id}`"
            class="view-btn"
          >
            View
          </router-link>
        </div>
      </div>
    </div>
    
    <div v-if="hasMore" class="load-more">
      <button @click="loadMore" :disabled="loadingMore" class="load-more-btn">
        {{ loadingMore ? 'Loading...' : 'Load More' }}
      </button>
    </div>
  </div>
</template>

<script>
import FavoriteButton from './FavoriteButton.vue'

export default {
  name: 'FavoritesPage',
  components: {
    FavoriteButton
  },
  
  data() {
    return {
      favorites: [],
      loading: false,
      loadingMore: false,
      searchQuery: '',
      sortBy: 'updated_at',
      sortOrder: 'desc',
      page: 1,
      hasMore: true
    }
  },
  
  watch: {
    searchQuery() {
      this.debouncedSearch()
    },
    sortBy() {
      this.resetAndLoad()
    }
  },
  
  async mounted() {
    await this.loadFavorites()
  },
  
  methods: {
    async loadFavorites(append = false) {
      try {
        if (!append) {
          this.loading = true
          this.page = 1
        } else {
          this.loadingMore = true
        }
        
        const params = {
          page: this.page,
          limit: 20,
          sort_by: this.sortBy,
          sort_order: this.sortOrder
        }
        
        if (this.searchQuery) {
          params.search = this.searchQuery
        }
        
        const response = await this.$api.get('/favorites/', { params })
        
        if (append) {
          this.favorites.push(...response.data)
        } else {
          this.favorites = response.data
        }
        
        this.hasMore = response.data.length === 20
        
      } catch (error) {
        this.$toast.error('Failed to load favorites')
      } finally {
        this.loading = false
        this.loadingMore = false
      }
    },
    
    async loadMore() {
      this.page++
      await this.loadFavorites(true)
    },
    
    async resetAndLoad() {
      this.page = 1
      this.hasMore = true
      await this.loadFavorites()
    },
    
    debouncedSearch: debounce(function() {
      this.resetAndLoad()
    }, 500),
    
    async exportFavorites() {
      try {
        const response = await this.$api.get('/favorites/export?format=json')
        const blob = new Blob([JSON.stringify(response.data.content, null, 2)], {
          type: 'application/json'
        })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = response.data.filename
        a.click()
        URL.revokeObjectURL(url)
      } catch (error) {
        this.$toast.error('Failed to export favorites')
      }
    },
    
    onFavoriteChanged(event) {
      if (!event.isFavorite) {
        // Remove from list if unfavorited
        this.favorites = this.favorites.filter(f => f.manga_id !== event.mangaId)
      }
    },
    
    truncateDescription(description) {
      if (!description) return ''
      return description.length > 150 ? description.substring(0, 150) + '...' : description
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString()
    }
  }
}

// Utility function
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}
</script>
```

## 🔧 API Integration

### API Service Setup

```javascript
// api/favorites.js
export const favoritesApi = {
  getFavorites(params = {}) {
    return api.get('/favorites/', { params })
  },
  
  addToFavorites(mangaId) {
    return api.post(`/favorites/${mangaId}`)
  },
  
  removeFromFavorites(mangaId) {
    return api.delete(`/favorites/${mangaId}`)
  },
  
  getFavoriteStatus(mangaId) {
    return api.get(`/favorites/${mangaId}/status`)
  },
  
  getFavoritesCount() {
    return api.get('/favorites/count')
  },
  
  bulkUpdateFavorites(mangaIds, isFavorite) {
    return api.patch('/favorites/bulk', {
      manga_ids: mangaIds,
      is_favorite: isFavorite
    })
  },
  
  exportFavorites(format = 'json') {
    return api.get('/favorites/export', {
      params: { format }
    })
  }
}

// api/providers.js
export const providersApi = {
  getProviders() {
    return api.get('/providers/')
  },
  
  getProviderStatuses() {
    return api.get('/providers/status')
  },
  
  testProvider(providerId) {
    return api.post(`/providers/${providerId}/test`)
  },
  
  getProviderStatistics() {
    return api.get('/providers/statistics')
  },
  
  updateCheckInterval(interval) {
    return api.patch('/providers/check-interval', { interval })
  }
}
```

This integration guide provides a solid foundation for implementing the new features in the Vue.js frontend while maintaining a good user experience and following modern frontend practices.
