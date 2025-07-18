import { defineStore } from "pinia";
import axios from "axios";

export const useIntegrationsStore = defineStore("integrations", {
  state: () => ({
    anilistStatus: null,
    malStatus: null,
    kitsuStatus: null,
    loading: false,
    error: null,
    syncInProgress: false,
  }),

  getters: {
    isAnilistConnected: (state) => state.anilistStatus?.is_connected || false,
    isMALConnected: (state) => state.malStatus?.is_connected || false,
    isKitsuConnected: (state) => state.kitsuStatus?.is_connected || false,
    hasAnyConnection: (state) =>
      state.anilistStatus?.is_connected ||
      false ||
      state.malStatus?.is_connected ||
      false ||
      state.kitsuStatus?.is_connected ||
      false,
  },

  actions: {
    async fetchIntegrationSettings() {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.get("/v1/integrations/settings");
        const settings = response.data;

        this.anilistStatus = settings.anilist;
        this.malStatus = settings.myanimelist;
        this.kitsuStatus = settings.kitsu;
      } catch (error) {
        this.error =
          error.response?.data?.detail ||
          "Failed to fetch integration settings";
        console.error("Integration settings fetch error:", error);
      } finally {
        this.loading = false;
      }
    },

    async setupIntegration(integrationType, credentials) {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.post("/v1/integrations/setup", {
          integration_type: integrationType,
          client_id: credentials.client_id,
          client_secret: credentials.client_secret,
        });

        // Refresh settings to get updated status
        await this.fetchIntegrationSettings();

        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail ||
          `Failed to setup ${integrationType} credentials`;
        console.error(`${integrationType} setup error:`, error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async connectAnilist(authCode, redirectUri) {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.post("/v1/integrations/anilist/connect", {
          authorization_code: authCode,
          redirect_uri: redirectUri,
        });

        // Refresh settings to get updated status
        await this.fetchIntegrationSettings();

        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to connect Anilist";
        console.error("Anilist connection error:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async connectMAL(authCode, codeVerifier, redirectUri) {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.post(
          "/v1/integrations/myanimelist/connect",
          {
            authorization_code: authCode,
            code_verifier: codeVerifier,
            redirect_uri: redirectUri,
          },
        );

        // Refresh settings to get updated status
        await this.fetchIntegrationSettings();

        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to connect MyAnimeList";
        console.error("MyAnimeList connection error:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async connectKitsu(credentials) {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.post("/v1/integrations/kitsu/connect", {
          username: credentials.username,
          password: credentials.password,
        });

        // Refresh settings to get updated status
        await this.fetchIntegrationSettings();
        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail || "Failed to connect Kitsu account";
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async updateIntegrationSettings(integrationType, settings) {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.put(
          `/v1/integrations/${integrationType}`,
          settings,
        );

        // Update local state
        if (integrationType === "anilist") {
          this.anilistStatus = { ...this.anilistStatus, ...settings };
        } else if (integrationType === "myanimelist") {
          this.malStatus = { ...this.malStatus, ...settings };
        } else if (integrationType === "kitsu") {
          this.kitsuStatus = { ...this.kitsuStatus, ...settings };
        }

        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail ||
          `Failed to update ${integrationType} settings`;
        console.error(`${integrationType} settings update error:`, error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async disconnectIntegration(integrationType) {
      this.loading = true;
      this.error = null;

      try {
        await axios.delete(`/v1/integrations/${integrationType}`);

        // Update local state
        if (integrationType === "anilist") {
          this.anilistStatus = {
            integration_type: "anilist",
            is_connected: false,
            last_sync_status: "disabled",
            sync_enabled: false,
            auto_sync: false,
            manga_count: 0,
          };
        } else if (integrationType === "myanimelist") {
          this.malStatus = {
            integration_type: "myanimelist",
            is_connected: false,
            last_sync_status: "disabled",
            sync_enabled: false,
            auto_sync: false,
            manga_count: 0,
          };
        }
      } catch (error) {
        this.error =
          error.response?.data?.detail ||
          `Failed to disconnect ${integrationType}`;
        console.error(`${integrationType} disconnection error:`, error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async triggerSync(integrationType, forceFull = false) {
      this.syncInProgress = true;
      this.error = null;

      try {
        const response = await axios.post("/v1/integrations/sync", {
          integration_type: integrationType,
          force_full_sync: forceFull,
          sync_direction: "bidirectional",
        });

        // Update sync status
        if (integrationType === "anilist" && this.anilistStatus) {
          this.anilistStatus.last_sync_status = "in_progress";
        } else if (integrationType === "myanimelist" && this.malStatus) {
          this.malStatus.last_sync_status = "in_progress";
        }

        // Poll for sync completion (optional)
        this.pollSyncStatus(integrationType);

        return response.data;
      } catch (error) {
        this.error =
          error.response?.data?.detail ||
          `Failed to trigger ${integrationType} sync`;
        console.error(`${integrationType} sync error:`, error);
        throw error;
      } finally {
        this.syncInProgress = false;
      }
    },

    async pollSyncStatus(integrationType, maxAttempts = 30) {
      let attempts = 0;

      const poll = async () => {
        if (attempts >= maxAttempts) {
          console.warn(`Sync status polling timeout for ${integrationType}`);
          return;
        }

        try {
          await this.fetchIntegrationSettings();

          const status =
            integrationType === "anilist"
              ? this.anilistStatus?.last_sync_status
              : this.malStatus?.last_sync_status;

          if (status === "in_progress") {
            attempts++;
            setTimeout(poll, 2000); // Poll every 2 seconds
          }
        } catch (error) {
          console.error(
            `Error polling sync status for ${integrationType}:`,
            error,
          );
        }
      };

      poll();
    },

    // OAuth callback handlers
    handleAnilistCallback(authCode, redirectUri) {
      return this.connectAnilist(authCode, redirectUri);
    },

    handleMALCallback(authCode, codeVerifier, redirectUri) {
      return this.connectMAL(authCode, codeVerifier, redirectUri);
    },

    // Utility methods
    clearError() {
      this.error = null;
    },

    reset() {
      this.anilistStatus = null;
      this.malStatus = null;
      this.kitsuStatus = null;
      this.loading = false;
      this.error = null;
      this.syncInProgress = false;
    },

    // Get sync status for display
    getSyncStatusText(integrationType) {
      let status;
      if (integrationType === "anilist") {
        status = this.anilistStatus?.last_sync_status;
      } else if (integrationType === "myanimelist") {
        status = this.malStatus?.last_sync_status;
      } else if (integrationType === "kitsu") {
        status = this.kitsuStatus?.last_sync_status;
      }

      const statusMap = {
        pending: "Pending",
        in_progress: "Syncing...",
        success: "Success",
        failed: "Failed",
        disabled: "Disabled",
      };

      return statusMap[status] || "Unknown";
    },

    getSyncStatusColor(integrationType) {
      let status;
      if (integrationType === "anilist") {
        status = this.anilistStatus?.last_sync_status;
      } else if (integrationType === "myanimelist") {
        status = this.malStatus?.last_sync_status;
      } else if (integrationType === "kitsu") {
        status = this.kitsuStatus?.last_sync_status;
      }

      const colorMap = {
        pending: "text-yellow-600",
        in_progress: "text-blue-600",
        success: "text-green-600",
        failed: "text-red-600",
        disabled: "text-gray-600",
      };

      return colorMap[status] || "text-gray-600";
    },
  },
});
