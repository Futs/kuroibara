<template>
  <div class="integration-settings">
    <!-- Anilist Integration -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-3">
          <div
            class="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center"
          >
            <svg
              class="w-5 h-5 text-white"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                d="M6.361 2.943 0 21.056h4.06l1.077-3.133h6.875l1.077 3.133H17.15L10.79 2.943H6.361zm2.214 5.071 2.262 6.594H6.313l2.262-6.594zM24 12.5c0 6.351-5.149 11.5-11.5 11.5S1 18.851 1 12.5 6.149 1 12.5 1 24 6.149 24 12.5z"
              />
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              Anilist
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Sync your manga list with Anilist
            </p>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <span
            v-if="anilistStatus?.is_connected"
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
          >
            Connected
          </span>
          <span
            v-else
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
          >
            Not Connected
          </span>
        </div>
      </div>

      <div v-if="anilistStatus?.is_connected" class="space-y-4">
        <!-- Connected Status -->
        <div
          class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-green-800 dark:text-green-200">
                Connected as {{ anilistStatus.external_username }}
              </p>
              <p class="text-xs text-green-600 dark:text-green-400">
                {{ anilistStatus.manga_count }} manga synced
                <span v-if="anilistStatus.last_sync_at">
                  • Last sync: {{ formatDate(anilistStatus.last_sync_at) }}
                </span>
              </p>
            </div>
            <button
              @click="disconnectAnilist"
              :disabled="loading"
              class="text-sm text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50"
            >
              Disconnect
            </button>
          </div>
        </div>

        <!-- Sync Settings -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Auto Sync
            </label>
            <input
              type="checkbox"
              v-model="anilistSettings.auto_sync"
              @change="updateAnilistSettings"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
            />
          </div>
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Sync Reading Progress
            </label>
            <input
              type="checkbox"
              v-model="anilistSettings.sync_reading_progress"
              @change="updateAnilistSettings"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
            />
          </div>
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Sync Ratings
            </label>
            <input
              type="checkbox"
              v-model="anilistSettings.sync_ratings"
              @change="updateAnilistSettings"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
            />
          </div>
        </div>

        <!-- Manual Sync Button -->
        <button
          @click="triggerSync('anilist')"
          :disabled="loading || !anilistStatus.sync_enabled"
          class="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading">Syncing...</span>
          <span v-else>Sync Now</span>
        </button>
      </div>

      <div v-else class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Connect your Anilist account to sync your manga list, reading
          progress, and ratings.
        </p>

        <!-- API Credentials Setup -->
        <div
          v-if="!anilistStatus?.client_id"
          class="space-y-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
        >
          <h4 class="text-sm font-medium text-gray-900 dark:text-white">
            API Credentials Required
          </h4>
          <p class="text-xs text-gray-600 dark:text-gray-400">
            Get your credentials from
            <a
              href="https://anilist.co/settings/developer"
              target="_blank"
              class="text-blue-600 hover:text-blue-800"
              >Anilist Developer Settings</a
            >
          </p>

          <div class="space-y-2">
            <label
              class="block text-xs font-medium text-gray-700 dark:text-gray-300"
            >
              Client ID
            </label>
            <input
              v-model="anilistCredentials.client_id"
              type="text"
              placeholder="Enter your Anilist Client ID"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          <div class="space-y-2">
            <label
              class="block text-xs font-medium text-gray-700 dark:text-gray-300"
            >
              Client Secret
            </label>
            <input
              v-model="anilistCredentials.client_secret"
              type="password"
              placeholder="Enter your Anilist Client Secret"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          <button
            @click="setupAnilistCredentials"
            :disabled="
              loading ||
              !anilistCredentials.client_id ||
              !anilistCredentials.client_secret
            "
            class="w-full bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            <span v-if="loading">Setting up...</span>
            <span v-else>Save Credentials</span>
          </button>
        </div>

        <button
          @click="connectAnilist"
          :disabled="loading || !canConnectAnilist"
          class="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading">Connecting...</span>
          <span v-else>Connect Anilist</span>
        </button>

        <p
          v-if="!canConnectAnilist"
          class="text-xs text-gray-500 dark:text-gray-400"
        >
          Please set up your API credentials first or configure them in
          environment variables.
        </p>
      </div>
    </div>

    <!-- MyAnimeList Integration -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-3">
          <div
            class="w-8 h-8 bg-blue-700 rounded-lg flex items-center justify-center"
          >
            <svg
              class="w-5 h-5 text-white"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                d="M8.273 7.247v8.423l1.624-.323v-5.65h2.411v5.65l1.624.323V7.247H8.273zm6.15 0v8.423l1.624-.323v-5.65h2.411v5.65l1.624.323V7.247h-5.659z"
              />
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              MyAnimeList
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Sync your manga list with MyAnimeList
            </p>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <span
            v-if="malStatus?.is_connected"
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
          >
            Connected
          </span>
          <span
            v-else
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
          >
            Not Connected
          </span>
        </div>
      </div>

      <div v-if="malStatus?.is_connected" class="space-y-4">
        <!-- Connected Status -->
        <div
          class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-green-800 dark:text-green-200">
                Connected as {{ malStatus.external_username }}
              </p>
              <p class="text-xs text-green-600 dark:text-green-400">
                {{ malStatus.manga_count }} manga synced
                <span v-if="malStatus.last_sync_at">
                  • Last sync: {{ formatDate(malStatus.last_sync_at) }}
                </span>
              </p>
            </div>
            <button
              @click="disconnectMAL"
              :disabled="loading"
              class="text-sm text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50"
            >
              Disconnect
            </button>
          </div>
        </div>

        <!-- Sync Settings -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Auto Sync
            </label>
            <input
              type="checkbox"
              v-model="malSettings.auto_sync"
              @change="updateMALSettings"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
            />
          </div>
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Sync Reading Progress
            </label>
            <input
              type="checkbox"
              v-model="malSettings.sync_reading_progress"
              @change="updateMALSettings"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
            />
          </div>
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Sync Ratings
            </label>
            <input
              type="checkbox"
              v-model="malSettings.sync_ratings"
              @change="updateMALSettings"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
            />
          </div>
        </div>

        <!-- Manual Sync Button -->
        <button
          @click="triggerSync('myanimelist')"
          :disabled="loading || !malStatus.sync_enabled"
          class="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading">Syncing...</span>
          <span v-else>Sync Now</span>
        </button>
      </div>

      <div v-else class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Connect your MyAnimeList account to sync your manga list, reading
          progress, and ratings.
        </p>

        <!-- API Credentials Setup -->
        <div
          v-if="!malStatus?.client_id"
          class="space-y-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
        >
          <h4 class="text-sm font-medium text-gray-900 dark:text-white">
            API Credentials Required
          </h4>
          <p class="text-xs text-gray-600 dark:text-gray-400">
            Get your credentials from
            <a
              href="https://myanimelist.net/apiconfig"
              target="_blank"
              class="text-blue-600 hover:text-blue-800"
              >MyAnimeList API Config</a
            >
          </p>

          <div class="space-y-2">
            <label
              class="block text-xs font-medium text-gray-700 dark:text-gray-300"
            >
              Client ID
            </label>
            <input
              v-model="malCredentials.client_id"
              type="text"
              placeholder="Enter your MyAnimeList Client ID"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          <div class="space-y-2">
            <label
              class="block text-xs font-medium text-gray-700 dark:text-gray-300"
            >
              Client Secret
            </label>
            <input
              v-model="malCredentials.client_secret"
              type="password"
              placeholder="Enter your MyAnimeList Client Secret"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          <button
            @click="setupMALCredentials"
            :disabled="
              loading ||
              !malCredentials.client_id ||
              !malCredentials.client_secret
            "
            class="w-full bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            <span v-if="loading">Setting up...</span>
            <span v-else>Save Credentials</span>
          </button>
        </div>

        <button
          @click="connectMAL"
          :disabled="loading || !canConnectMAL"
          class="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading">Connecting...</span>
          <span v-else>Connect MyAnimeList</span>
        </button>

        <p
          v-if="!canConnectMAL"
          class="text-xs text-gray-500 dark:text-gray-400"
        >
          Please set up your API credentials first or configure them in
          environment variables.
        </p>
      </div>
    </div>

    <!-- Kitsu Integration -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-3">
          <div
            class="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center"
          >
            <svg
              class="w-5 h-5 text-white"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.568 8.16c-.169-.331-.423-.586-.754-.755l-3.981-2.016c-.331-.169-.724-.169-1.055 0L7.797 7.405c-.331.169-.585.424-.754.755-.169.331-.169.724 0 1.055l2.016 3.981c.169.331.423.586.754.755l3.981 2.016c.331.169.724.169 1.055 0l3.981-2.016c.331-.169.585-.424.754-.755.169-.331.169-.724 0-1.055l-2.016-3.981z"
              />
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              Kitsu
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Sync your manga list with Kitsu
            </p>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <span
            v-if="kitsuStatus?.is_connected"
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
          >
            Connected
          </span>
          <span
            v-else
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
          >
            Not Connected
          </span>
        </div>
      </div>

      <div v-if="kitsuStatus?.is_connected" class="space-y-4">
        <!-- Connected Status -->
        <div
          class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-green-800 dark:text-green-200">
                Connected as {{ kitsuStatus.external_username }}
              </p>
              <p class="text-xs text-green-600 dark:text-green-400">
                {{ kitsuStatus.manga_count }} manga synced
                <span v-if="kitsuStatus.last_sync_at">
                  • Last sync: {{ formatDate(kitsuStatus.last_sync_at) }}
                </span>
              </p>
            </div>
            <button
              @click="disconnectKitsu"
              class="text-xs text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
            >
              Disconnect
            </button>
          </div>
        </div>

        <!-- Sync Settings -->
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">
            Sync Settings
          </h4>
          <div class="space-y-3">
            <label class="flex items-center">
              <input
                v-model="kitsuSettings.auto_sync"
                type="checkbox"
                class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Auto-sync on changes
              </span>
            </label>
            <label class="flex items-center">
              <input
                v-model="kitsuSettings.sync_reading_progress"
                type="checkbox"
                class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Sync reading progress
              </span>
            </label>
            <label class="flex items-center">
              <input
                v-model="kitsuSettings.sync_ratings"
                type="checkbox"
                class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Sync ratings
              </span>
            </label>
          </div>
        </div>

        <!-- Manual Sync Button -->
        <button
          @click="triggerSync('kitsu')"
          :disabled="loading || !kitsuStatus.sync_enabled"
          class="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading">Syncing...</span>
          <span v-else>Sync Now</span>
        </button>
      </div>

      <div v-else class="space-y-4">
        <!-- Setup Instructions -->
        <div
          class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4"
        >
          <h4 class="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
            Connect your Kitsu account
          </h4>
          <p class="text-xs text-blue-600 dark:text-blue-400 mb-3">
            Enter your Kitsu username and password to connect your account.
          </p>
        </div>

        <!-- Credentials Form -->
        <div class="space-y-4">
          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Username
            </label>
            <input
              v-model="kitsuCredentials.username"
              type="text"
              placeholder="Your Kitsu username"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Password
            </label>
            <input
              v-model="kitsuCredentials.password"
              type="password"
              placeholder="Your Kitsu password"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>

        <!-- Connect Button -->
        <button
          @click="connectKitsu"
          :disabled="loading || !canConnectKitsu"
          class="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading">Connecting...</span>
          <span v-else>Connect Kitsu</span>
        </button>
      </div>
    </div>

    <!-- Error Display -->
    <div
      v-if="error"
      class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
    >
      <p class="text-sm text-red-800 dark:text-red-200">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useIntegrationsStore } from "../stores/integrations";

