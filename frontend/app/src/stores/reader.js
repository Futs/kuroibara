import { defineStore } from "pinia";
import api from "../services/api";

export const useReaderStore = defineStore("reader", {
  state: () => ({
    manga: null,
    chapter: null,
    chapters: [],
    pages: [],
    currentPage: 1,
    loading: false,
    error: null,
    settings: {
      readingDirection: localStorage.getItem("readingDirection") || "rtl", // rtl, ltr
      pageLayout: localStorage.getItem("pageLayout") || "single", // single, double
      fitMode: localStorage.getItem("fitMode") || "width", // width, height, both
      showPageNumbers: localStorage.getItem("showPageNumbers") === "true",
      autoAdvance: localStorage.getItem("autoAdvance") === "true",
    },
  }),

  getters: {
    getManga: (state) => state.manga,
    getChapter: (state) => state.chapter,
    getChapters: (state) => state.chapters,
    getPages: (state) => state.pages,
    getCurrentPage: (state) => state.currentPage,
    getSettings: (state) => state.settings,
    getTotalPages: (state) => state.pages.length,
    hasNextPage: (state) => state.currentPage < state.pages.length,
    hasPrevPage: (state) => state.currentPage > 1,
    hasNextChapter: (state) => {
      if (!state.chapters.length || !state.chapter) return false;
      const currentIndex = state.chapters.findIndex(
        (c) => c.id === state.chapter.id,
      );
      return currentIndex < state.chapters.length - 1;
    },
    hasPrevChapter: (state) => {
      if (!state.chapters.length || !state.chapter) return false;
      const currentIndex = state.chapters.findIndex(
        (c) => c.id === state.chapter.id,
      );
      return currentIndex > 0;
    },
  },

  actions: {
    async fetchManga(mangaId) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(`/v1/manga/${mangaId}`);
        this.manga = response.data;
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.detail || "Failed to fetch manga";
        console.error("Manga fetch error:", error);
      } finally {
        this.loading = false;
      }
    },

    async fetchChapters(mangaId) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(`/v1/manga/${mangaId}/chapters`);
        this.chapters = response.data;
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.detail || "Failed to fetch chapters";
        console.error("Chapters fetch error:", error);
      } finally {
        this.loading = false;
      }
    },

    async fetchChapter(mangaId, chapterId) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(
          `/v1/manga/${mangaId}/chapters/${chapterId}`,
        );
        this.chapter = response.data;
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.detail || "Failed to fetch chapter";
        console.error("Chapter fetch error:", error);
      } finally {
        this.loading = false;
      }
    },

    async fetchPages(mangaId, chapterId) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(
          `/v1/manga/${mangaId}/chapters/${chapterId}/pages`,
        );
        this.pages = response.data;
        return response.data;
      } catch (error) {
        this.error = error.response?.data?.detail || "Failed to fetch pages";
        console.error("Pages fetch error:", error);
      } finally {
        this.loading = false;
      }
    },

    async updateReadingProgress(mangaId, chapterId, page) {
      try {
        await api.post(`/v1/library/${mangaId}/progress`, {
          chapter_id: chapterId,
          page,
        });
      } catch (error) {
        console.error("Failed to update reading progress:", error);
      }
    },

    setCurrentPage(page) {
      this.currentPage = page;
      if (this.manga && this.chapter) {
        this.updateReadingProgress(this.manga.id, this.chapter.id, page);
      }
    },

    nextPage() {
      if (this.hasNextPage) {
        this.currentPage++;
      } else if (this.hasNextChapter && this.settings.autoAdvance) {
        this.loadNextChapter();
      }
    },

    prevPage() {
      if (this.hasPrevPage) {
        this.currentPage--;
      } else if (this.hasPrevChapter && this.settings.autoAdvance) {
        this.loadPrevChapter();
      }
    },

    async loadNextChapter() {
      if (!this.hasNextChapter) return;

      const currentIndex = this.chapters.findIndex(
        (c) => c.id === this.chapter.id,
      );
      const nextChapter = this.chapters[currentIndex + 1];

      await this.fetchChapter(this.manga.id, nextChapter.id);
      await this.fetchPages(this.manga.id, nextChapter.id);
      this.currentPage = 1;
    },

    async loadPrevChapter() {
      if (!this.hasPrevChapter) return;

      const currentIndex = this.chapters.findIndex(
        (c) => c.id === this.chapter.id,
      );
      const prevChapter = this.chapters[currentIndex - 1];

      await this.fetchChapter(this.manga.id, prevChapter.id);
      await this.fetchPages(this.manga.id, prevChapter.id);
      this.currentPage = this.pages.length;
    },

    updateSettings(settings) {
      this.settings = { ...this.settings, ...settings };

      // Save settings to localStorage
      Object.entries(this.settings).forEach(([key, value]) => {
        localStorage.setItem(key, value.toString());
      });
    },
  },
});
