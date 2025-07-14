import { defineStore } from "pinia";
import api from "../services/api";

export const useLibraryStore = defineStore("library", {
  state: () => ({
    manga: [],
    currentManga: null,
    loading: false,
    error: null,

    // Enhanced filtering system
    filters: {
      // Basic filters
      category: null,
      status: null,
      sort: "title",
      order: "asc",

      // Advanced filters
      readStatus: [], // 'unread', 'reading', 'completed', 'on-hold', 'dropped'
      rating: { min: 0, max: 10 },
      dateAdded: { start: null, end: null },
      lastRead: { start: null, end: null },
      genres: [],
      authors: [],
      languages: [],
      tags: [],
      customTags: [],

      // Search and text filters
      search: "",
      title: "",
      author: "",
      description: "",

      // Content filters
      hasUnreadChapters: null,
      isDownloaded: null,
      isFavorite: null,
      hasBookmarks: null,

      // Advanced options
      duplicatesOnly: false,
      missingMetadata: false,
    },

    // Bulk operations
    selectedManga: new Set(),
    bulkOperationMode: false,

    // View options
    viewMode: localStorage.getItem("libraryViewMode") || "grid", // 'grid', 'list', 'compact', 'detailed'
    gridSize: localStorage.getItem("libraryGridSize") || "medium", // 'small', 'medium', 'large'

    // Statistics
    statistics: {
      total: 0,
      unread: 0,
      reading: 0,
      completed: 0,
      onHold: 0,
      dropped: 0,
      favorites: 0,
      downloaded: 0,
      totalSize: 0,
      genreDistribution: {},
      authorDistribution: {},
      languageDistribution: {},
      readingTimeStats: {},
    },

    // Collections and tags
    collections: [],
    customTags: JSON.parse(localStorage.getItem("customTags")) || [],

    pagination: {
      page: 1,
      limit: parseInt(localStorage.getItem("libraryPageSize")) || 20,
      total: 0,
    },
  }),

  getters: {
    getManga: (state) => state.manga,
    getCurrentManga: (state) => state.currentManga,
    getFilters: (state) => state.filters,
    getPagination: (state) => state.pagination,
    getStatistics: (state) => state.statistics,
    getSelectedManga: (state) => Array.from(state.selectedManga),
    getSelectedCount: (state) => state.selectedManga.size,
    getCustomTags: (state) => state.customTags,
    getCollections: (state) => state.collections,

    // Filtered manga based on current filters
    getFilteredManga: (state) => {
      let filtered = [...state.manga];

      // Apply search filter
      if (state.filters.search) {
        const searchTerm = state.filters.search.toLowerCase();
        filtered = filtered.filter(
          (item) =>
            item.manga.title.toLowerCase().includes(searchTerm) ||
            item.manga.description?.toLowerCase().includes(searchTerm) ||
            item.manga.authors?.some((author) =>
              author.name.toLowerCase().includes(searchTerm),
            ),
        );
      }

      // Apply read status filter
      if (state.filters.readStatus.length > 0) {
        filtered = filtered.filter((item) =>
          state.filters.readStatus.includes(item.read_status || "unread"),
        );
      }

      // Apply rating filter
      if (state.filters.rating.min > 0 || state.filters.rating.max < 10) {
        filtered = filtered.filter((item) => {
          const rating = item.rating || 0;
          return (
            rating >= state.filters.rating.min &&
            rating <= state.filters.rating.max
          );
        });
      }

      // Apply genre filter
      if (state.filters.genres.length > 0) {
        filtered = filtered.filter((item) =>
          item.manga.genres?.some((genre) =>
            state.filters.genres.includes(genre.name),
          ),
        );
      }

      // Apply custom tags filter
      if (state.filters.customTags.length > 0) {
        filtered = filtered.filter((item) =>
          item.custom_tags?.some((tag) =>
            state.filters.customTags.includes(tag),
          ),
        );
      }

      // Apply favorite filter
      if (state.filters.isFavorite !== null) {
        filtered = filtered.filter(
          (item) => Boolean(item.is_favorite) === state.filters.isFavorite,
        );
      }

      // Apply date filters
      if (state.filters.dateAdded.start || state.filters.dateAdded.end) {
        filtered = filtered.filter((item) => {
          const addedDate = new Date(item.created_at);
          const start = state.filters.dateAdded.start
            ? new Date(state.filters.dateAdded.start)
            : null;
          const end = state.filters.dateAdded.end
            ? new Date(state.filters.dateAdded.end)
            : null;

          if (start && addedDate < start) return false;
          if (end && addedDate > end) return false;
          return true;
        });
      }

      return filtered;
    },

    // Available filter options
    getAvailableGenres: (state) => {
      const genres = new Set();
      state.manga.forEach((item) => {
        item.manga.genres?.forEach((genre) => genres.add(genre.name));
      });
      return Array.from(genres).sort();
    },

    getAvailableAuthors: (state) => {
      const authors = new Set();
      state.manga.forEach((item) => {
        item.manga.authors?.forEach((author) => authors.add(author.name));
      });
      return Array.from(authors).sort();
    },

    getAvailableLanguages: (state) => {
      const languages = new Set();
      state.manga.forEach((item) => {
        item.manga.chapters?.forEach((chapter) => {
          if (chapter.language) languages.add(chapter.language);
        });
      });
      return Array.from(languages).sort();
    },

    getAvailableReadStatuses: () => [
      { value: "unread", label: "Unread", color: "gray" },
      { value: "reading", label: "Reading", color: "blue" },
      { value: "completed", label: "Completed", color: "green" },
      { value: "on-hold", label: "On Hold", color: "yellow" },
      { value: "dropped", label: "Dropped", color: "red" },
    ],
  },

  actions: {
    async fetchLibrary() {
      this.loading = true;
      this.error = null;

      try {
        const { page, limit } = this.pagination;
        const { category, status } = this.filters;

        // Calculate skip from page
        const skip = (page - 1) * limit;

        // Prepare params for backend API
        const params = {
          skip,
          limit,
        };

        // Add category filter if specified
        if (category) {
          params.category_id = category;
        }

        // Add favorite filter if status is 'favorite'
        if (status === "favorite") {
          params.is_favorite = true;
        } else if (status === "not_favorite") {
          params.is_favorite = false;
        }

        const response = await api.get("/v1/library", { params });

        this.manga = response.data || [];
        this.pagination.total = response.data.length || 0;
      } catch (error) {
        this.error = error.response?.data?.detail || "Failed to fetch library";
        console.error("Library fetch error:", error);
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
        this.error =
          error.response?.data?.detail || "Failed to fetch manga details";
        console.error("Manga details fetch error:", error);
      } finally {
        this.loading = false;
      }
    },

    async addToLibrary(mangaId) {
      this.loading = true;
      this.error = null;

      try {
        await api.post("/v1/library", { manga_id: mangaId });
        await this.fetchLibrary();
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to add manga to library";
        console.error("Add to library error:", error);
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
        this.error =
          error.response?.data?.detail || "Failed to remove manga from library";
        console.error("Remove from library error:", error);
        throw error; // Re-throw so calling code can handle it
      } finally {
        this.loading = false;
      }
    },

    // Enhanced filtering methods
    setFilters(filters) {
      this.filters = { ...this.filters, ...filters };
      this.pagination.page = 1; // Reset to first page when filters change
      this.fetchLibrary();
    },

    resetFilters() {
      this.filters = {
        category: null,
        status: null,
        sort: "title",
        order: "asc",
        readStatus: [],
        rating: { min: 0, max: 10 },
        dateAdded: { start: null, end: null },
        lastRead: { start: null, end: null },
        genres: [],
        authors: [],
        languages: [],
        tags: [],
        customTags: [],
        search: "",
        title: "",
        author: "",
        description: "",
        hasUnreadChapters: null,
        isDownloaded: null,
        isFavorite: null,
        hasBookmarks: null,
        duplicatesOnly: false,
        missingMetadata: false,
      };
      this.fetchLibrary();
    },

    setAdvancedFilter(filterType, value) {
      this.filters[filterType] = value;
      this.pagination.page = 1;
      this.fetchLibrary();
    },

    addToFilter(filterType, value) {
      if (!this.filters[filterType].includes(value)) {
        this.filters[filterType].push(value);
        this.pagination.page = 1;
        this.fetchLibrary();
      }
    },

    removeFromFilter(filterType, value) {
      const index = this.filters[filterType].indexOf(value);
      if (index > -1) {
        this.filters[filterType].splice(index, 1);
        this.pagination.page = 1;
        this.fetchLibrary();
      }
    },

    setPage(page) {
      this.pagination.page = page;
      this.fetchLibrary();
    },

    setPageSize(size) {
      this.pagination.limit = size;
      this.pagination.page = 1;
      localStorage.setItem("libraryPageSize", size.toString());
      this.fetchLibrary();
    },

    setViewMode(mode) {
      this.viewMode = mode;
      localStorage.setItem("libraryViewMode", mode);
    },

    setGridSize(size) {
      this.gridSize = size;
      localStorage.setItem("libraryGridSize", size);
    },

    async fetchLibraryItemDetailed(libraryItemId) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(`/v1/library/${libraryItemId}/detailed`);
        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail ||
          "Failed to fetch library item details";
        console.error("Error fetching library item details:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async downloadChapter(
      libraryItemId,
      chapterId,
      provider,
      externalMangaId,
      externalChapterId,
    ) {
      try {
        const response = await api.post(
          `/v1/library/${libraryItemId}/download-chapter`,
          {
            chapter_id: chapterId,
            provider,
            external_manga_id: externalMangaId,
            external_chapter_id: externalChapterId,
          },
        );
        return response.data;
      } catch (error) {
        console.error("Error downloading chapter:", error);
        throw error;
      }
    },

    async getFilteredChapters(libraryItemId, filters = {}) {
      try {
        const response = await api.get(
          `/v1/library/${libraryItemId}/chapters/filter`,
          {
            params: filters,
          },
        );
        return response.data;
      } catch (error) {
        console.error("Error fetching filtered chapters:", error);
        throw error;
      }
    },

    // Bulk operations
    toggleBulkMode() {
      this.bulkOperationMode = !this.bulkOperationMode;
      if (!this.bulkOperationMode) {
        this.selectedManga.clear();
      }
    },

    selectManga(mangaId) {
      this.selectedManga.add(mangaId);
    },

    deselectManga(mangaId) {
      this.selectedManga.delete(mangaId);
    },

    toggleMangaSelection(mangaId) {
      if (this.selectedManga.has(mangaId)) {
        this.selectedManga.delete(mangaId);
      } else {
        this.selectedManga.add(mangaId);
      }
    },

    selectAllManga() {
      this.manga.forEach((item) => this.selectedManga.add(item.id));
    },

    deselectAllManga() {
      this.selectedManga.clear();
    },

    async bulkMarkAsRead() {
      if (this.selectedManga.size === 0) return;

      try {
        const mangaIds = Array.from(this.selectedManga);
        await api.post("/v1/library/bulk/mark-read", { manga_ids: mangaIds });
        await this.fetchLibrary();
        this.selectedManga.clear();
      } catch (error) {
        console.error("Bulk mark as read error:", error);
        throw error;
      }
    },

    async bulkMarkAsUnread() {
      if (this.selectedManga.size === 0) return;

      try {
        const mangaIds = Array.from(this.selectedManga);
        await api.post("/v1/library/bulk/mark-unread", { manga_ids: mangaIds });
        await this.fetchLibrary();
        this.selectedManga.clear();
      } catch (error) {
        console.error("Bulk mark as unread error:", error);
        throw error;
      }
    },

    async bulkAddToFavorites() {
      if (this.selectedManga.size === 0) return;

      try {
        const mangaIds = Array.from(this.selectedManga);
        await api.post("/v1/library/bulk/add-favorites", {
          manga_ids: mangaIds,
        });
        await this.fetchLibrary();
        this.selectedManga.clear();
      } catch (error) {
        console.error("Bulk add to favorites error:", error);
        throw error;
      }
    },

    async bulkRemoveFromFavorites() {
      if (this.selectedManga.size === 0) return;

      try {
        const mangaIds = Array.from(this.selectedManga);
        await api.post("/v1/library/bulk/remove-favorites", {
          manga_ids: mangaIds,
        });
        await this.fetchLibrary();
        this.selectedManga.clear();
      } catch (error) {
        console.error("Bulk remove from favorites error:", error);
        throw error;
      }
    },

    async bulkDelete() {
      if (this.selectedManga.size === 0) return;

      try {
        const mangaIds = Array.from(this.selectedManga);
        await api.post("/v1/library/bulk/delete", { manga_ids: mangaIds });
        await this.fetchLibrary();
        this.selectedManga.clear();
      } catch (error) {
        console.error("Bulk delete error:", error);
        throw error;
      }
    },

    async bulkUpdateTags(tags) {
      if (this.selectedManga.size === 0) return;

      try {
        const mangaIds = Array.from(this.selectedManga);
        await api.post("/v1/library/bulk/update-tags", {
          manga_ids: mangaIds,
          tags,
        });
        await this.fetchLibrary();
        this.selectedManga.clear();
      } catch (error) {
        console.error("Bulk update tags error:", error);
        throw error;
      }
    },

    // Statistics and analytics
    async fetchStatistics() {
      try {
        const response = await api.get("/v1/library/statistics");
        this.statistics = response.data;
        return response.data;
      } catch (error) {
        console.error("Error fetching statistics:", error);
        throw error;
      }
    },

    calculateLocalStatistics() {
      const stats = {
        total: this.manga.length,
        unread: 0,
        reading: 0,
        completed: 0,
        onHold: 0,
        dropped: 0,
        favorites: 0,
        downloaded: 0,
        totalSize: 0,
        genreDistribution: {},
        authorDistribution: {},
        languageDistribution: {},
      };

      this.manga.forEach((item) => {
        // Count by read status
        const status = item.read_status || "unread";
        stats[status] = (stats[status] || 0) + 1;

        // Count favorites
        if (item.is_favorite) stats.favorites++;

        // Count downloaded
        if (item.is_downloaded) stats.downloaded++;

        // Genre distribution
        item.manga.genres?.forEach((genre) => {
          stats.genreDistribution[genre.name] =
            (stats.genreDistribution[genre.name] || 0) + 1;
        });

        // Author distribution
        item.manga.authors?.forEach((author) => {
          stats.authorDistribution[author.name] =
            (stats.authorDistribution[author.name] || 0) + 1;
        });

        // Language distribution
        item.manga.chapters?.forEach((chapter) => {
          if (chapter.language) {
            stats.languageDistribution[chapter.language] =
              (stats.languageDistribution[chapter.language] || 0) + 1;
          }
        });
      });

      this.statistics = stats;
      return stats;
    },

    // Custom tags management
    createCustomTag(tag) {
      if (!this.customTags.find((t) => t.name === tag.name)) {
        this.customTags.push({
          id: Date.now().toString(),
          name: tag.name,
          color: tag.color || "#3B82F6",
          description: tag.description || "",
          createdAt: new Date().toISOString(),
        });
        localStorage.setItem("customTags", JSON.stringify(this.customTags));
      }
    },

    updateCustomTag(tagId, updates) {
      const index = this.customTags.findIndex((t) => t.id === tagId);
      if (index !== -1) {
        this.customTags[index] = { ...this.customTags[index], ...updates };
        localStorage.setItem("customTags", JSON.stringify(this.customTags));
      }
    },

    deleteCustomTag(tagId) {
      this.customTags = this.customTags.filter((t) => t.id !== tagId);
      localStorage.setItem("customTags", JSON.stringify(this.customTags));
    },

    // Duplicate detection
    async findDuplicates() {
      try {
        const response = await api.get("/v1/library/duplicates");
        return response.data;
      } catch (error) {
        console.error("Error finding duplicates:", error);
        throw error;
      }
    },

    findLocalDuplicates() {
      const duplicates = [];
      const titleMap = new Map();

      this.manga.forEach((item) => {
        const normalizedTitle = item.manga.title
          .toLowerCase()
          .replace(/[^\w\s]/g, "")
          .replace(/\s+/g, " ")
          .trim();

        if (titleMap.has(normalizedTitle)) {
          const existing = titleMap.get(normalizedTitle);
          duplicates.push({
            title: normalizedTitle,
            items: [existing, item],
            similarity: this.calculateSimilarity(existing.manga, item.manga),
          });
        } else {
          titleMap.set(normalizedTitle, item);
        }
      });

      return duplicates;
    },

    calculateSimilarity(manga1, manga2) {
      let score = 0;
      let factors = 0;

      // Title similarity (already matched)
      score += 40;
      factors += 40;

      // Author similarity
      if (manga1.authors && manga2.authors) {
        const authors1 = manga1.authors.map((a) => a.name.toLowerCase());
        const authors2 = manga2.authors.map((a) => a.name.toLowerCase());
        const commonAuthors = authors1.filter((a) => authors2.includes(a));
        score +=
          (commonAuthors.length / Math.max(authors1.length, authors2.length)) *
          30;
      }
      factors += 30;

      // Genre similarity
      if (manga1.genres && manga2.genres) {
        const genres1 = manga1.genres.map((g) => g.name.toLowerCase());
        const genres2 = manga2.genres.map((g) => g.name.toLowerCase());
        const commonGenres = genres1.filter((g) => genres2.includes(g));
        score +=
          (commonGenres.length / Math.max(genres1.length, genres2.length)) * 20;
      }
      factors += 20;

      // Description similarity
      if (manga1.description && manga2.description) {
        const desc1 = manga1.description.toLowerCase();
        const desc2 = manga2.description.toLowerCase();
        const words1 = desc1.split(/\s+/);
        const words2 = desc2.split(/\s+/);
        const commonWords = words1.filter(
          (w) => words2.includes(w) && w.length > 3,
        );
        score +=
          (commonWords.length / Math.max(words1.length, words2.length)) * 10;
      }
      factors += 10;

      return Math.round((score / factors) * 100);
    },

    // Metadata management
    async updateMangaMetadata(mangaId, metadata) {
      try {
        const response = await api.put(
          `/v1/library/${mangaId}/metadata`,
          metadata,
        );

        // Update local manga data
        const index = this.manga.findIndex((item) => item.id === mangaId);
        if (index !== -1) {
          this.manga[index] = { ...this.manga[index], ...response.data };
        }

        return response.data;
      } catch (error) {
        console.error("Error updating metadata:", error);
        throw error;
      }
    },

    async bulkUpdateMetadata(mangaIds, metadata) {
      try {
        await api.post("/v1/library/bulk/update-metadata", {
          manga_ids: mangaIds,
          metadata,
        });

        // Refresh library to get updated data
        await this.fetchLibrary();
      } catch (error) {
        console.error("Error bulk updating metadata:", error);
        throw error;
      }
    },

    async deleteManga(mangaId) {
      try {
        await api.delete(`/v1/library/${mangaId}`);

        // Remove from local state
        this.manga = this.manga.filter((item) => item.id !== mangaId);
        this.selectedManga.delete(mangaId);

        // Update statistics
        this.calculateLocalStatistics();
      } catch (error) {
        console.error("Error deleting manga:", error);
        throw error;
      }
    },

    // Search and filtering enhancements
    async saveSearch(searchQuery, filters) {
      const savedSearch = {
        id: Date.now().toString(),
        name: searchQuery || "Untitled Search",
        query: searchQuery,
        filters: { ...filters },
        createdAt: new Date().toISOString(),
      };

      const savedSearches =
        JSON.parse(localStorage.getItem("savedSearches")) || [];
      savedSearches.unshift(savedSearch);

      // Keep only last 20 searches
      if (savedSearches.length > 20) {
        savedSearches.splice(20);
      }

      localStorage.setItem("savedSearches", JSON.stringify(savedSearches));
      return savedSearch;
    },

    getSavedSearches() {
      return JSON.parse(localStorage.getItem("savedSearches")) || [];
    },

    deleteSavedSearch(searchId) {
      const savedSearches =
        JSON.parse(localStorage.getItem("savedSearches")) || [];
      const filtered = savedSearches.filter((search) => search.id !== searchId);
      localStorage.setItem("savedSearches", JSON.stringify(filtered));
    },

    // Library export/import
    async exportLibrary() {
      try {
        const exportData = {
          manga: this.manga,
          customTags: this.customTags,
          statistics: this.statistics,
          exportDate: new Date().toISOString(),
          version: "1.0",
        };

        return JSON.stringify(exportData, null, 2);
      } catch (error) {
        console.error("Error exporting library:", error);
        throw error;
      }
    },

    async importLibrary(libraryData) {
      try {
        const data =
          typeof libraryData === "string"
            ? JSON.parse(libraryData)
            : libraryData;

        if (data.customTags) {
          this.customTags = [...this.customTags, ...data.customTags];
          localStorage.setItem("customTags", JSON.stringify(this.customTags));
        }

        // Import would typically involve API calls to add manga
        // For now, we'll just merge the data locally
        if (data.manga) {
          console.log(`Importing ${data.manga.length} manga items`);
          // This would be handled by the backend
        }

        return true;
      } catch (error) {
        console.error("Error importing library:", error);
        return false;
      }
    },
  },
});
