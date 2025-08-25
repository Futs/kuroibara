/**
 * Enhanced Search Service
 * 
 * Integrates with the new tiered indexing system providing:
 * - MangaUpdates (primary tier)
 * - MadaraDex (secondary tier) 
 * - MangaDex (tertiary tier)
 * 
 * Features:
 * - Rich metadata from multiple sources
 * - Source attribution and confidence scoring
 * - NSFW content detection
 * - Intelligent fallback between indexers
 */

import api from './api.js';

class EnhancedSearchService {
  constructor() {
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Enhanced search using tiered indexing system
   * @param {Object} params - Search parameters
   * @param {string} params.query - Search query
   * @param {number} params.page - Page number (default: 1)
   * @param {number} params.limit - Results per page (default: 20)
   * @returns {Promise<Object>} Search results with metadata
   */
  async search({ query, page = 1, limit = 20 }) {
    if (!query || query.trim().length === 0) {
      return {
        results: [],
        total: 0,
        page,
        limit,
        has_next: false,
        sources: [],
        performance: {}
      };
    }

    // Check cache first
    const cacheKey = `search:${query}:${page}:${limit}`;
    const cached = this.getFromCache(cacheKey);
    if (cached) {
      return {
        ...cached,
        cached: true
      };
    }

    try {
      const startTime = performance.now();

      console.log('Enhanced search: calling /v1/search/enhanced with params:', { query, page, limit });

      const response = await api.post('/v1/search/enhanced', null, {
        params: { query, page, limit }
      });

      console.log('Enhanced search: received response:', response.data);

      const endTime = performance.now();
      const responseTime = Math.round(endTime - startTime);

      const searchResults = {
        results: response.data.results || [],
        total: response.data.total || 0,
        page: response.data.page || page,
        limit: response.data.limit || limit,
        has_next: response.data.has_next || false,
        sources: this.extractSources(response.data.results || []),
        performance: {
          response_time_ms: responseTime,
          cached: false
        }
      };

      // Cache the results
      this.setCache(cacheKey, searchResults);

      return searchResults;

    } catch (error) {
      console.error('Enhanced search failed:', error);
      console.error('Error details:', error.response?.data || error.message);
      console.error('Error status:', error.response?.status);

      // Fallback to legacy search if enhanced search fails
      console.log('Falling back to legacy search...');
      try {
        const fallbackResults = await this.fallbackSearch({ query, page, limit });
        console.log('Fallback search successful:', fallbackResults);
        return fallbackResults;
      } catch (fallbackError) {
        console.error('Fallback search also failed:', fallbackError);
        throw new Error(`Search failed: ${error.message}`);
      }
    }
  }

  /**
   * Fallback to legacy search system
   * @param {Object} params - Search parameters
   * @returns {Promise<Object>} Legacy search results
   */
  async fallbackSearch({ query, page = 1, limit = 20 }) {
    const response = await api.post('/v1/search', {
      query,
      page,
      limit,
      provider: null
    });

    return {
      results: response.data.results || [],
      total: response.data.total || 0,
      page: response.data.page || page,
      limit: response.data.limit || limit,
      has_next: response.data.has_next || false,
      sources: this.extractSources(response.data.results || []),
      performance: {
        response_time_ms: null,
        cached: false,
        fallback: true
      }
    };
  }

  /**
   * Get system health status
   * @returns {Promise<Object>} Health status
   */
  async getSystemHealth() {
    try {
      const response = await api.get('/v1/health/');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      return {
        status: 'unhealthy',
        message: 'Health check failed'
      };
    }
  }

  /**
   * Get indexer health status
   * @returns {Promise<Object>} Indexer health status
   */
  async getIndexerHealth() {
    try {
      const response = await api.get('/v1/search/indexers/health');
      return response.data;
    } catch (error) {
      console.error('Indexer health check failed:', error);
      return {
        status: 'unhealthy',
        indexers: {},
        message: 'Indexer health check failed'
      };
    }
  }

  /**
   * Extract unique sources from search results
   * @param {Array} results - Search results
   * @returns {Array} Array of source information
   */
  extractSources(results) {
    const sourceMap = new Map();
    
    results.forEach(result => {
      if (result.provider && !sourceMap.has(result.provider)) {
        sourceMap.set(result.provider, {
          name: result.provider,
          tier: this.getSourceTier(result.provider),
          count: 1,
          confidence_range: {
            min: result.confidence_score || 0,
            max: result.confidence_score || 0
          }
        });
      } else if (result.provider && sourceMap.has(result.provider)) {
        const source = sourceMap.get(result.provider);
        source.count++;
        if (result.confidence_score) {
          source.confidence_range.min = Math.min(source.confidence_range.min, result.confidence_score);
          source.confidence_range.max = Math.max(source.confidence_range.max, result.confidence_score);
        }
      }
    });

    return Array.from(sourceMap.values()).sort((a, b) => {
      const tierOrder = { 'primary': 1, 'secondary': 2, 'tertiary': 3, 'unknown': 4 };
      return tierOrder[a.tier] - tierOrder[b.tier];
    });
  }

  /**
   * Get source tier classification
   * @param {string} provider - Provider name
   * @returns {string} Tier classification
   */
  getSourceTier(provider) {
    const tierMap = {
      'mangaupdates': 'primary',
      'madaradex': 'secondary', 
      'mangadex': 'tertiary'
    };
    return tierMap[provider.toLowerCase()] || 'unknown';
  }

  /**
   * Get from cache
   * @param {string} key - Cache key
   * @returns {Object|null} Cached data or null
   */
  getFromCache(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    if (cached) {
      this.cache.delete(key);
    }
    return null;
  }

  /**
   * Set cache
   * @param {string} key - Cache key
   * @param {Object} data - Data to cache
   */
  setCache(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });

    // Clean up old cache entries (simple LRU)
    if (this.cache.size > 100) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
  }

  /**
   * Clear cache
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * Format confidence score for display
   * @param {number} score - Confidence score (0-1)
   * @returns {string} Formatted confidence
   */
  formatConfidence(score) {
    if (!score) return 'Unknown';
    const percentage = Math.round(score * 100);
    if (percentage >= 90) return 'Excellent';
    if (percentage >= 80) return 'Very Good';
    if (percentage >= 70) return 'Good';
    if (percentage >= 60) return 'Fair';
    return 'Low';
  }

  /**
   * Get confidence color class
   * @param {number} score - Confidence score (0-1)
   * @returns {string} CSS color class
   */
  getConfidenceColor(score) {
    if (!score) return 'text-gray-500';
    const percentage = Math.round(score * 100);
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 80) return 'text-green-500';
    if (percentage >= 70) return 'text-yellow-500';
    if (percentage >= 60) return 'text-orange-500';
    return 'text-red-500';
  }
}

// Export singleton instance
export default new EnhancedSearchService();
