import { defineStore } from "pinia";
import api from "../services/api";

export const useDownloadsStore = defineStore("downloads", {
  state: () => ({
    activeDownloads: new Map(), // Map of download task IDs to download info
    downloadHistory: [],
    websocket: null,
    isConnected: false,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    bulkDownloads: new Map(), // Map of bulk download IDs to bulk download info
    pollingInterval: null, // Polling interval for download updates
  }),

  getters: {
    getActiveDownloads: (state) => Array.from(state.activeDownloads.values()),
    getDownloadById: (state) => (taskId) => state.activeDownloads.get(taskId),
    getDownloadsByManga: (state) => (mangaId) => {
      return Array.from(state.activeDownloads.values()).filter(
        (download) => download.manga_id === mangaId,
      );
    },
    getDownloadsByChapter: (state) => (chapterId) => {
      return Array.from(state.activeDownloads.values()).filter(
        (download) => download.chapter_id === chapterId,
      );
    },
    getTotalActiveDownloads: (state) => state.activeDownloads.size,
    isDownloading: (state) => (chapterId) => {
      return Array.from(state.activeDownloads.values()).some(
        (download) =>
          download.chapter_id === chapterId &&
          download.status === "downloading",
      );
    },
    getBulkDownloads: (state) => Array.from(state.bulkDownloads.values()),
    getBulkDownloadById: (state) => (bulkId) => state.bulkDownloads.get(bulkId),
    isBulkDownloading: (state) => (bulkId) => {
      const bulk = state.bulkDownloads.get(bulkId);
      return bulk && bulk.status === "downloading";
    },
  },

  actions: {
    async fetchActiveDownloads() {
      try {
        const response = await api.get("/v1/library/downloads");
        console.log("Downloads API response:", response.data);

        // Clear existing downloads and add fetched ones
        this.activeDownloads.clear();

        // Handle the response format: { tasks: [...], count: number }
        if (response.data.tasks && Array.isArray(response.data.tasks)) {
          console.log("Processing downloads:", response.data.tasks);
          response.data.tasks.forEach((download) => {
            console.log("Adding download to store:", download);
            this.activeDownloads.set(download.task_id, {
              ...download,
              // Ensure required fields exist
              progress: download.progress || 0,
              status: download.status || 'downloading',
              downloaded_pages: download.downloaded_pages || 0,
              total_pages: download.total_pages || 0,
            });
          });
        } else {
          console.log("No tasks found in response or invalid format");
        }
      } catch (error) {
        console.error("Error fetching active downloads:", error);
      }
    },

    async fetchDownloadHistory() {
      try {
        const response = await api.get("/v1/library/downloads/history");
        this.downloadHistory = response.data;
      } catch (error) {
        console.error("Error fetching download history:", error);
      }
    },

    async cancelDownload(taskId) {
      try {
        await api.delete(`/v1/library/downloads/${taskId}`);
        this.activeDownloads.delete(taskId);
      } catch (error) {
        console.error("Error canceling download:", error);
        throw error;
      }
    },

    async cancelAllDownloads() {
      try {
        const response = await api.delete("/v1/library/downloads");

        // Clear all active downloads from the store
        this.activeDownloads.clear();

        return response.data;
      } catch (error) {
        console.error("Error canceling all downloads:", error);
        throw error;
      }
    },

    async clearDownloadHistory() {
      try {
        const response = await api.delete("/v1/library/downloads/history");

        // Clear download history from the store
        this.downloadHistory = [];

        return response.data;
      } catch (error) {
        console.error("Error clearing download history:", error);
        throw error;
      }
    },

    // Bulk download management
    addBulkDownload(bulkDownloadData) {
      this.bulkDownloads.set(bulkDownloadData.id, {
        ...bulkDownloadData,
        chapter_downloads: new Set(), // Track individual chapter download IDs
      });
    },

    startBulkDownload(bulkId, mangaId, totalChapters) {
      this.bulkDownloads.set(bulkId, {
        id: bulkId,
        manga_id: mangaId,
        status: "downloading",
        total_chapters: totalChapters,
        completed_chapters: 0,
        failed_chapters: 0,
        started_at: new Date().toISOString(),
        chapter_downloads: new Set(), // Track individual chapter download IDs
      });
    },

    async cancelBulkDownload(bulkId) {
      const bulkDownload = this.bulkDownloads.get(bulkId);
      if (!bulkDownload) return;

      try {
        // Cancel all individual chapter downloads
        const cancelPromises = Array.from(bulkDownload.chapter_downloads).map(
          (taskId) => this.cancelDownload(taskId),
        );

        await Promise.allSettled(cancelPromises);

        // Update bulk download status
        bulkDownload.status = "cancelled";
        bulkDownload.cancelled_at = new Date().toISOString();

        console.log(`Bulk download ${bulkId} cancelled`);
      } catch (error) {
        console.error("Error canceling bulk download:", error);
        throw error;
      }
    },

    updateBulkDownloadProgress(bulkId, chapterTaskId, status, progress = null, completedChapters = null) {
      const bulkDownload = this.bulkDownloads.get(bulkId);
      if (!bulkDownload) return;

      // Add chapter download to tracking if provided
      if (chapterTaskId) {
        bulkDownload.chapter_downloads.add(chapterTaskId);
      }

      // Update status
      bulkDownload.status = status;

      // Update progress if provided
      if (progress !== null) {
        bulkDownload.progress = progress;
      }

      // Update completed chapters if provided
      if (completedChapters !== null) {
        bulkDownload.completed_chapters = completedChapters;
      }

      // Update counters based on status (legacy support)
      if (status === "completed" && completedChapters === null) {
        bulkDownload.completed_chapters++;
      } else if (status === "failed") {
        bulkDownload.failed_chapters = (bulkDownload.failed_chapters || 0) + 1;
      }

      // Check if bulk download is complete
      if (status === "completed" || bulkDownload.progress >= 100) {
        bulkDownload.status = "completed";
        bulkDownload.completed_at = new Date().toISOString();
        bulkDownload.progress = 100;
        bulkDownload.completed_chapters = bulkDownload.total_chapters;
      }
    },

    removeBulkDownload(bulkId) {
      this.bulkDownloads.delete(bulkId);
    },

    connectWebSocket() {
      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        return;
      }

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/api/v1/progress/ws`;

      try {
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
          console.log("Download WebSocket connected");
          this.isConnected = true;
          this.reconnectAttempts = 0;
        };

        this.websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        this.websocket.onclose = () => {
          console.log("Download WebSocket disconnected");
          this.isConnected = false;
          this.attemptReconnect();
        };

        this.websocket.onerror = (error) => {
          console.error("Download WebSocket error:", error);
        };
      } catch (error) {
        console.error("Error creating WebSocket connection:", error);
        this.attemptReconnect();
      }
    },

    disconnectWebSocket() {
      if (this.websocket) {
        this.websocket.close();
        this.websocket = null;
        this.isConnected = false;
      }
    },

    attemptReconnect() {
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.log("Max reconnection attempts reached");
        return;
      }

      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

      console.log(
        `Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`,
      );

      setTimeout(() => {
        this.connectWebSocket();
      }, delay);
    },

    handleWebSocketMessage(data) {
      switch (data.type) {
        case "download_started":
          this.activeDownloads.set(data.task_id, {
            task_id: data.task_id,
            manga_id: data.manga_id,
            chapter_id: data.chapter_id,
            status: "downloading",
            progress: 0,
            total_pages: data.total_pages || 0,
            downloaded_pages: 0,
            started_at: data.timestamp,
            error: null,
          });
          break;

        case "download_progress": {
          const progressDownload = this.activeDownloads.get(data.task_id);
          if (progressDownload) {
            progressDownload.progress = data.progress;
            progressDownload.downloaded_pages = data.downloaded_pages;
            progressDownload.total_pages = data.total_pages;
            progressDownload.status = "downloading";
          }
          break;
        }

        case "download_completed": {
          const completedDownload = this.activeDownloads.get(data.task_id);
          if (completedDownload) {
            completedDownload.status = "completed";
            completedDownload.progress = 100;
            completedDownload.completed_at = data.timestamp;

            // Move to history after a delay
            setTimeout(() => {
              this.activeDownloads.delete(data.task_id);
              this.downloadHistory.unshift(completedDownload);
            }, 5000);
          }
          break;
        }

        case "download_failed": {
          const failedDownload = this.activeDownloads.get(data.task_id);
          if (failedDownload) {
            failedDownload.status = "failed";
            failedDownload.error = data.error;
            failedDownload.failed_at = data.timestamp;

            // Move to history after a delay
            setTimeout(() => {
              this.activeDownloads.delete(data.task_id);
              this.downloadHistory.unshift(failedDownload);
            }, 10000);
          }
          break;
        }

        case "download_cancelled":
          this.activeDownloads.delete(data.task_id);
          break;

        default:
          console.log("Unknown WebSocket message type:", data.type);
      }
    },

    addDownload(downloadInfo) {
      this.activeDownloads.set(downloadInfo.task_id, downloadInfo);
    },

    updateDownloadProgress(taskId, progress) {
      const download = this.activeDownloads.get(taskId);
      if (download) {
        download.progress = progress.progress;
        download.downloaded_pages = progress.downloaded_pages;
        download.total_pages = progress.total_pages;
        download.status = progress.status;
      }
    },

    removeDownload(taskId) {
      this.activeDownloads.delete(taskId);
    },

    clearHistory() {
      this.downloadHistory = [];
    },

    async pauseDownload(taskId) {
      try {
        await api.post(`/v1/library/downloads/${taskId}/pause`);
        const download = this.activeDownloads.get(taskId);
        if (download) {
          download.status = 'paused';
        }
      } catch (error) {
        console.error("Error pausing download:", error);
        throw error;
      }
    },

    async resumeDownload(taskId) {
      try {
        await api.post(`/v1/library/downloads/${taskId}/resume`);
        const download = this.activeDownloads.get(taskId);
        if (download) {
          download.status = 'downloading';
        }
      } catch (error) {
        console.error("Error resuming download:", error);
        throw error;
      }
    },

    async retryDownload(downloadData) {
      try {
        // Re-add the failed download to the queue
        // This would typically call the same API endpoint that started the original download
        console.log("Retrying download:", downloadData);
        // Implementation depends on your backend API structure
      } catch (error) {
        console.error("Error retrying download:", error);
        throw error;
      }
    },

    // Start polling for download updates
    startPolling() {
      // Poll every 2 seconds for download updates
      this.pollingInterval = setInterval(() => {
        this.fetchActiveDownloads();
      }, 2000);
    },

    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval);
        this.pollingInterval = null;
      }
    },

    // Initialize the store
    init() {
      this.fetchActiveDownloads();
      this.connectWebSocket();
      this.startPolling(); // Start polling for real download updates
    },

    // Cleanup when store is no longer needed
    cleanup() {
      this.stopPolling();
      this.disconnectWebSocket();
    },
  },
});