const integrationsStore = useIntegrationsStore();

// Local state
const loading = ref(false);
const error = ref(null);

// Computed properties
const anilistStatus = computed(() => integrationsStore.anilistStatus);
const malStatus = computed(() => integrationsStore.malStatus);
const kitsuStatus = computed(() => integrationsStore.kitsuStatus);

const anilistSettings = ref({
  auto_sync: true,
  sync_reading_progress: true,
  sync_ratings: true,
});

const malSettings = ref({
  auto_sync: true,
  sync_reading_progress: true,
  sync_ratings: true,
});

const kitsuSettings = ref({
  auto_sync: true,
  sync_reading_progress: true,
  sync_ratings: true,
});

const anilistCredentials = ref({
  client_id: "",
  client_secret: "",
});

const kitsuCredentials = ref({
  username: "",
  password: "",
});

const malCredentials = ref({
  client_id: "",
  client_secret: "",
});

// Computed properties for connection availability
const canConnectAnilist = computed(() => {
  return (
    anilistStatus.value?.client_id ||
    anilistCredentials.value.client_id ||
    import.meta.env.VITE_ANILIST_CLIENT_ID
  );
});

const canConnectMAL = computed(() => {
  return (
    malStatus.value?.client_id ||
    malCredentials.value.client_id ||
    import.meta.env.VITE_MAL_CLIENT_ID
  );
});

