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
    preloadedImages: new Map(), // Cache for preloaded images
    preloadQueue: [], // Queue of images being preloaded

    // Reading statistics and progress tracking
    readingSession: {
      startTime: null,
      endTime: null,
      pagesRead: 0,
      timeSpent: 0, // in seconds
      mangaId: null,
      chapterId: null,
    },
    readingStats: {
      totalTimeSpent: parseInt(localStorage.getItem("totalTimeSpent")) || 0,
      totalPagesRead: parseInt(localStorage.getItem("totalPagesRead")) || 0,
      totalChaptersRead:
        parseInt(localStorage.getItem("totalChaptersRead")) || 0,
      totalMangaRead: parseInt(localStorage.getItem("totalMangaRead")) || 0,
      currentStreak: parseInt(localStorage.getItem("currentStreak")) || 0,
      longestStreak: parseInt(localStorage.getItem("longestStreak")) || 0,
      lastReadDate: localStorage.getItem("lastReadDate") || null,
    },
    bookmarks: JSON.parse(localStorage.getItem("bookmarks")) || [],
    readingHistory: JSON.parse(localStorage.getItem("readingHistory")) || [],
    achievements: JSON.parse(localStorage.getItem("achievements")) || [],
    unlockedAchievements:
      JSON.parse(localStorage.getItem("unlockedAchievements")) || [],
    settings: {
      readingDirection: localStorage.getItem("readingDirection") || "rtl", // rtl, ltr
      pageLayout: localStorage.getItem("pageLayout") || "single", // single, double, list, adaptive
      fitMode: localStorage.getItem("fitMode") || "width", // width, height, both, original
      showPageNumbers: localStorage.getItem("showPageNumbers") === "true",
      autoAdvance: localStorage.getItem("autoAdvance") === "true",
      preloadDistance: parseInt(localStorage.getItem("preloadDistance")) || 3, // number of pages to preload
      imageQuality: localStorage.getItem("imageQuality") || "high", // high, medium, low
      adaptiveMode: localStorage.getItem("adaptiveMode") === "true", // auto-detect content type

      // Theme and customization settings
      theme: localStorage.getItem("readerTheme") || "dark",
      customTheme: JSON.parse(localStorage.getItem("customTheme")) || null,
      uiLayout: localStorage.getItem("uiLayout") || "default",
      typography: JSON.parse(localStorage.getItem("typography")) || {
        fontFamily: "system-ui",
        fontSize: "16px",
        lineHeight: "1.6",
        letterSpacing: "0px",
        textColor: "#ffffff",
      },
      displayOptions: JSON.parse(localStorage.getItem("displayOptions")) || {
        pageMargin: 20,
        pagePadding: 10,
        borderRadius: 8,
        showShadows: true,
        transitionDuration: 300,
        backgroundColor: "#1a1a1a",
        uiOpacity: 0.9,
      },
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

    // Double-page mode getters
    getCurrentPagePair: (state) => {
      if (state.settings.pageLayout !== "double" || !state.pages.length) {
        const page = state.pages[state.currentPage - 1];
        return page ? [{ ...page, url: state.getCurrentPageUrl }] : [];
      }

      const leftPage = state.pages[state.currentPage - 1];
      const rightPage = state.pages[state.currentPage];

      // Apply quality settings to URLs
      const processPage = (page) => {
        if (!page) return null;
        const targetQuality = state.settings.imageQuality;
        let url = page.url;

        if (targetQuality !== "high" && page.url.includes("?")) {
          try {
            const urlObj = new URL(page.url);
            switch (targetQuality) {
              case "medium":
                urlObj.searchParams.set("quality", "75");
                urlObj.searchParams.set("width", "1200");
                break;
              case "low":
                urlObj.searchParams.set("quality", "60");
                urlObj.searchParams.set("width", "800");
                break;
            }
            url = urlObj.toString();
          } catch (error) {
            // Keep original URL if parsing fails
          }
        }

        return { ...page, url };
      };

      const processedLeft = processPage(leftPage);
      const processedRight = processPage(rightPage);

      // For RTL reading, swap the pages
      if (state.settings.readingDirection === "rtl") {
        return processedRight
          ? [processedRight, processedLeft]
          : [processedLeft];
      } else {
        return processedRight
          ? [processedLeft, processedRight]
          : [processedLeft];
      }
    },

    getEffectivePageCount: (state) => {
      if (state.settings.pageLayout === "double") {
        // In double-page mode, count page pairs
        return Math.ceil(state.pages.length / 2);
      }
      return state.pages.length;
    },

    getCurrentPageDisplay: (state, getters) => {
      if (state.settings.pageLayout === "double") {
        const pairIndex = Math.ceil(state.currentPage / 2);
        return `${pairIndex} / ${getters.getEffectivePageCount}`;
      }
      return `${state.currentPage} / ${state.pages.length}`;
    },

    getCurrentPageUrl: (state) => {
      if (
        !state.pages ||
        !state.pages.length ||
        state.currentPage > state.pages.length
      )
        return null;
      const page = state.pages[state.currentPage - 1];
      if (!page || !page.url) return null;

      const targetQuality = state.settings.imageQuality;

      // If original quality or no quality parameters available, return original URL
      if (targetQuality === "high" || !page.url.includes("?")) {
        return page.url;
      }

      // Add quality parameters to URL
      try {
        const url = new URL(page.url);
        switch (targetQuality) {
          case "medium":
            url.searchParams.set("quality", "75");
            url.searchParams.set("width", "1200");
            break;
          case "low":
            url.searchParams.set("quality", "60");
            url.searchParams.set("width", "800");
            break;
          default:
            break;
        }
        return url.toString();
      } catch (error) {
        return page.url; // Fallback to original URL if URL parsing fails
      }
    },

    // Reading statistics getters
    getReadingStats: (state) => state.readingStats,
    getCurrentSession: (state) => state.readingSession,
    getBookmarks: (state) => state.bookmarks,
    getReadingHistory: (state) => state.readingHistory,

    getFormattedReadingTime: (state) => {
      const totalMinutes = Math.floor(state.readingStats.totalTimeSpent / 60);
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;

      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes}m`;
    },

    getTodayReadingTime: (state) => {
      const today = new Date().toDateString();
      const todayHistory = state.readingHistory.filter(
        (session) => new Date(session.date).toDateString() === today,
      );

      return todayHistory.reduce(
        (total, session) => total + (session.timeSpent || 0),
        0,
      );
    },

    getWeeklyReadingStats: (state) => {
      const oneWeekAgo = new Date();
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

      const weeklyHistory = state.readingHistory.filter(
        (session) => new Date(session.date) >= oneWeekAgo,
      );

      return {
        timeSpent: weeklyHistory.reduce(
          (total, session) => total + (session.timeSpent || 0),
          0,
        ),
        pagesRead: weeklyHistory.reduce(
          (total, session) => total + (session.pagesRead || 0),
          0,
        ),
        chaptersRead: weeklyHistory.length,
      };
    },
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

        // Start reading session
        this.startReadingSession(mangaId, chapterId);

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

        // Trigger adaptive mode analysis if enabled
        if (this.settings.pageLayout === "adaptive") {
          setTimeout(() => this.analyzeContentType(), 100);
        }

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
        // Save reading position for resume functionality
        this.saveReadingPosition();
      }

      // Track page read for statistics
      this.trackPageRead();

      // Trigger image preloading
      this.preloadImages();
    },

    nextPage() {
      const increment = this.settings.pageLayout === "double" ? 2 : 1;

      if (this.currentPage + increment <= this.pages.length) {
        this.currentPage += increment;
      } else if (this.hasNextChapter && this.settings.autoAdvance) {
        this.loadNextChapter();
      }
    },

    prevPage() {
      const decrement = this.settings.pageLayout === "double" ? 2 : 1;

      if (this.currentPage - decrement >= 1) {
        this.currentPage -= decrement;
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

      // Track reading mode usage for achievements
      if (settings.pageLayout) {
        this.trackReadingModeUsage(settings.pageLayout);
      }

      // Save settings to localStorage
      Object.entries(this.settings).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          localStorage.setItem(key, value.toString());
        }
      });

      // Check achievements after settings change
      this.checkAchievements();
    },

    // Adaptive mode detection
    async analyzeContentType() {
      if (!this.pages.length || this.settings.pageLayout !== "adaptive") return;

      try {
        const sampleSize = Math.min(5, this.pages.length); // Analyze first 5 pages
        const imageAnalyses = [];

        for (let i = 0; i < sampleSize; i++) {
          const analysis = await this.analyzeImage(this.pages[i].url);
          if (analysis) {
            imageAnalyses.push(analysis);
          }
        }

        if (imageAnalyses.length === 0) return;

        // Calculate average dimensions and aspect ratios
        const avgWidth =
          imageAnalyses.reduce((sum, img) => sum + img.width, 0) /
          imageAnalyses.length;
        const avgHeight =
          imageAnalyses.reduce((sum, img) => sum + img.height, 0) /
          imageAnalyses.length;
        const avgAspectRatio = avgWidth / avgHeight;

        // Determine optimal reading mode
        let detectedMode = "single";

        // Check for long-strip content (webtoons)
        const tallImages = imageAnalyses.filter(
          (img) => img.height / img.width > 2,
        ).length;
        if (tallImages / imageAnalyses.length > 0.6) {
          detectedMode = "list";
        }
        // Check for wide images that might benefit from double-page
        else if (avgAspectRatio > 1.4 && avgWidth > 1200) {
          detectedMode = "double";
        }
        // Check if images are consistently wide enough for double-page
        else if (
          imageAnalyses.filter((img) => img.width > img.height * 1.3).length /
            imageAnalyses.length >
          0.7
        ) {
          detectedMode = "double";
        }

        // Apply detected mode
        if (detectedMode !== "adaptive") {
          this.settings.pageLayout = detectedMode;
          localStorage.setItem("pageLayout", detectedMode);
          console.log(`Adaptive mode detected: ${detectedMode}`);
        }
      } catch (error) {
        console.error("Error analyzing content type:", error);
      }
    },

    analyzeImage(url) {
      return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
          resolve({
            width: img.naturalWidth,
            height: img.naturalHeight,
            aspectRatio: img.naturalWidth / img.naturalHeight,
          });
        };
        img.onerror = () => resolve(null);
        img.src = url;
      });
    },

    // Image preloading system
    preloadImages() {
      if (!this.pages.length) return;

      const distance = this.settings.preloadDistance;
      const startIndex = Math.max(0, this.currentPage - 1);
      const endIndex = Math.min(this.pages.length - 1, startIndex + distance);

      // Clear old preloaded images that are too far away
      this.cleanupPreloadedImages();

      // Preload images in range
      for (let i = startIndex; i <= endIndex; i++) {
        const page = this.pages[i];
        if (page && !this.preloadedImages.has(page.url)) {
          this.preloadImage(page.url);
        }
      }
    },

    preloadImage(url) {
      if (this.preloadedImages.has(url) || this.preloadQueue.includes(url)) {
        return;
      }

      this.preloadQueue.push(url);

      const img = new Image();
      img.onload = () => {
        this.preloadedImages.set(url, img);
        this.preloadQueue = this.preloadQueue.filter((u) => u !== url);
      };
      img.onerror = () => {
        this.preloadQueue = this.preloadQueue.filter((u) => u !== url);
      };
      img.src = url;
    },

    cleanupPreloadedImages() {
      const distance = this.settings.preloadDistance;
      const currentIndex = this.currentPage - 1;
      const keepStart = Math.max(0, currentIndex - distance);
      const keepEnd = Math.min(
        this.pages.length - 1,
        currentIndex + distance * 2,
      );

      // Remove images that are too far from current position
      for (const [url] of this.preloadedImages) {
        const pageIndex = this.pages.findIndex((p) => p.url === url);
        if (pageIndex < keepStart || pageIndex > keepEnd) {
          this.preloadedImages.delete(url);
        }
      }
    },

    isImagePreloaded(url) {
      return this.preloadedImages.has(url);
    },

    // Image quality management
    getImageUrl(page, quality = null) {
      if (!page || !page.url) return null;

      const targetQuality = quality || this.settings.imageQuality;

      // If original quality or no quality parameters available, return original URL
      if (targetQuality === "high" || !page.url.includes("?")) {
        return page.url;
      }

      // Add quality parameters to URL
      const url = new URL(page.url);
      switch (targetQuality) {
        case "medium":
          url.searchParams.set("quality", "75");
          url.searchParams.set("width", "1200");
          break;
        case "low":
          url.searchParams.set("quality", "60");
          url.searchParams.set("width", "800");
          break;
        default:
          break;
      }

      return url.toString();
    },

    // Auto-adjust quality based on connection speed
    async detectConnectionSpeed() {
      try {
        const startTime = performance.now();
        const response = await fetch("/api/speed-test", { method: "HEAD" });
        const endTime = performance.now();
        const duration = endTime - startTime;

        // Simple heuristic: if response takes more than 500ms, use lower quality
        if (duration > 1000) {
          this.updateSettings({ imageQuality: "low" });
        } else if (duration > 500) {
          this.updateSettings({ imageQuality: "medium" });
        } else {
          this.updateSettings({ imageQuality: "high" });
        }
      } catch (error) {
        // Fallback to medium quality if speed test fails
        console.log("Connection speed test failed, using medium quality");
        this.updateSettings({ imageQuality: "medium" });
      }
    },

    // Reading session and statistics tracking
    startReadingSession(mangaId, chapterId) {
      this.readingSession = {
        startTime: Date.now(),
        endTime: null,
        pagesRead: 0,
        timeSpent: 0,
        mangaId,
        chapterId,
      };
    },

    endReadingSession() {
      if (!this.readingSession.startTime) return;

      this.readingSession.endTime = Date.now();
      this.readingSession.timeSpent = Math.floor(
        (this.readingSession.endTime - this.readingSession.startTime) / 1000,
      );

      // Update overall statistics
      this.readingStats.totalTimeSpent += this.readingSession.timeSpent;
      this.readingStats.totalPagesRead += this.readingSession.pagesRead;

      // Update reading streak
      this.updateReadingStreak();

      // Save to reading history
      this.saveReadingSession();

      // Persist statistics
      this.saveReadingStats();

      // Reset session
      this.readingSession = {
        startTime: null,
        endTime: null,
        pagesRead: 0,
        timeSpent: 0,
        mangaId: null,
        chapterId: null,
      };
    },

    trackPageRead() {
      if (this.readingSession.startTime) {
        this.readingSession.pagesRead++;
      }
    },

    updateReadingStreak() {
      const today = new Date().toDateString();
      const lastReadDate = this.readingStats.lastReadDate;

      if (!lastReadDate) {
        // First time reading
        this.readingStats.currentStreak = 1;
        this.readingStats.longestStreak = 1;
      } else {
        const lastRead = new Date(lastReadDate);
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);

        if (lastRead.toDateString() === yesterday.toDateString()) {
          // Consecutive day
          this.readingStats.currentStreak++;
          this.readingStats.longestStreak = Math.max(
            this.readingStats.longestStreak,
            this.readingStats.currentStreak,
          );
        } else if (lastRead.toDateString() !== today) {
          // Streak broken
          this.readingStats.currentStreak = 1;
        }
        // If lastRead is today, don't change streak
      }

      this.readingStats.lastReadDate = today;
    },

    saveReadingSession() {
      const sessionData = {
        ...this.readingSession,
        date: new Date().toISOString(),
        mangaTitle: this.manga?.title || "Unknown",
        chapterTitle: this.chapter?.title || "Unknown",
      };

      this.readingHistory.unshift(sessionData);

      // Keep only last 100 sessions
      if (this.readingHistory.length > 100) {
        this.readingHistory = this.readingHistory.slice(0, 100);
      }

      localStorage.setItem(
        "readingHistory",
        JSON.stringify(this.readingHistory),
      );
    },

    saveReadingStats() {
      Object.entries(this.readingStats).forEach(([key, value]) => {
        localStorage.setItem(key, value.toString());
      });

      // Check for new achievements
      this.checkAchievements();
    },

    // Bookmark management
    addBookmark(note = "") {
      if (!this.manga || !this.chapter) return;

      const bookmark = {
        id: Date.now().toString(),
        mangaId: this.manga.id,
        mangaTitle: this.manga.title,
        chapterId: this.chapter.id,
        chapterTitle: this.chapter.title,
        page: this.currentPage,
        note,
        createdAt: new Date().toISOString(),
        pageUrl: this.getCurrentPageUrl,
      };

      this.bookmarks.unshift(bookmark);
      localStorage.setItem("bookmarks", JSON.stringify(this.bookmarks));

      return bookmark;
    },

    removeBookmark(bookmarkId) {
      this.bookmarks = this.bookmarks.filter((b) => b.id !== bookmarkId);
      localStorage.setItem("bookmarks", JSON.stringify(this.bookmarks));
    },

    updateBookmark(bookmarkId, updates) {
      const index = this.bookmarks.findIndex((b) => b.id === bookmarkId);
      if (index !== -1) {
        this.bookmarks[index] = { ...this.bookmarks[index], ...updates };
        localStorage.setItem("bookmarks", JSON.stringify(this.bookmarks));
      }
    },

    getBookmarksForManga(mangaId) {
      return this.bookmarks.filter((b) => b.mangaId === mangaId);
    },

    getBookmarksForChapter(mangaId, chapterId) {
      return this.bookmarks.filter(
        (b) => b.mangaId === mangaId && b.chapterId === chapterId,
      );
    },

    hasBookmarkOnCurrentPage() {
      return this.bookmarks.some(
        (b) =>
          b.mangaId === this.manga?.id &&
          b.chapterId === this.chapter?.id &&
          b.page === this.currentPage,
      );
    },

    // Resume reading functionality
    getLastReadPosition(mangaId) {
      const recentSessions = this.readingHistory
        .filter((session) => session.mangaId === mangaId)
        .sort((a, b) => new Date(b.date) - new Date(a.date));

      return recentSessions[0] || null;
    },

    saveReadingPosition() {
      if (!this.manga || !this.chapter) return;

      const position = {
        mangaId: this.manga.id,
        chapterId: this.chapter.id,
        page: this.currentPage,
        timestamp: Date.now(),
        pageLayout: this.settings.pageLayout,
      };

      localStorage.setItem(
        `readingPosition_${this.manga.id}`,
        JSON.stringify(position),
      );
    },

    getReadingPosition(mangaId) {
      const saved = localStorage.getItem(`readingPosition_${mangaId}`);
      return saved ? JSON.parse(saved) : null;
    },

    // Achievements system
    getAchievementDefinitions() {
      return [
        {
          id: "first_page",
          title: "First Steps",
          description: "Read your first page",
          icon: "📖",
          requirement: { type: "pages", value: 1 },
        },
        {
          id: "page_turner",
          title: "Page Turner",
          description: "Read 100 pages",
          icon: "📚",
          requirement: { type: "pages", value: 100 },
        },
        {
          id: "bookworm",
          title: "Bookworm",
          description: "Read 1000 pages",
          icon: "🐛",
          requirement: { type: "pages", value: 1000 },
        },
        {
          id: "speed_reader",
          title: "Speed Reader",
          description: "Read 10000 pages",
          icon: "⚡",
          requirement: { type: "pages", value: 10000 },
        },
        {
          id: "first_hour",
          title: "Getting Started",
          description: "Spend 1 hour reading",
          icon: "⏰",
          requirement: { type: "time", value: 3600 }, // 1 hour in seconds
        },
        {
          id: "dedicated_reader",
          title: "Dedicated Reader",
          description: "Spend 10 hours reading",
          icon: "🕐",
          requirement: { type: "time", value: 36000 }, // 10 hours
        },
        {
          id: "marathon_reader",
          title: "Marathon Reader",
          description: "Spend 100 hours reading",
          icon: "🏃",
          requirement: { type: "time", value: 360000 }, // 100 hours
        },
        {
          id: "streak_starter",
          title: "Streak Starter",
          description: "Read for 3 consecutive days",
          icon: "🔥",
          requirement: { type: "streak", value: 3 },
        },
        {
          id: "consistent_reader",
          title: "Consistent Reader",
          description: "Read for 7 consecutive days",
          icon: "📅",
          requirement: { type: "streak", value: 7 },
        },
        {
          id: "reading_master",
          title: "Reading Master",
          description: "Read for 30 consecutive days",
          icon: "👑",
          requirement: { type: "streak", value: 30 },
        },
        {
          id: "bookmark_collector",
          title: "Bookmark Collector",
          description: "Create 10 bookmarks",
          icon: "🔖",
          requirement: { type: "bookmarks", value: 10 },
        },
        {
          id: "explorer",
          title: "Explorer",
          description: "Try all reading modes",
          icon: "🧭",
          requirement: {
            type: "modes",
            value: ["single", "double", "list", "adaptive"],
          },
        },
      ];
    },

    checkAchievements() {
      const definitions = this.getAchievementDefinitions();
      const newAchievements = [];

      definitions.forEach((achievement) => {
        // Skip if already unlocked
        if (this.unlockedAchievements.includes(achievement.id)) return;

        let unlocked = false;

        switch (achievement.requirement.type) {
          case "pages":
            unlocked =
              this.readingStats.totalPagesRead >= achievement.requirement.value;
            break;
          case "time":
            unlocked =
              this.readingStats.totalTimeSpent >= achievement.requirement.value;
            break;
          case "streak":
            unlocked =
              this.readingStats.currentStreak >=
                achievement.requirement.value ||
              this.readingStats.longestStreak >= achievement.requirement.value;
            break;
          case "bookmarks":
            unlocked = this.bookmarks.length >= achievement.requirement.value;
            break;
          case "modes": {
            const usedModes =
              JSON.parse(localStorage.getItem("usedReadingModes")) || [];
            unlocked = achievement.requirement.value.every((mode) =>
              usedModes.includes(mode),
            );
            break;
          }
        }

        if (unlocked) {
          this.unlockedAchievements.push(achievement.id);
          newAchievements.push(achievement);
        }
      });

      if (newAchievements.length > 0) {
        localStorage.setItem(
          "unlockedAchievements",
          JSON.stringify(this.unlockedAchievements),
        );
        this.showAchievementNotifications(newAchievements);
      }

      return newAchievements;
    },

    showAchievementNotifications(achievements) {
      // This will be handled by the UI component
      achievements.forEach((achievement) => {
        console.log(
          `🎉 Achievement Unlocked: ${achievement.title} - ${achievement.description}`,
        );
      });
    },

    trackReadingModeUsage(mode) {
      const usedModes =
        JSON.parse(localStorage.getItem("usedReadingModes")) || [];
      if (!usedModes.includes(mode)) {
        usedModes.push(mode);
        localStorage.setItem("usedReadingModes", JSON.stringify(usedModes));
      }
    },

    getUnlockedAchievements() {
      const definitions = this.getAchievementDefinitions();
      return definitions.filter((achievement) =>
        this.unlockedAchievements.includes(achievement.id),
      );
    },

    getAchievementProgress(achievementId) {
      const achievement = this.getAchievementDefinitions().find(
        (a) => a.id === achievementId,
      );
      if (!achievement) return 0;

      switch (achievement.requirement.type) {
        case "pages":
          return Math.min(
            100,
            (this.readingStats.totalPagesRead / achievement.requirement.value) *
              100,
          );
        case "time":
          return Math.min(
            100,
            (this.readingStats.totalTimeSpent / achievement.requirement.value) *
              100,
          );
        case "streak":
          return Math.min(
            100,
            (Math.max(
              this.readingStats.currentStreak,
              this.readingStats.longestStreak,
            ) /
              achievement.requirement.value) *
              100,
          );
        case "bookmarks":
          return Math.min(
            100,
            (this.bookmarks.length / achievement.requirement.value) * 100,
          );
        case "modes": {
          const usedModes =
            JSON.parse(localStorage.getItem("usedReadingModes")) || [];
          const requiredModes = achievement.requirement.value;
          const completedModes = requiredModes.filter((mode) =>
            usedModes.includes(mode),
          ).length;
          return Math.min(100, (completedModes / requiredModes.length) * 100);
        }
        default:
          return 0;
      }
    },

    // Theme and customization methods
    getThemeDefinitions() {
      return {
        dark: {
          id: "dark",
          name: "Dark",
          description: "Classic dark theme for comfortable reading",
          colors: {
            background: "#1a1a1a",
            surface: "#2d2d2d",
            primary: "#3b82f6",
            secondary: "#6b7280",
            accent: "#8b5cf6",
            text: "#ffffff",
            textSecondary: "#d1d5db",
            border: "#374151",
            success: "#10b981",
            warning: "#f59e0b",
            error: "#ef4444",
          },
          ui: {
            toolbarBg: "rgba(45, 45, 45, 0.95)",
            overlayBg: "rgba(0, 0, 0, 0.8)",
            buttonHover: "rgba(255, 255, 255, 0.1)",
            shadow: "0 4px 12px rgba(0, 0, 0, 0.3)",
          },
        },
        light: {
          id: "light",
          name: "Light",
          description: "Clean light theme for daytime reading",
          colors: {
            background: "#ffffff",
            surface: "#f8fafc",
            primary: "#3b82f6",
            secondary: "#6b7280",
            accent: "#8b5cf6",
            text: "#1f2937",
            textSecondary: "#6b7280",
            border: "#e5e7eb",
            success: "#10b981",
            warning: "#f59e0b",
            error: "#ef4444",
          },
          ui: {
            toolbarBg: "rgba(248, 250, 252, 0.95)",
            overlayBg: "rgba(255, 255, 255, 0.9)",
            buttonHover: "rgba(0, 0, 0, 0.05)",
            shadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
          },
        },
        sepia: {
          id: "sepia",
          name: "Sepia",
          description: "Warm sepia theme to reduce eye strain",
          colors: {
            background: "#f4f1e8",
            surface: "#ede6d3",
            primary: "#8b4513",
            secondary: "#a0522d",
            accent: "#cd853f",
            text: "#3e2723",
            textSecondary: "#5d4037",
            border: "#d7ccc8",
            success: "#689f38",
            warning: "#f57c00",
            error: "#d32f2f",
          },
          ui: {
            toolbarBg: "rgba(237, 230, 211, 0.95)",
            overlayBg: "rgba(244, 241, 232, 0.9)",
            buttonHover: "rgba(62, 39, 35, 0.1)",
            shadow: "0 4px 12px rgba(62, 39, 35, 0.2)",
          },
        },
        night: {
          id: "night",
          name: "Night",
          description: "Ultra-dark theme for late night reading",
          colors: {
            background: "#0a0a0a",
            surface: "#1a1a1a",
            primary: "#4f46e5",
            secondary: "#6b7280",
            accent: "#7c3aed",
            text: "#e5e7eb",
            textSecondary: "#9ca3af",
            border: "#374151",
            success: "#059669",
            warning: "#d97706",
            error: "#dc2626",
          },
          ui: {
            toolbarBg: "rgba(26, 26, 26, 0.98)",
            overlayBg: "rgba(0, 0, 0, 0.9)",
            buttonHover: "rgba(255, 255, 255, 0.05)",
            shadow: "0 4px 12px rgba(0, 0, 0, 0.5)",
          },
        },
        custom: {
          id: "custom",
          name: "Custom",
          description: "Your personalized theme",
          colors: {},
          ui: {},
        },
      };
    },

    getCurrentTheme() {
      const themes = this.getThemeDefinitions();
      if (this.settings.theme === "custom" && this.settings.customTheme) {
        return { ...themes.custom, ...this.settings.customTheme };
      }
      return themes[this.settings.theme] || themes.dark;
    },

    updateTheme(themeId, customTheme = null) {
      this.settings.theme = themeId;
      if (customTheme) {
        this.settings.customTheme = customTheme;
        localStorage.setItem("customTheme", JSON.stringify(customTheme));
      }
      localStorage.setItem("readerTheme", themeId);
      this.applyTheme();
    },

    applyTheme() {
      const theme = this.getCurrentTheme();
      const root = document.documentElement;

      // Apply CSS custom properties
      Object.entries(theme.colors).forEach(([key, value]) => {
        root.style.setProperty(`--reader-${key}`, value);
      });

      Object.entries(theme.ui).forEach(([key, value]) => {
        root.style.setProperty(`--reader-ui-${key}`, value);
      });

      // Apply display options
      Object.entries(this.settings.displayOptions).forEach(([key, value]) => {
        root.style.setProperty(
          `--reader-display-${key}`,
          typeof value === "number" ? `${value}px` : value,
        );
      });

      // Apply typography
      Object.entries(this.settings.typography).forEach(([key, value]) => {
        root.style.setProperty(`--reader-typography-${key}`, value);
      });
    },

    createCustomTheme(baseThemeId, customizations) {
      const baseTheme = this.getThemeDefinitions()[baseThemeId];
      const customTheme = {
        ...baseTheme,
        id: "custom",
        name: "Custom Theme",
        colors: { ...baseTheme.colors, ...customizations.colors },
        ui: { ...baseTheme.ui, ...customizations.ui },
      };

      this.updateTheme("custom", customTheme);
      return customTheme;
    },

    exportTheme() {
      const theme = this.getCurrentTheme();
      const exportData = {
        theme,
        typography: this.settings.typography,
        displayOptions: this.settings.displayOptions,
        uiLayout: this.settings.uiLayout,
        exportDate: new Date().toISOString(),
        version: "1.0",
      };

      return JSON.stringify(exportData, null, 2);
    },

    importTheme(themeData) {
      try {
        const data =
          typeof themeData === "string" ? JSON.parse(themeData) : themeData;

        if (data.theme) {
          this.updateTheme("custom", data.theme);
        }

        if (data.typography) {
          this.settings.typography = {
            ...this.settings.typography,
            ...data.typography,
          };
          localStorage.setItem(
            "typography",
            JSON.stringify(this.settings.typography),
          );
        }

        if (data.displayOptions) {
          this.settings.displayOptions = {
            ...this.settings.displayOptions,
            ...data.displayOptions,
          };
          localStorage.setItem(
            "displayOptions",
            JSON.stringify(this.settings.displayOptions),
          );
        }

        if (data.uiLayout) {
          this.settings.uiLayout = data.uiLayout;
          localStorage.setItem("uiLayout", data.uiLayout);
        }

        this.applyTheme();
        return true;
      } catch (error) {
        console.error("Failed to import theme:", error);
        return false;
      }
    },

    updateTypography(updates) {
      this.settings.typography = { ...this.settings.typography, ...updates };
      localStorage.setItem(
        "typography",
        JSON.stringify(this.settings.typography),
      );
      this.applyTheme();
    },

    updateDisplayOptions(updates) {
      this.settings.displayOptions = {
        ...this.settings.displayOptions,
        ...updates,
      };
      localStorage.setItem(
        "displayOptions",
        JSON.stringify(this.settings.displayOptions),
      );
      this.applyTheme();
    },

    updateUILayout(layout) {
      this.settings.uiLayout = layout;
      localStorage.setItem("uiLayout", layout);
      this.applyUILayout();
    },

    applyUILayout() {
      const root = document.documentElement;
      root.setAttribute("data-ui-layout", this.settings.uiLayout);
    },

    getUILayoutDefinitions() {
      return {
        default: {
          id: "default",
          name: "Default",
          description: "Standard layout with top toolbar",
          toolbar: { position: "top", alignment: "center" },
          pageNumbers: { position: "bottom-center", visible: true },
          navigation: { position: "sides", visible: true },
          bookmarkButton: { position: "toolbar", visible: true },
        },
        minimal: {
          id: "minimal",
          name: "Minimal",
          description: "Clean layout with minimal UI",
          toolbar: { position: "top", alignment: "center", autoHide: true },
          pageNumbers: { position: "bottom-right", visible: true },
          navigation: { position: "hidden", visible: false },
          bookmarkButton: { position: "floating-right", visible: true },
        },
        immersive: {
          id: "immersive",
          name: "Immersive",
          description: "Full-screen reading with hidden UI",
          toolbar: { position: "hidden", alignment: "center", autoHide: true },
          pageNumbers: { position: "hidden", visible: false },
          navigation: { position: "overlay", visible: true },
          bookmarkButton: { position: "floating-bottom", visible: true },
        },
        sidebar: {
          id: "sidebar",
          name: "Sidebar",
          description: "Vertical toolbar on the side",
          toolbar: { position: "left", alignment: "top" },
          pageNumbers: { position: "bottom-left", visible: true },
          navigation: { position: "toolbar", visible: true },
          bookmarkButton: { position: "toolbar", visible: true },
        },
        bottom: {
          id: "bottom",
          name: "Bottom Bar",
          description: "Controls at the bottom",
          toolbar: { position: "bottom", alignment: "center" },
          pageNumbers: { position: "top-center", visible: true },
          navigation: { position: "toolbar", visible: true },
          bookmarkButton: { position: "toolbar", visible: true },
        },
      };
    },

    getCurrentUILayout() {
      const layouts = this.getUILayoutDefinitions();
      return layouts[this.settings.uiLayout] || layouts.default;
    },

    resetToDefaultTheme() {
      this.settings.theme = "dark";
      this.settings.customTheme = null;
      this.settings.typography = {
        fontFamily: "system-ui",
        fontSize: "16px",
        lineHeight: "1.6",
        letterSpacing: "0px",
        textColor: "#ffffff",
      };
      this.settings.displayOptions = {
        pageMargin: 20,
        pagePadding: 10,
        borderRadius: 8,
        showShadows: true,
        transitionDuration: 300,
        backgroundColor: "#1a1a1a",
        uiOpacity: 0.9,
      };
      this.settings.uiLayout = "default";

      // Clear localStorage
      localStorage.removeItem("readerTheme");
      localStorage.removeItem("customTheme");
      localStorage.removeItem("typography");
      localStorage.removeItem("displayOptions");
      localStorage.removeItem("uiLayout");

      this.applyTheme();
      this.applyUILayout();
    },
  },
});
