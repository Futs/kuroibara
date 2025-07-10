<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="bg-white dark:bg-dark-800 shadow overflow-hidden sm:rounded-lg">
      <div class="px-4 py-5 sm:px-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
          Edit Profile Picture
        </h3>
        <p class="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
          Update your profile picture
        </p>
      </div>
      
      <div class="border-t border-gray-200 dark:border-dark-600 px-4 py-5 sm:p-6">
        <div class="flex flex-col space-y-6">
          <div class="flex items-center space-x-4">
            <img 
              v-if="user?.avatar" 
              :src="user.avatar" 
              alt="Current avatar" 
              class="h-20 w-20 rounded-full object-cover"
            />
            <div v-else class="h-20 w-20 rounded-full bg-primary-500 flex items-center justify-center text-white text-xl">
              {{ userInitials }}
            </div>
            <div>
              <p class="text-sm text-gray-500 dark:text-gray-400">Current profile picture</p>
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              New Profile Picture URL
            </label>
            <input
              v-model="formData.avatar"
              type="text"
              class="mt-1 block w-full border border-gray-300 dark:border-dark-600 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm"
              placeholder="https://example.com/avatar.jpg"
            />
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
              @click="updateAvatar"
              class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              :disabled="loading"
            >
              <span v-if="loading">Updating...</span>
              <span v-else>Update Profile Picture</span>
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
import api from '../../services/api.js';

const authStore = useAuthStore();
const router = useRouter();
const user = computed(() => authStore.getUser);
const userInitials = computed(() => {
  if (!user.value?.username) return '';
  return user.value.username.charAt(0).toUpperCase();
});

const loading = ref(false);
const error = ref(null);
const formData = ref({
  avatar: ''
});

onMounted(() => {
  if (user.value?.avatar) {
    formData.value.avatar = user.value.avatar;
  }
});

const updateAvatar = async () => {
  loading.value = true;
  error.value = null;

  try {
    await api.put('/v1/users/me', {
      avatar: formData.value.avatar
    });
    
    // Refresh user data
    await authStore.fetchUser();
    
    // Navigate back to profile
    router.push('/profile');
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to update profile picture';
    console.error('Profile picture update error:', err);
  } finally {
    loading.value = false;
  }
};
</script>