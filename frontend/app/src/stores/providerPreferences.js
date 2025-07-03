import { defineStore } from 'pinia';
import axios from 'axios';

export const useProviderPreferencesStore = defineStore('providerPreferences', {
  state: () => ({
    providers: [],
    loading: false,
    error: null,
    lastFetched: null,
  }),

  getters: {
    getProviders: (state) => state.providers,
    getFavoriteProviders: (state) => 
      state.providers
        .filter(p => p.is_favorite)
        .sort((a, b) => (a.priority_order || 999) - (b.priority_order || 999)),
    getRegularProviders: (state) => 
      state.providers
        .filter(p => !p.is_favorite)
        .sort((a, b) => a.name.localeCompare(b.name)),
    getProviderById: (state) => (id) => 
      state.providers.find(p => p.id === id),
    isProviderFavorite: (state) => (id) => {
      const provider = state.providers.find(p => p.id === id);
      return provider ? provider.is_favorite : false;
    },
    getProviderStatus: (state) => (id) => {
      const provider = state.providers.find(p => p.id === id);
      return provider ? provider.status : 'unknown';
    },
    isLoading: (state) => state.loading,
    getError: (state) => state.error,
  },

  actions: {
    async fetchProviderPreferences(force = false) {
      // Don't fetch if we have recent data and not forcing
      if (!force && this.lastFetched && Date.now() - this.lastFetched < 5 * 60 * 1000) {
        return;
      }

      this.loading = true;
      this.error = null;

      try {
        const response = await axios.get('/v1/users/me/provider-preferences');
        this.providers = response.data.providers;
        this.lastFetched = Date.now();
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch provider preferences';
        console.error('Error fetching provider preferences:', error);
      } finally {
        this.loading = false;
      }
    },

    async updateProviderPreference(providerId, updates) {
      try {
        await axios.put(`/v1/users/me/provider-preferences/${providerId}`, updates);
        
        // Update local state
        const provider = this.providers.find(p => p.id === providerId);
        if (provider) {
          Object.assign(provider, updates);
        }
        
        return true;
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to update provider preference';
        console.error('Error updating provider preference:', error);
        return false;
      }
    },

    async bulkUpdateProviderPreferences(preferences) {
      try {
        await axios.post('/v1/users/me/provider-preferences/bulk', {
          preferences
        });
        
        // Update local state
        preferences.forEach(pref => {
          const provider = this.providers.find(p => p.id === pref.provider_id);
          if (provider) {
            provider.is_favorite = pref.is_favorite;
            provider.priority_order = pref.priority_order;
            provider.user_enabled = pref.is_enabled;
          }
        });
        
        return true;
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to bulk update provider preferences';
        console.error('Error bulk updating provider preferences:', error);
        return false;
      }
    },

    async toggleProviderFavorite(providerId) {
      const provider = this.providers.find(p => p.id === providerId);
      if (!provider) return false;

      const newFavoriteState = !provider.is_favorite;
      let priorityOrder = provider.priority_order;

      if (newFavoriteState) {
        // Set priority order for new favorite
        const maxPriority = Math.max(
          ...this.providers
            .filter(p => p.is_favorite && p.id !== providerId)
            .map(p => p.priority_order || 0),
          0
        );
        priorityOrder = maxPriority + 1;
      } else {
        // Remove priority order when unfavoriting
        priorityOrder = null;
      }

      return await this.updateProviderPreference(providerId, {
        is_favorite: newFavoriteState,
        priority_order: priorityOrder,
      });
    },

    async toggleProviderEnabled(providerId) {
      const provider = this.providers.find(p => p.id === providerId);
      if (!provider) return false;

      return await this.updateProviderPreference(providerId, {
        is_enabled: !provider.user_enabled,
      });
    },

    clearError() {
      this.error = null;
    },

    // Helper method to get provider display info for search interface
    getProviderDisplayInfo(providerId) {
      const provider = this.getProviderById(providerId);
      if (!provider) {
        return {
          name: providerId,
          isFavorite: false,
          status: 'unknown',
          isEnabled: true,
        };
      }

      return {
        name: provider.name,
        isFavorite: provider.is_favorite,
        status: provider.status,
        isEnabled: provider.user_enabled,
        priorityOrder: provider.priority_order,
        responseTime: provider.response_time,
        uptimePercentage: provider.uptime_percentage,
      };
    },
  },
});
