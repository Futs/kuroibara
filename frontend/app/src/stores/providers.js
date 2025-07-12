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
  }),

  getters: {
    getProviders: (state) => state.providers,
    getSelectedProvider: (state) => state.selectedProvider,
    getProviderManga: (state) => state.providerManga,
    getSelectedManga: (state) => state.selectedManga,
    getPagination: (state) => state.pagination,
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
        this.error = error.response?.data?.detail || "Failed to fetch providers";
        console.error("Error fetching providers:", error);
      } finally {
        this.loading = false;
      }
    },

    async selectProvider(providerId) {
      this.selectedProvider = this.providers.find(p => p.id === providerId);
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

    async fetchProviderManga(providerId, page = 1) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(`/v1/providers/${providerId}/manga`, {
          params: {
            page,
            limit: this.pagination.limit,
          },
        });

        if (page === 1) {
          this.providerManga = response.data.manga;
        } else {
          this.providerManga.push(...response.data.manga);
        }

        this.pagination = {
          page: response.data.pagination.page,
          limit: response.data.pagination.limit,
          total: response.data.pagination.total,
          hasMore: response.data.pagination.has_more,
        };
      } catch (error) {
        this.error = error.response?.data?.detail || "Failed to fetch provider manga";
        console.error("Error fetching provider manga:", error);
      } finally {
        this.loading = false;
      }
    },

    async fetchProviderMangaDetails(providerId, mangaId) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(`/v1/providers/${providerId}/manga/${mangaId}`);
        this.selectedManga = response.data;
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.detail || "Failed to fetch manga details";
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

      await this.fetchProviderManga(this.selectedProvider.id, this.pagination.page + 1);
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
    },

    clearSelectedManga() {
      this.selectedManga = null;
    },

    clearError() {
      this.error = null;
    },
  },
});
