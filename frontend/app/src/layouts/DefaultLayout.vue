<template>
  <div class="min-h-screen flex flex-col bg-gray-50 dark:bg-dark-900">
    <header class="bg-white dark:bg-dark-800 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <router-link to="/" class="flex items-center space-x-3">
                <img
                  src="/assets/logo/logo.png"
                  alt="Kuroibara Logo"
                  class="h-8 w-8"
                />
                <img src="/assets/logo/name.png" alt="Kuroibara" class="h-6" />
              </router-link>
            </div>
            <nav class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <router-link
                v-for="item in navItems"
                :key="item.name"
                :to="item.to"
                :class="[
                  $route.path === item.to ||
                  $route.path.startsWith(item.to + '/')
                    ? 'border-primary-500 text-gray-900 dark:text-white'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white',
                  'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium',
                ]"
              >
                {{ item.name }}
              </router-link>
            </nav>
          </div>
          <div class="hidden sm:ml-6 sm:flex sm:items-center">
            <div class="ml-3 relative user-menu">
              <div v-if="isAuthenticated">
                <button
                  @click="userMenuOpen = !userMenuOpen"
                  class="flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <span class="sr-only">Open user menu</span>
                  <img
                    v-if="user?.avatar"
                    :src="user.avatar"
                    :alt="user.username"
                    class="h-8 w-8 rounded-full object-cover"
                  />
                  <div
                    v-else
                    class="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center text-white"
                  >
                    {{ userInitials }}
                  </div>
                </button>
                <div
                  v-if="userMenuOpen"
                  class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white dark:bg-dark-700 ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
                >
                  <router-link
                    to="/profile"
                    class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-600"
                    @click="userMenuOpen = false"
                  >
                    Your Profile
                  </router-link>
                  <router-link
                    to="/settings"
                    class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-600"
                    @click="userMenuOpen = false"
                  >
                    Settings
                  </router-link>
                  <router-link
                    to="/recovery"
                    class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-600"
                    @click="userMenuOpen = false"
                  >
                    Storage Recovery
                  </router-link>
                  <router-link
                    to="/backup"
                    class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-600"
                    @click="userMenuOpen = false"
                  >
                    Backup & Restore
                  </router-link>
                  <button
                    @click="logout"
                    class="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-600"
                  >
                    Sign out
                  </button>
                </div>
              </div>
              <div v-else class="flex space-x-4">
                <router-link
                  to="/login"
                  class="text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                >
                  Login
                </router-link>
                <router-link
                  to="/register"
                  class="bg-primary-600 text-white hover:bg-primary-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Register
                </router-link>
              </div>
            </div>
          </div>
          <div class="-mr-2 flex items-center sm:hidden">
            <button
              @click="mobileMenuOpen = !mobileMenuOpen"
              class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
            >
              <span class="sr-only">Open main menu</span>
              <svg
                class="h-6 w-6"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  v-if="!mobileMenuOpen"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
                <path
                  v-else
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div v-if="mobileMenuOpen" class="sm:hidden">
        <div class="pt-2 pb-3 space-y-1">
          <router-link
            v-for="item in navItems"
            :key="item.name"
            :to="item.to"
            :class="[
              $route.path === item.to || $route.path.startsWith(item.to + '/')
                ? 'bg-primary-50 dark:bg-primary-900 border-primary-500 text-primary-700 dark:text-primary-300'
                : 'border-transparent text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-700 hover:border-gray-300 hover:text-gray-800',
              'block pl-3 pr-4 py-2 border-l-4 text-base font-medium',
            ]"
            @click="mobileMenuOpen = false"
          >
            {{ item.name }}
          </router-link>
        </div>
        <div
          v-if="isAuthenticated"
          class="pt-4 pb-3 border-t border-gray-200 dark:border-dark-600"
        >
          <div class="flex items-center px-4">
            <div class="flex-shrink-0">
              <img
                v-if="user?.avatar"
                :src="user.avatar"
                :alt="user.username"
                class="h-10 w-10 rounded-full object-cover"
              />
              <div
                v-else
                class="h-10 w-10 rounded-full bg-primary-500 flex items-center justify-center text-white"
              >
                {{ userInitials }}
              </div>
            </div>
            <div class="ml-3">
              <div class="text-base font-medium text-gray-800 dark:text-white">
                {{ user?.username }}
              </div>
              <div class="text-sm font-medium text-gray-500 dark:text-gray-400">
                {{ user?.email }}
              </div>
            </div>
          </div>
          <div class="mt-3 space-y-1">
            <router-link
              to="/profile"
              class="block px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 hover:bg-gray-100 dark:hover:bg-dark-700"
              @click="mobileMenuOpen = false"
            >
              Your Profile
            </router-link>
            <router-link
              to="/profile/edit"
              class="block px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 hover:bg-gray-100 dark:hover:bg-dark-700"
              @click="mobileMenuOpen = false"
            >
              Edit Profile Picture
            </router-link>
            <router-link
              to="/profile/accounts"
              class="block px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 hover:bg-gray-100 dark:hover:bg-dark-700"
              @click="mobileMenuOpen = false"
            >
              Link External Accounts
            </router-link>
            <router-link
              to="/settings"
              class="block px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 hover:bg-gray-100 dark:hover:bg-dark-700"
              @click="mobileMenuOpen = false"
            >
              Settings
            </router-link>
            <router-link
              to="/recovery"
              class="block px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 hover:bg-gray-100 dark:hover:bg-dark-700"
              @click="mobileMenuOpen = false"
            >
              Storage Recovery
            </router-link>
            <router-link
              to="/backup"
              class="block px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 hover:bg-gray-100 dark:hover:bg-dark-700"
              @click="mobileMenuOpen = false"
            >
              Backup & Restore
            </router-link>
            <button
              @click="logout"
              class="block w-full text-left px-4 py-2 text-base font-medium text-gray-500 dark:text-gray-300 hover:text-gray-800 hover:bg-gray-100 dark:hover:bg-dark-700"
            >
              Sign out
            </button>
          </div>
        </div>
        <div
          v-else
          class="pt-4 pb-3 border-t border-gray-200 dark:border-dark-600"
        >
          <div class="flex items-center justify-around">
            <router-link
              to="/login"
              class="text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white px-3 py-2 rounded-md text-base font-medium"
              @click="mobileMenuOpen = false"
            >
              Login
            </router-link>
            <router-link
              to="/register"
              class="bg-primary-600 text-white hover:bg-primary-700 px-3 py-2 rounded-md text-base font-medium"
              @click="mobileMenuOpen = false"
            >
              Register
            </router-link>
          </div>
        </div>
      </div>
    </header>

    <main class="flex-grow">
      <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <router-view />
      </div>
    </main>

    <footer class="bg-white dark:bg-dark-800 shadow-sm">
      <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
        <div class="text-center text-sm text-gray-500 dark:text-gray-400">
          <p>
            &copy; {{ new Date().getFullYear() }} Kuroibara. All rights
            reserved.
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useSettingsStore } from "../stores/settings";

const router = useRouter();
const authStore = useAuthStore();
const settingsStore = useSettingsStore();

const mobileMenuOpen = ref(false);
const userMenuOpen = ref(false);

const isAuthenticated = computed(() => authStore.isAuthenticated);
const user = computed(() => authStore.getUser);

const userInitials = computed(() => {
  if (!user.value) return "";
  return user.value.username.substring(0, 2).toUpperCase();
});

const navItems = computed(() => {
  const items = [
    { name: "Home", to: "/" },
    { name: "Search", to: "/search" },
  ];

  if (isAuthenticated.value) {
    items.push(
      { name: "Library", to: "/library" },
      { name: "Categories", to: "/categories" },
      { name: "Reading Lists", to: "/reading-lists" },
    );
  }

  return items;
});

const logout = () => {
  authStore.logout();
  userMenuOpen.value = false;
  mobileMenuOpen.value = false;
};

onMounted(() => {
  // Initialize settings (auth is already initialized in App.vue)
  settingsStore.initSettings();

  // Close menus when clicking outside
  document.addEventListener("click", (event) => {
    if (userMenuOpen.value && !event.target.closest(".user-menu")) {
      userMenuOpen.value = false;
    }
  });
});
</script>
