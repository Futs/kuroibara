<template>
  <div
    class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900"
  >
    <div class="max-w-md w-full space-y-8">
      <div class="text-center">
        <div v-if="loading" class="space-y-4">
          <div
            class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"
          ></div>
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
            Connecting to Anilist...
          </h2>
          <p class="text-gray-600 dark:text-gray-400">
            Please wait while we complete the connection.
          </p>
        </div>

        <div v-else-if="success" class="space-y-4">
          <div
            class="rounded-full h-12 w-12 bg-green-100 dark:bg-green-900 mx-auto flex items-center justify-center"
          >
            <svg
              class="h-6 w-6 text-green-600 dark:text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              ></path>
            </svg>
          </div>
          <h2 class="text-xl font-semibold text-green-900 dark:text-green-100">
            Successfully Connected!
          </h2>
          <p class="text-gray-600 dark:text-gray-400">
            Your Anilist account has been connected. You can close this window.
          </p>
        </div>

        <div v-else-if="error" class="space-y-4">
          <div
            class="rounded-full h-12 w-12 bg-red-100 dark:bg-red-900 mx-auto flex items-center justify-center"
          >
            <svg
              class="h-6 w-6 text-red-600 dark:text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              ></path>
            </svg>
          </div>
          <h2 class="text-xl font-semibold text-red-900 dark:text-red-100">
            Connection Failed
          </h2>
          <p class="text-gray-600 dark:text-gray-400">
            {{ error }}
          </p>
          <button
            @click="retry"
            class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useIntegrationsStore } from "../../stores/integrations";

const route = useRoute();
const integrationsStore = useIntegrationsStore();

const loading = ref(true);
const success = ref(false);
const error = ref(null);

const handleCallback = async () => {
  try {
    loading.value = true;
    error.value = null;

    // Get authorization code from URL params
    const authCode = route.query.code;
    const state = route.query.state;
    const errorParam = route.query.error;

    if (errorParam) {
      throw new Error(`OAuth error: ${errorParam}`);
    }

    if (!authCode) {
      throw new Error("No authorization code received");
    }

    // Get redirect URI (should match what was sent in the initial request)
    const redirectUri = `${window.location.origin}/integrations/anilist/callback`;

    // Connect the account
    await integrationsStore.connectAnilist(authCode, redirectUri);

    success.value = true;

    // Notify parent window if this is a popup
    if (window.opener) {
      window.opener.postMessage(
        {
          type: "ANILIST_AUTH_SUCCESS",
          data: { success: true },
        },
        window.location.origin,
      );

      // Close popup after a short delay
      setTimeout(() => {
        window.close();
      }, 2000);
    }
  } catch (err) {
    console.error("Anilist callback error:", err);
    error.value = err.message || "Failed to connect Anilist account";

    // Notify parent window of error if this is a popup
    if (window.opener) {
      window.opener.postMessage(
        {
          type: "ANILIST_AUTH_ERROR",
          data: { error: error.value },
        },
        window.location.origin,
      );
    }
  } finally {
    loading.value = false;
  }
};

const retry = () => {
  // Close this window and let user try again from main app
  if (window.opener) {
    window.close();
  } else {
    // If not a popup, redirect to settings
    window.location.href = "/settings";
  }
};

onMounted(() => {
  handleCallback();
});
</script>
