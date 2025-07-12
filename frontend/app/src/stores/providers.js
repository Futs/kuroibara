import { defineStore } from "pinia";
import api from "../services/api";

export const useProvidersStore = defineStore("providers", {
  state: () => ({
    providers: [],
    selectedProvider: null,
    providerManga: [],
    selectedManga: null,
    loading: false,
    error: null,
    pagination: {
      page: 1,
      limit: 20,
      total: 0,
      hasMore: false,
    },
    filters: {
      search: "",
      genres: [],
      status: "",
      type: "",
      year: "",
      content: "",
      language: "",
    },
  }),

  getters: {
    getProviders: (state) => state.providers,
    getSelectedProvider: (state) => state.selectedProvider,
    getProviderManga: (state) => state.providerManga,
    getSelectedManga: (state) => state.selectedManga,
    getPagination: (state) => state.pagination,
    getFilters: (state) => state.filters,
    isLoading: (state) => state.loading,
    getError: (state) => state.error,
  },

  actions: {
    async fetchProviders() {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get("/v1/providers/");
        this.providers = response.data;
      } catch (error) {
        // Don't set error state for 401 errors as they will be handled by the API interceptor
        if (error.response?.status !== 401) {
          this.error =
            error.response?.data?.detail || "Failed to fetch providers";
        }
        console.error("Error fetching providers:", error);
        throw error; // Re-throw to allow component to handle it
      } finally {
        this.loading = false;
      }
    },

    async selectProvider(providerId) {
      this.selectedProvider = this.providers.find((p) => p.id === providerId);
      this.providerManga = [];
      this.pagination = {
        page: 1,
        limit: 20,
        total: 0,
        hasMore: false,
      };

      if (this.selectedProvider) {
        await this.fetchProviderManga(providerId);
      }
    },

    async fetchProviderManga(providerId, page = 1, filters = null) {
      this.loading = true;
      this.error = null;

      try {
        const params = {
          page,
          limit: this.pagination.limit,
        };

        // Add filter parameters if provided (only backend-supported filters)
        const activeFilters = filters || this.filters;
        if (activeFilters.search) {
          params.search = activeFilters.search;
        }
        // For now, use the first genre for backend filtering (backend only supports single genre)
        if (activeFilters.genres && activeFilters.genres.length > 0) {
          params.genre = activeFilters.genres[0];
        }

        const response = await api.get(`/v1/providers/${providerId}/manga`, {
          params,
        });

        let manga = response.data.manga;

        // Apply client-side filters for unsupported backend filters
        manga = this.applyClientSideFilters(manga, activeFilters);

        if (page === 1) {
          this.providerManga = manga;
        } else {
          this.providerManga.push(...manga);
        }

        this.pagination = {
          page: response.data.pagination.page,
          limit: response.data.pagination.limit,
          total: page === 1 ? manga.length : this.pagination.total, // Update total for filtered results on first page
          hasMore: response.data.pagination.has_more,
        };
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to fetch provider manga";
        console.error("Error fetching provider manga:", error);
      } finally {
        this.loading = false;
      }
    },

    async fetchProviderMangaDetails(providerId, mangaId) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(
          `/v1/providers/${providerId}/manga/${mangaId}`,
        );
        this.selectedManga = response.data;
        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to fetch manga details";
        console.error("Error fetching manga details:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async loadMoreManga() {
      if (!this.selectedProvider || !this.pagination.hasMore || this.loading) {
        return;
      }

      await this.fetchProviderManga(
        this.selectedProvider.id,
        this.pagination.page + 1,
      );
    },

    clearSelectedProvider() {
      this.selectedProvider = null;
      this.providerManga = [];
      this.selectedManga = null;
      this.pagination = {
        page: 1,
        limit: 20,
        total: 0,
        hasMore: false,
      };
      this.filters = {
        search: "",
        genres: [],
        status: "",
        type: "",
        year: "",
        content: "",
        language: "",
      };
    },

    clearSelectedManga() {
      this.selectedManga = null;
    },

    clearError() {
      this.error = null;
    },

    updateFilters(newFilters) {
      this.filters = { ...this.filters, ...newFilters };
    },

    clearFilters() {
      this.filters = {
        search: "",
        genres: [],
        status: "",
        type: "",
        year: "",
        content: "",
        language: "",
      };
    },

    async applyFilters() {
      if (!this.selectedProvider) return;

      // Reset pagination when applying filters
      this.pagination.page = 1;
      await this.fetchProviderManga(this.selectedProvider.id, 1);
    },

    applyClientSideFilters(manga, filters) {
      if (!manga || !Array.isArray(manga)) return manga;

      return manga.filter((item) => {
        // Multiple genres filter (client-side filtering for additional genres beyond the first one)
        if (filters.genres && filters.genres.length > 1) {
          // Check if the manga has all selected genres
          const hasAllGenres = filters.genres.every(
            (selectedGenre) =>
              item.genres &&
              item.genres.some(
                (mangaGenre) =>
                  mangaGenre.toLowerCase() === selectedGenre.toLowerCase(),
              ),
          );
          if (!hasAllGenres) {
            return false;
          }
        }

        // Status filter
        if (filters.status && item.status !== filters.status) {
          return false;
        }

        // Type filter
        if (filters.type && item.type !== filters.type) {
          return false;
        }

        // Year filter
        if (filters.year && item.year !== parseInt(filters.year)) {
          return false;
        }

        // Content filter
        if (filters.content) {
          if (
            filters.content === "safe" &&
            (item.is_nsfw || item.is_explicit)
          ) {
            return false;
          }
          if (
            filters.content === "nsfw" &&
            !item.is_nsfw &&
            !item.is_explicit
          ) {
            return false;
          }
        }

        // Language filter (this would need to be implemented based on available language data)
        // For now, we'll skip language filtering as it's not clear how language data is structured

        return true;
      });
    },
  },
});
