import { defineStore } from "pinia";
import axios from "axios";

export const useSettingsStore = defineStore("settings", {
  state: () => ({
    theme: localStorage.getItem("theme") || "light", // light, dark, system
    nsfwBlur: localStorage.getItem("nsfwBlur") === "true",
    downloadQuality: localStorage.getItem("downloadQuality") || "high", // low, medium, high
    downloadPath: localStorage.getItem("downloadPath") || "/app/storage",

    // Naming settings
    namingFormatManga:
      localStorage.getItem("namingFormatManga") ||
      "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}",
    namingFormatChapter:
      localStorage.getItem("namingFormatChapter") ||
      "{Chapter Number} - {Chapter Name}",
    autoOrganizeImports:
      localStorage.getItem("autoOrganizeImports") !== "false", // default true
    createCbzFiles: localStorage.getItem("createCbzFiles") !== "false", // default true
    preserveOriginalFiles:
      localStorage.getItem("preserveOriginalFiles") === "true", // default false

    // Chapter update settings
    chapterAutoRefreshInterval:
      parseInt(localStorage.getItem("chapterAutoRefreshInterval")) || 300, // 5 minutes
    chapterCheckOnTabFocus:
      localStorage.getItem("chapterCheckOnTabFocus") !== "false", // default true
    chapterShowUpdateNotifications:
      localStorage.getItem("chapterShowUpdateNotifications") !== "false", // default true
    chapterEnableManualRefresh:
      localStorage.getItem("chapterEnableManualRefresh") !== "false", // default true

    // Storage settings
    storageType: localStorage.getItem("storageType") || "local",
    maxUploadSize: localStorage.getItem("maxUploadSize") || "100MB",

    loading: false,
    error: null,
  }),

  getters: {
    getTheme: (state) => state.theme,
    getNsfwBlur: (state) => state.nsfwBlur,
    getDownloadQuality: (state) => state.downloadQuality,
    getDownloadPath: (state) => state.downloadPath,

    // Naming settings getters
    getNamingFormatManga: (state) => state.namingFormatManga,
    getNamingFormatChapter: (state) => state.namingFormatChapter,
    getAutoOrganizeImports: (state) => state.autoOrganizeImports,
    getCreateCbzFiles: (state) => state.createCbzFiles,
    getPreserveOriginalFiles: (state) => state.preserveOriginalFiles,

    // Chapter update settings getters
    getChapterAutoRefreshInterval: (state) => state.chapterAutoRefreshInterval,
    getChapterCheckOnTabFocus: (state) => state.chapterCheckOnTabFocus,
    getChapterShowUpdateNotifications: (state) =>
      state.chapterShowUpdateNotifications,
    getChapterEnableManualRefresh: (state) => state.chapterEnableManualRefresh,

    // Storage settings getters
    getStorageType: (state) => state.storageType,
    getMaxUploadSize: (state) => state.maxUploadSize,
  },

  actions: {
    async fetchUserSettings() {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.get("/v1/users/settings");

        // Update local settings from server
        const {
          theme,
          nsfw_blur,
          download_quality,
          download_path,
          naming_format_manga,
          naming_format_chapter,
          auto_organize_imports,
          create_cbz_files,
          preserve_original_files,
          chapter_auto_refresh_interval,
          chapter_check_on_tab_focus,
          chapter_show_update_notifications,
          chapter_enable_manual_refresh,
          storage_type,
          max_upload_size,
        } = response.data;

        this.theme = theme || this.theme;
        this.nsfwBlur = nsfw_blur !== undefined ? nsfw_blur : this.nsfwBlur;
        this.downloadQuality = download_quality || this.downloadQuality;
        this.downloadPath = download_path || this.downloadPath;

        // Update naming settings
        this.namingFormatManga = naming_format_manga || this.namingFormatManga;
        this.namingFormatChapter =
          naming_format_chapter || this.namingFormatChapter;
        this.autoOrganizeImports =
          auto_organize_imports !== undefined
            ? auto_organize_imports
            : this.autoOrganizeImports;
        this.createCbzFiles =
          create_cbz_files !== undefined
            ? create_cbz_files
            : this.createCbzFiles;
        this.preserveOriginalFiles =
          preserve_original_files !== undefined
            ? preserve_original_files
            : this.preserveOriginalFiles;

        // Update chapter update settings
        this.chapterAutoRefreshInterval =
          chapter_auto_refresh_interval !== undefined
            ? chapter_auto_refresh_interval
            : this.chapterAutoRefreshInterval;
        this.chapterCheckOnTabFocus =
          chapter_check_on_tab_focus !== undefined
            ? chapter_check_on_tab_focus
            : this.chapterCheckOnTabFocus;
        this.chapterShowUpdateNotifications =
          chapter_show_update_notifications !== undefined
            ? chapter_show_update_notifications
            : this.chapterShowUpdateNotifications;
        this.chapterEnableManualRefresh =
          chapter_enable_manual_refresh !== undefined
            ? chapter_enable_manual_refresh
            : this.chapterEnableManualRefresh;

        // Update storage settings
        this.storageType = storage_type || this.storageType;
        this.maxUploadSize = max_upload_size || this.maxUploadSize;

        // Save to localStorage and apply theme
        this.saveToLocalStorage();
        this.applyTheme();
      } catch (error) {
        // Don't set error for authentication issues, just log them
        if (error.response?.status === 401 || error.response?.status === 403) {
          console.log("User not authenticated, using local settings");
        } else {
          this.error =
            error.response?.data?.detail || "Failed to fetch settings";
          console.error("Settings fetch error:", error);
        }
      } finally {
        this.loading = false;
      }
    },

    async updateUserSettings() {
      this.loading = true;
      this.error = null;

      try {
        await axios.put("/v1/users/settings", {
          theme: this.theme,
          nsfw_blur: this.nsfwBlur,
          download_quality: this.downloadQuality,
          download_path: this.downloadPath,
          naming_format_manga: this.namingFormatManga,
          naming_format_chapter: this.namingFormatChapter,
          auto_organize_imports: this.autoOrganizeImports,
          create_cbz_files: this.createCbzFiles,
          preserve_original_files: this.preserveOriginalFiles,
          chapter_auto_refresh_interval: this.chapterAutoRefreshInterval,
          chapter_check_on_tab_focus: this.chapterCheckOnTabFocus,
          chapter_show_update_notifications:
            this.chapterShowUpdateNotifications,
          chapter_enable_manual_refresh: this.chapterEnableManualRefresh,
          storage_type: this.storageType,
          max_upload_size: this.maxUploadSize,
        });

        // Save to localStorage
        this.saveToLocalStorage();
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to update settings";
        console.error("Settings update error:", error);
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

    toggleNsfwBlur() {
      this.nsfwBlur = !this.nsfwBlur;
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

    // Naming settings methods
    setNamingSettings(settings) {
      if (settings.namingFormatManga !== undefined) {
        this.namingFormatManga = settings.namingFormatManga;
      }
      if (settings.namingFormatChapter !== undefined) {
        this.namingFormatChapter = settings.namingFormatChapter;
      }
      if (settings.autoOrganizeImports !== undefined) {
        this.autoOrganizeImports = settings.autoOrganizeImports;
      }
      if (settings.createCbzFiles !== undefined) {
        this.createCbzFiles = settings.createCbzFiles;
      }
      if (settings.preserveOriginalFiles !== undefined) {
        this.preserveOriginalFiles = settings.preserveOriginalFiles;
      }
      this.saveToLocalStorage();
    },

    // Chapter update settings methods
    setChapterUpdateSettings(settings) {
      if (settings.chapterAutoRefreshInterval !== undefined) {
        this.chapterAutoRefreshInterval = settings.chapterAutoRefreshInterval;
      }
      if (settings.chapterCheckOnTabFocus !== undefined) {
        this.chapterCheckOnTabFocus = settings.chapterCheckOnTabFocus;
      }
      if (settings.chapterShowUpdateNotifications !== undefined) {
        this.chapterShowUpdateNotifications =
          settings.chapterShowUpdateNotifications;
      }
      if (settings.chapterEnableManualRefresh !== undefined) {
        this.chapterEnableManualRefresh = settings.chapterEnableManualRefresh;
      }
      this.saveToLocalStorage();
    },

    // Storage settings methods
    setStorageType(type) {
      this.storageType = type;
      this.saveToLocalStorage();
    },

    setMaxUploadSize(size) {
      this.maxUploadSize = size;
      this.saveToLocalStorage();
    },

    saveToLocalStorage() {
      localStorage.setItem("theme", this.theme);
      localStorage.setItem("nsfwBlur", this.nsfwBlur.toString());
      localStorage.setItem("downloadQuality", this.downloadQuality);
      localStorage.setItem("downloadPath", this.downloadPath);

      // Save naming settings
      localStorage.setItem("namingFormatManga", this.namingFormatManga);
      localStorage.setItem("namingFormatChapter", this.namingFormatChapter);
      localStorage.setItem(
        "autoOrganizeImports",
        this.autoOrganizeImports.toString(),
      );
      localStorage.setItem("createCbzFiles", this.createCbzFiles.toString());
      localStorage.setItem(
        "preserveOriginalFiles",
        this.preserveOriginalFiles.toString(),
      );

      // Save chapter update settings
      localStorage.setItem(
        "chapterAutoRefreshInterval",
        this.chapterAutoRefreshInterval.toString(),
      );
      localStorage.setItem(
        "chapterCheckOnTabFocus",
        this.chapterCheckOnTabFocus.toString(),
      );
      localStorage.setItem(
        "chapterShowUpdateNotifications",
        this.chapterShowUpdateNotifications.toString(),
      );
      localStorage.setItem(
        "chapterEnableManualRefresh",
        this.chapterEnableManualRefresh.toString(),
      );

      // Save storage settings
      localStorage.setItem("storageType", this.storageType);
      localStorage.setItem("maxUploadSize", this.maxUploadSize);
    },

    applyTheme() {
      const isDark =
        this.theme === "dark" ||
        (this.theme === "system" &&
          window.matchMedia("(prefers-color-scheme: dark)").matches);

      if (isDark) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    },

    initSettings() {
      this.applyTheme();

      // Listen for system theme changes if using system theme
      if (this.theme === "system") {
        window
          .matchMedia("(prefers-color-scheme: dark)")
          .addEventListener("change", () => this.applyTheme());
      }
    },
  },
});
