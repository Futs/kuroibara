<script setup>
import { onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { useSettingsStore } from "./stores/settings";
import { useAuthStore } from "./stores/auth";
import { useDownloadsStore } from "./stores/downloads";

const route = useRoute();
const settingsStore = useSettingsStore();
const authStore = useAuthStore();
const downloadsStore = useDownloadsStore();

// Apply theme on route change
watch(
  () => route.path,
  () => {
    settingsStore.applyTheme();
  },
);

onMounted(async () => {
  console.log("App.vue: Starting initialization...");

  // Initialize settings first
  settingsStore.initSettings();
  console.log("App.vue: Settings initialized");

  // Initialize auth
  authStore.initAuth();
  console.log("App.vue: Auth initialized");

  // Initialize downloads store if authenticated
  if (authStore.isAuthenticated) {
    downloadsStore.init();
    console.log("App.vue: Downloads store initialized");
  }
});
</script>

<template>
  <router-view />
</template>

<style>
/* Global styles */
html {
  scroll-behavior: smooth;
}

/* Dark mode transition */
.dark {
  color-scheme: dark;
}

/* Transition effects */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
