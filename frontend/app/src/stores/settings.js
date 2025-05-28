import { defineStore } from 'pinia';
import axios from 'axios';

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    theme: localStorage.getItem('theme') || 'light', // light, dark, system
    nsfwBlur: localStorage.getItem('nsfwBlur') === 'true',
    downloadQuality: localStorage.getItem('downloadQuality') || 'high', // low, medium, high
    downloadPath: localStorage.getItem('downloadPath') || 'default',
    loading: false,
    error: null,
  }),

  getters: {
    getTheme: (state) => state.theme,
    getNsfwBlur: (state) => state.nsfwBlur,
    getDownloadQuality: (state) => state.downloadQuality,
    getDownloadPath: (state) => state.downloadPath,
  },

  actions: {
    async fetchUserSettings() {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.get('/v1/users/settings');

        // Update local settings from server
        const { theme, nsfw_blur, download_quality, download_path } = response.data;

        this.theme = theme || this.theme;
        this.nsfwBlur = nsfw_blur !== undefined ? nsfw_blur : this.nsfwBlur;
        this.downloadQuality = download_quality || this.downloadQuality;
        this.downloadPath = download_path || this.downloadPath;

        // Save to localStorage
        this.saveToLocalStorage();
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch settings';
        console.error('Settings fetch error:', error);
      } finally {
        this.loading = false;
      }
    },

    async updateUserSettings() {
      this.loading = true;
      this.error = null;

      try {
        await axios.put('/v1/users/settings', {
          theme: this.theme,
          nsfw_blur: this.nsfwBlur,
          download_quality: this.downloadQuality,
          download_path: this.downloadPath,
        });

        // Save to localStorage
        this.saveToLocalStorage();
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to update settings';
        console.error('Settings update error:', error);
      } finally {
        this.loading = false;
      }
    },

    setTheme(theme) {
      this.theme = theme;
      this.saveToLocalStorage();
      this.applyTheme();
    },

    setNsfwBlur(blur) {
      this.nsfwBlur = blur;
      this.saveToLocalStorage();
    },

    setDownloadQuality(quality) {
      this.downloadQuality = quality;
      this.saveToLocalStorage();
    },

    setDownloadPath(path) {
      this.downloadPath = path;
      this.saveToLocalStorage();
    },

    saveToLocalStorage() {
      localStorage.setItem('theme', this.theme);
      localStorage.setItem('nsfwBlur', this.nsfwBlur.toString());
      localStorage.setItem('downloadQuality', this.downloadQuality);
      localStorage.setItem('downloadPath', this.downloadPath);
    },

    applyTheme() {
      const isDark =
        this.theme === 'dark' ||
        (this.theme === 'system' &&
         window.matchMedia('(prefers-color-scheme: dark)').matches);

      if (isDark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    },

    initSettings() {
      this.applyTheme();

      // Listen for system theme changes if using system theme
      if (this.theme === 'system') {
        window.matchMedia('(prefers-color-scheme: dark)')
          .addEventListener('change', () => this.applyTheme());
      }
    },
  },
});
