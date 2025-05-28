<script setup>
import { onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useSettingsStore } from './stores/settings';
import { useAuthStore } from './stores/auth';

const route = useRoute();
const settingsStore = useSettingsStore();
const authStore = useAuthStore();

// Apply theme on route change
watch(() => route.path, () => {
  settingsStore.applyTheme();
});

onMounted(() => {
  // Initialize settings
  settingsStore.initSettings();

  // Initialize auth
  authStore.initAuth();
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