const canConnectKitsu = computed(() => {
  return kitsuCredentials.value.username && kitsuCredentials.value.password;
});

// Methods
const setupAnilistCredentials = async () => {
  loading.value = true;
  error.value = null;

  try {
    await integrationsStore.setupIntegration("anilist", {
      client_id: anilistCredentials.value.client_id,
      client_secret: anilistCredentials.value.client_secret,
    });

    // Clear the form
    anilistCredentials.value = { client_id: "", client_secret: "" };

    // Refresh settings
    await integrationsStore.fetchIntegrationSettings();
  } catch (err) {
    error.value = err.message || "Failed to setup Anilist credentials";
  } finally {
    loading.value = false;
  }
};

const setupMALCredentials = async () => {
  loading.value = true;
  error.value = null;

  try {
    await integrationsStore.setupIntegration("myanimelist", {
      client_id: malCredentials.value.client_id,
      client_secret: malCredentials.value.client_secret,
    });

    // Clear the form
    malCredentials.value = { client_id: "", client_secret: "" };

    // Refresh settings
    await integrationsStore.fetchIntegrationSettings();
  } catch (err) {
    error.value = err.message || "Failed to setup MyAnimeList credentials";
  } finally {
    loading.value = false;
  }
};

const connectAnilist = async () => {
  loading.value = true;
  error.value = null;

  try {
    // Get client ID from various sources
    const clientId =
      anilistStatus.value?.client_id ||
      anilistCredentials.value.client_id ||
      import.meta.env.VITE_ANILIST_CLIENT_ID;

    if (!clientId) {
      throw new Error(
        "Anilist client ID not configured. Please set up your API credentials first.",
      );
    }

    const redirectUri = `${window.location.origin}/integrations/anilist/callback`;
    const authUrl = `https://anilist.co/api/v2/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code`;

    // Open OAuth flow in a popup
    const popup = window.open(
      authUrl,
      "anilist-auth",
      "width=600,height=700,scrollbars=yes,resizable=yes",
    );

    // Listen for messages from the popup
    const messageHandler = (event) => {
      if (event.origin !== window.location.origin) return;

      if (event.data.type === "ANILIST_AUTH_SUCCESS") {
        window.removeEventListener("message", messageHandler);
        loading.value = false;
        // Refresh integration settings
        integrationsStore.fetchIntegrationSettings();
      } else if (event.data.type === "ANILIST_AUTH_ERROR") {
        window.removeEventListener("message", messageHandler);
        error.value = event.data.data.error;
        loading.value = false;
      }
    };

    window.addEventListener("message", messageHandler);

    // Handle popup being closed manually
    const checkClosed = setInterval(() => {
      if (popup.closed) {
        clearInterval(checkClosed);
        window.removeEventListener("message", messageHandler);
        loading.value = false;
      }
    }, 1000);
  } catch (err) {
    error.value = err.message || "Failed to connect Anilist";
    loading.value = false;
  }
};

