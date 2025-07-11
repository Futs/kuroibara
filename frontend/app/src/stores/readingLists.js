import { defineStore } from "pinia";
import api from "../services/api";

export const useReadingListsStore = defineStore("readingLists", {
  state: () => ({
    readingLists: [],
    currentReadingList: null,
    loading: false,
    error: null,
  }),

  getters: {
    getReadingLists: (state) => state.readingLists,
    getCurrentReadingList: (state) => state.currentReadingList,
    getLoading: (state) => state.loading,
    getError: (state) => state.error,
  },

  actions: {
    async fetchReadingLists() {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get("/v1/reading-lists");
        this.readingLists = response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to fetch reading lists";
        console.error("Reading lists fetch error:", error);
      } finally {
        this.loading = false;
      }
    },

    async fetchReadingList(id) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.get(`/v1/reading-lists/${id}`);
        this.currentReadingList = response.data;
        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to fetch reading list";
        console.error("Reading list fetch error:", error);
      } finally {
        this.loading = false;
      }
    },

    async createReadingList(readingListData) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.post("/v1/reading-lists", readingListData);
        await this.fetchReadingLists(); // Refresh the list
        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to create reading list";
        console.error("Create reading list error:", error);
        throw error; // Re-throw so calling code can handle it
      } finally {
        this.loading = false;
      }
    },

    async updateReadingList(id, readingListData) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.put(
          `/v1/reading-lists/${id}`,
          readingListData,
        );
        await this.fetchReadingLists(); // Refresh the list
        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to update reading list";
        console.error("Update reading list error:", error);
        throw error; // Re-throw so calling code can handle it
      } finally {
        this.loading = false;
      }
    },

    async deleteReadingList(id) {
      this.loading = true;
      this.error = null;

      try {
        await api.delete(`/v1/reading-lists/${id}`);
        await this.fetchReadingLists(); // Refresh the list
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to delete reading list";
        console.error("Delete reading list error:", error);
        throw error; // Re-throw so calling code can handle it
      } finally {
        this.loading = false;
      }
    },

    async addMangaToReadingList(readingListId, mangaId) {
      this.loading = true;
      this.error = null;

      try {
        await api.post(`/v1/reading-lists/${readingListId}/manga`, {
          manga_id: mangaId,
        });
        if (
          this.currentReadingList &&
          this.currentReadingList.id === readingListId
        ) {
          await this.fetchReadingList(readingListId); // Refresh current list
        }
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to add manga to reading list";
        console.error("Add manga to reading list error:", error);
        throw error; // Re-throw so calling code can handle it
      } finally {
        this.loading = false;
      }
    },

    async removeMangaFromReadingList(readingListId, mangaId) {
      this.loading = true;
      this.error = null;

      try {
        await api.delete(`/v1/reading-lists/${readingListId}/manga/${mangaId}`);
        if (
          this.currentReadingList &&
          this.currentReadingList.id === readingListId
        ) {
          await this.fetchReadingList(readingListId); // Refresh current list
        }
      } catch (error) {
        this.error =
          error.response?.data?.detail ||
          "Failed to remove manga from reading list";
        console.error("Remove manga from reading list error:", error);
        throw error; // Re-throw so calling code can handle it
      } finally {
        this.loading = false;
      }
    },

    clearError() {
      this.error = null;
    },

    clearCurrentReadingList() {
      this.currentReadingList = null;
    },
  },
});
