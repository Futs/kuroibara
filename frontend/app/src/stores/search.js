import { defineStore } from "pinia";
import enhancedSearchService from "../services/enhancedSearchService.js";

export const useSearchStore = defineStore("search", {
  state: () => ({
    results: [],
    loading: false,
    error: null,
    query: "",
    provider: "all",
    filters: {
      status: null,
      genre: null,
      nsfw: null, // New NSFW filter
    },
    pagination: {
      page: 1,
      limit: 20,
      total: 0,
      has_next: false,
    },
    // Enhanced search features
    sources: [],
    performance: {},
    indexerHealth: null,
    useEnhancedSearch: true,
  }),

  getters: {
    getResults: (state) => state.results,
    getQuery: (state) => state.query,
    getProvider: (state) => state.provider,
    getFilters: (state) => state.filters,
    getPagination: (state) => state.pagination,
    getSources: (state) => state.sources,
    getPerformance: (state) => state.performance,
    getIndexerHealth: (state) => state.indexerHealth,
    isEnhancedSearchEnabled: (state) => state.useEnhancedSearch,

    // Enhanced getters
    getResultsBySource: (state) => {
      const grouped = {};
      state.results.forEach(result => {
        const source = result.provider || 'unknown';
        if (!grouped[source]) {
          grouped[source] = [];
        }
        grouped[source].push(result);
      });
      return grouped;
    },

    getHighConfidenceResults: (state) => {
      return state.results.filter(result =>
        result.confidence_score && result.confidence_score >= 0.8
      );
    },

    getNsfwResults: (state) => {
      return state.results.filter(result => result.is_nsfw);
    },

    getSafeResults: (state) => {
      return state.results.filter(result => !result.is_nsfw);
    },
  },

  actions: {
    async search() {
      if (!this.query || this.query.trim().length === 0) {
        this.clearResults();
        return;
      }

      this.loading = true;
      this.error = null;

      try {
        const { page, limit } = this.pagination;

        let searchResults;

        if (this.useEnhancedSearch) {
          // Use enhanced search with tiered indexing
          searchResults = await enhancedSearchService.search({
            query: this.query.trim(),
            page,
            limit
          });
        } else {
          // Fallback to legacy search
          searchResults = await enhancedSearchService.fallbackSearch({
            query: this.query.trim(),
            page,
            limit
          });
        }

        // Update state with results
        this.results = this.applyFilters(searchResults.results);
        this.pagination.total = searchResults.total;
        this.pagination.page = searchResults.page;
        this.pagination.has_next = searchResults.has_next;
        this.sources = searchResults.sources || [];
        this.performance = searchResults.performance || {};

      } catch (error) {
        this.error = error.message;
        console.error("Search error:", error);

        // Try fallback if enhanced search failed
        if (this.useEnhancedSearch) {
          console.log("Attempting fallback search...");
          try {
            const fallbackResults = await enhancedSearchService.fallbackSearch({
              query: this.query.trim(),
              page: this.pagination.page,
              limit: this.pagination.limit
            });

            this.results = this.applyFilters(fallbackResults.results);
            this.pagination.total = fallbackResults.total;
            this.pagination.page = fallbackResults.page;
            this.pagination.has_next = fallbackResults.has_next;
            this.sources = fallbackResults.sources || [];
            this.performance = { ...fallbackResults.performance, fallback: true };
            this.error = null; // Clear error since fallback worked

          } catch (fallbackError) {
            console.error("Fallback search also failed:", fallbackError);
            this.error = `Search failed: ${fallbackError.message}`;
          }
        }
      } finally {
        this.loading = false;
      }
    },

    /**
     * Apply filters to search results
     * @param {Array} results - Raw search results
     * @returns {Array} Filtered results
     */
    applyFilters(results) {
      if (!results) return [];

      let filtered = [...results];

      // Apply NSFW filter
      if (this.filters.nsfw === false) {
        filtered = filtered.filter(result => !result.is_nsfw);
      } else if (this.filters.nsfw === true) {
        filtered = filtered.filter(result => result.is_nsfw);
      }

      // Apply status filter
      if (this.filters.status) {
        filtered = filtered.filter(result =>
          result.status && result.status.toLowerCase() === this.filters.status.toLowerCase()
        );
      }

      // Apply genre filter
      if (this.filters.genre) {
        filtered = filtered.filter(result =>
          result.genres && result.genres.some(genre =>
            genre.toLowerCase().includes(this.filters.genre.toLowerCase())
          )
        );
      }

      return filtered;
    },

    /**
     * Clear search results and reset state
     */
    clearResults() {
      this.results = [];
      this.pagination.total = 0;
      this.pagination.page = 1;
      this.pagination.has_next = false;
      this.sources = [];
      this.performance = {};
      this.error = null;
    },

    /**
     * Set search query and trigger search
     * @param {string} query - Search query
     */
    async setQuery(query) {
      this.query = query;
      this.pagination.page = 1; // Reset to first page
      await this.search();
    },

    /**
     * Set page and trigger search
     * @param {number} page - Page number
     */
    async setPage(page) {
      this.pagination.page = page;
      await this.search();
    },

    /**
     * Toggle enhanced search mode
     * @param {boolean} enabled - Whether to use enhanced search
     */
    setEnhancedSearch(enabled) {
      this.useEnhancedSearch = enabled;
      enhancedSearchService.clearCache(); // Clear cache when switching modes
    },

    /**
     * Update filters and trigger search
     * @param {Object} filters - Filter object
     */
    async updateFilters(filters) {
      this.filters = { ...this.filters, ...filters };
      this.pagination.page = 1; // Reset to first page when filters change
      await this.search();
    },

    /**
     * Get indexer health status
     */
    async checkIndexerHealth() {
      try {
        this.indexerHealth = await enhancedSearchService.getIndexerHealth();
      } catch (error) {
        console.error("Failed to check indexer health:", error);
        this.indexerHealth = {
          status: 'unhealthy',
          message: 'Health check failed'
        };
      }
    },

    setQuery(query) {
      this.query = query;
      this.pagination.page = 1; // Reset to first page when query changes
    },

    setProvider(provider) {
      this.provider = provider;
      this.pagination.page = 1; // Reset to first page when provider changes
    },

    setFilters(filters) {
      this.filters = { ...this.filters, ...filters };
      this.pagination.page = 1; // Reset to first page when filters change
    },

    setPage(page) {
      this.pagination.page = page;
      this.search();
    },

    resetSearch() {
      this.results = [];
      this.query = "";
      this.provider = "all";
      this.filters = {
        status: null,
        genre: null,
      };
      this.pagination = {
        page: 1,
        limit: 20,
        total: 0,
      };
    },
  },
});
