<template>
  <div class="home">
    <div class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">
      <div class="px-4 py-5 sm:p-6">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
          Welcome to Kurobara
        </h1>
        <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
          Black Rose - Your Personal Manga Library
        </p>
        
        <div class="mt-6">
          <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <div v-if="!isAuthenticated" class="col-span-full">
              <div class="bg-primary-50 dark:bg-primary-900 rounded-lg p-6 text-center">
                <h2 class="text-xl font-semibold text-primary-700 dark:text-primary-300">
                  Get Started
                </h2>
                <p class="mt-2 text-primary-600 dark:text-primary-400">
                  Create an account or log in to access your manga library.
                </p>
                <div class="mt-4 flex justify-center space-x-4">
                  <router-link 
                    to="/register" 
                    class="btn btn-primary"
                  >
                    Register
                  </router-link>
                  <router-link 
                    to="/login" 
                    class="btn bg-white dark:bg-dark-700 text-primary-600 dark:text-primary-400 border border-primary-600 dark:border-primary-400 hover:bg-primary-50 dark:hover:bg-dark-600"
                  >
                    Login
                  </router-link>
                </div>
              </div>
            </div>
            
            <div v-else>
              <div class="card">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                  Your Library
                </h2>
                <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  Access your manga collection.
                </p>
                <div class="mt-4">
                  <router-link 
                    to="/library" 
                    class="btn btn-primary"
                  >
                    Go to Library
                  </router-link>
                </div>
              </div>
            </div>
            
            <div>
              <div class="card">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                  Discover Manga
                </h2>
                <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  Search for new manga from various providers.
                </p>
                <div class="mt-4">
                  <router-link 
                    to="/search" 
                    class="btn btn-primary"
                  >
                    Search
                  </router-link>
                </div>
              </div>
            </div>
            
            <div v-if="isAuthenticated">
              <div class="card">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                  Reading Lists
                </h2>
                <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  Organize your manga into custom reading lists.
                </p>
                <div class="mt-4">
                  <router-link 
                    to="/reading-lists" 
                    class="btn btn-primary"
                  >
                    View Lists
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="mt-10">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
            Features
          </h2>
          <ul class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <li v-for="(feature, index) in features" :key="index" class="flex">
              <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-primary-600 dark:text-primary-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p class="ml-3 text-sm text-gray-700 dark:text-gray-300">
                {{ feature }}
              </p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();
const isAuthenticated = computed(() => authStore.isAuthenticated);

const features = [
  'Search for manga/manhua/manhwa from various online providers',
  'Add manga/manhua/manhwa with cover and metadata to your library',
  'Download manga/manhua/manhwa to your library',
  'Read manga/manhua/manhwa directly in the app',
  'Import CBZ or CBR files to your library',
  'User-defined and pre-made categories',
  'Customizable dashboard with pinned categories',
  'NSFW/Explicit content management with blur option',
  'User registration with 2FA',
  'Reading progress tracking and bookmarking',
  'Custom reading lists',
];
</script>
