<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="bg-white dark:bg-dark-800 shadow overflow-hidden sm:rounded-lg">
      <div class="px-4 py-5 sm:px-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
          Link External Accounts
        </h3>
        <p class="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
          Connect your AniList and MyAnimeList accounts
        </p>
      </div>
      
      <div class="border-t border-gray-200 dark:border-dark-600 px-4 py-5 sm:p-6">
        <div class="flex flex-col space-y-6">
          <!-- AniList -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              AniList Username
            </label>
            <div class="mt-1 flex rounded-md shadow-sm">
              <span class="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 dark:border-dark-600 bg-gray-50 dark:bg-dark-700 text-gray-500 dark:text-gray-400 sm:text-sm">
                anilist.co/user/
              </span>
              <input
                v-model="formData.anilist_username"
                type="text"
                class="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md border border-gray-300 dark:border-dark-600 dark:bg-dark-700 dark:text-white focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="username"
              />
            </div>
          </div>
          
          <!-- MyAnimeList -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              MyAnimeList Username
            </label>
            <div class="mt-1 flex rounded-md shadow-sm">
              <span class="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 dark:border-dark-600 bg-gray-50 dark:bg-dark-700 text-gray-500 dark:text-gray-400 sm:text-sm">
                myanimelist.net/profile/
              </span>
              <input
                v-model="formData.myanimelist_username"
                type="text"
                class="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md border border-gray-300 dark:border-dark-600 dark:bg-dark-700 dark:text-white focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="username"
              />
            </div>
          </div>
          
          <div class="flex justify-end space-x-3">
            <button
              type="button"
              @click="$router.push('/profile')"
              class="inline-flex justify-center py-2 px-4 border border-gray-300 dark:border-dark-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-700 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="updateAccounts"
              class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              :disabled="loading"
            >
              <span v-if="loading">Updating...</span>
              <span v-else>Save Accounts</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../../stores/auth';
import { useRouter } from 'vue-router';
import axios from 'axios';

const authStore = useAuthStore();
const router = useRouter();
const user = computed(() => authStore.getUser);

const loading = ref(false);
const error = ref(null);
const formData = ref({
  anilist_username: '',
  myanimelist_username: ''
});

onMounted(() => {
  if (user.value) {
    formData.value.anilist_username = user.value.anilist_username || '';
    formData.value.myanimelist_username = user.value.myanimelist_username || '';
  }
});

const updateAccounts = async () => {
  loading.value = true;
  error.value = null;

  try {
    await axios.put('/v1/users/me', {
      anilist_username: formData.value.anilist_username,
      myanimelist_username: formData.value.myanimelist_username
    });
    
    // Refresh user data
    await authStore.fetchUser();
    
    // Navigate back to profile
    router.push('/profile');
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to update linked accounts';
    console.error('Linked accounts update error:', err);
  } finally {
    loading.value = false;
  }
};
</script>