const connectMAL = async () => {
  loading.value = true;
  error.value = null;

  try {
    // Get client ID from various sources
    const clientId =
      malStatus.value?.client_id ||
      malCredentials.value.client_id ||
      import.meta.env.VITE_MAL_CLIENT_ID;

    if (!clientId) {
      throw new Error(
        "MyAnimeList client ID not configured. Please set up your API credentials first.",
      );
    }

    const redirectUri = `${window.location.origin}/integrations/mal/callback`;
    const authUrl = `https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&code_challenge=challenge&code_challenge_method=plain`;

    // Open OAuth flow in a popup
    const popup = window.open(
      authUrl,
      "mal-auth",
      "width=600,height=700,scrollbars=yes,resizable=yes",
    );

    // Listen for messages from the popup
    const messageHandler = (event) => {
      if (event.origin !== window.location.origin) return;

      if (event.data.type === "MAL_AUTH_SUCCESS") {
        window.removeEventListener("message", messageHandler);
        loading.value = false;
        // Refresh integration settings
        integrationsStore.fetchIntegrationSettings();
      } else if (event.data.type === "MAL_AUTH_ERROR") {
        window.removeEventListener("message", messageHandler);
        error.value = event.data.data.error;
        loading.value = false;
      }
    };

    window.addEventListener("message", messageHandler);

    // Handle popup being closed manually
    const checkClosed = setInterval(() => {
      if (popup.closed) {
        clearInterval(checkClosed);
        window.removeEventListener("message", messageHandler);
        loading.value = false;
      }
    }, 1000);
  } catch (err) {
    error.value = err.message || "Failed to connect MyAnimeList";
    loading.value = false;
  }
};

