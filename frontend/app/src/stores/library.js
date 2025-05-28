import { defineStore } from 'pinia';
import api from '../services/api';

export const useLibraryStore = defineStore('library', {
  state: () => ({
    manga: [],
    currentManga: null,
    loading: false,
    error: null,
    filters: {
      category: null,
      status: null,
      sort: 'title',
      order: 'asc',
    },
    pagination: {
      page: 1,
      limit: 20,
      total: 0,
    },
  }),

  getters: {
    getManga: (state) => state.manga,
    getCurrentManga: (state) => state.currentManga,
    getFilters: (state) => state.filters,
    getPagination: (state) => state.pagination,
  },

  actions: {
    async fetchLibrary() {
      this.loading = true;
      this.error = null;

      try {
        const { page, limit } = this.pagination;
        const { category, status, sort, order } = this.filters;

        const response = await api.get('/v1/library', {
          params: {
            page,
            limit,
            category,
            status,
            sort,
            order,
          },
        });

        this.manga = response.data.items || response.data;
        this.pagination.total = response.data.total || response.data.length;
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch library';
        console.error('Library fetch error:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchMangaDetails(id) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(`/v1/manga/${id}`);
        this.currentManga = response.data;
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch manga details';
        console.error('Manga details fetch error:', error);
      } finally {
        this.loading = false;
      }
    },

    async addToLibrary(mangaId) {
      this.loading = true;
      this.error = null;

      try {
        await api.post('/v1/library', { manga_id: mangaId });
        await this.fetchLibrary();
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to add manga to library';
        console.error('Add to library error:', error);
        throw error; // Re-throw so calling code can handle it
      } finally {
        this.loading = false;
      }
    },

    async removeFromLibrary(mangaId) {
      this.loading = true;
      this.error = null;

      try {
        await api.delete(`/v1/library/${mangaId}`);
        await this.fetchLibrary();
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to remove manga from library';
        console.error('Remove from library error:', error);
        throw error; // Re-throw so calling code can handle it
      } finally {
        this.loading = false;
      }
    },

    setFilters(filters) {
      this.filters = { ...this.filters, ...filters };
      this.pagination.page = 1; // Reset to first page when filters change
      this.fetchLibrary();
    },

    setPage(page) {
      this.pagination.page = page;
      this.fetchLibrary();
    },
  },
});
