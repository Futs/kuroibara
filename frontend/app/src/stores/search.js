import { defineStore } from 'pinia';
import axios from 'axios';

export const useSearchStore = defineStore('search', {
  state: () => ({
    results: [],
    loading: false,
    error: null,
    query: '',
    provider: 'all',
    filters: {
      status: null,
      genre: null,
    },
    pagination: {
      page: 1,
      limit: 20,
      total: 0,
    },
  }),

  getters: {
    getResults: (state) => state.results,
    getQuery: (state) => state.query,
    getProvider: (state) => state.provider,
    getFilters: (state) => state.filters,
    getPagination: (state) => state.pagination,
  },

  actions: {
    async search() {
      if (!this.query) return;

      this.loading = true;
      this.error = null;

      try {
        const { page, limit } = this.pagination;
        const { status, genre } = this.filters;

        const response = await axios.post('/v1/search', {
          query: this.query,
          provider: this.provider === 'all' ? null : this.provider,
          page,
          limit,
          status,
          genre,
        });

        this.results = response.data.results;
        this.pagination.total = response.data.total;
      } catch (error) {
        this.error = error.response?.data?.detail || 'Search failed';
        console.error('Search error:', error);
      } finally {
        this.loading = false;
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
      this.query = '';
      this.provider = 'all';
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