const disconnectAnilist = async () => {
  loading.value = true;
  error.value = null;

  try {
    await integrationsStore.disconnectIntegration("anilist");
  } catch (err) {
    error.value = err.message || "Failed to disconnect Anilist";
  } finally {
    loading.value = false;
  }
};

const disconnectMAL = async () => {
  loading.value = true;
  error.value = null;

  try {
    await integrationsStore.disconnectIntegration("myanimelist");
  } catch (err) {
    error.value = err.message || "Failed to disconnect MyAnimeList";
  } finally {
    loading.value = false;
  }
};

const connectKitsu = async () => {
  loading.value = true;
  error.value = null;

  try {
    await integrationsStore.connectKitsu({
      username: kitsuCredentials.value.username,
      password: kitsuCredentials.value.password,
    });

    // Clear credentials after successful connection
    kitsuCredentials.value.username = "";
    kitsuCredentials.value.password = "";
  } catch (err) {
    error.value = err.message || "Failed to connect Kitsu";
  } finally {
    loading.value = false;
  }
};

const disconnectKitsu = async () => {
  loading.value = true;
  error.value = null;

  try {
    await integrationsStore.disconnectIntegration("kitsu");
  } catch (err) {
    error.value = err.message || "Failed to disconnect Kitsu";
  } finally {
    loading.value = false;
  }
};

const updateAnilistSettings = async () => {
  try {
    await integrationsStore.updateIntegrationSettings(
      "anilist",
      anilistSettings.value,
    );
  } catch (err) {
    error.value = err.message || "Failed to update Anilist settings";
  }
};

const updateMALSettings = async () => {
  try {
    await integrationsStore.updateIntegrationSettings(
      "myanimelist",
      malSettings.value,
    );
  } catch (err) {
    error.value = err.message || "Failed to update MyAnimeList settings";
  }
};

const triggerSync = async (integrationType) => {
  loading.value = true;
  error.value = null;

  try {
    await integrationsStore.triggerSync(integrationType);
  } catch (err) {
    error.value = err.message || "Failed to trigger sync";
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return "Never";
  return new Date(dateString).toLocaleDateString();
};

// Lifecycle
onMounted(async () => {
  try {
    await integrationsStore.fetchIntegrationSettings();

    // Update local settings from store
    if (anilistStatus.value?.is_connected) {
      anilistSettings.value = {
        auto_sync: anilistStatus.value.auto_sync,
        sync_reading_progress:
          anilistStatus.value.sync_reading_progress || true,
        sync_ratings: anilistStatus.value.sync_ratings || true,
      };
    }

    if (malStatus.value?.is_connected) {
      malSettings.value = {
        auto_sync: malStatus.value.auto_sync,
        sync_reading_progress: malStatus.value.sync_reading_progress || true,
        sync_ratings: malStatus.value.sync_ratings || true,
      };
    }
  } catch (err) {
    error.value = err.message || "Failed to load integration settings";
  }
});
</script>
