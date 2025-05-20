<template>
  <div class="search-result-card">
    <div class="relative group">
      <div class="aspect-w-2 aspect-h-3 rounded-lg overflow-hidden bg-gray-200 dark:bg-dark-700">
        <img 
          v-if="manga.cover_url" 
          :src="manga.cover_url" 
          :alt="manga.title" 
          class="w-full h-full object-center object-cover"
          :class="{ 'blur-sm': isNsfw && blurNsfw }"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-500">
          <svg class="h-12 w-12" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        
        <!-- NSFW Badge -->
        <div v-if="isNsfw" class="absolute top-2 right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded">
          NSFW
        </div>
        
        <!-- Provider Badge -->
        <div v-if="manga.provider" class="absolute top-2 left-2 bg-gray-800 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
          {{ manga.provider }}
        </div>
        
        <!-- Status Badge -->
        <div v-if="manga.status" class="absolute bottom-2 left-2 bg-gray-800 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
          {{ formatStatus(manga.status) }}
        </div>
        
        <!-- Hover Actions -->
        <div class="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
          <button 
            @click="viewDetails" 
            class="p-2 bg-white dark:bg-dark-800 rounded-full text-gray-700 dark:text-gray-200 hover:text-primary-600 dark:hover:text-primary-400"
            title="View Details"
          >
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
          
          <button 
            @click="addToLibrary" 
            :disabled="inLibrary || adding"
            class="p-2 bg-white dark:bg-dark-800 rounded-full text-gray-700 dark:text-gray-200 hover:text-primary-600 dark:hover:text-primary-400 disabled:opacity-50 disabled:cursor-not-allowed"
            :title="inLibrary ? 'Already in Library' : 'Add to Library'"
          >
            <svg v-if="adding" class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else-if="inLibrary" class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </button>
        </div>
      </div>
      
      <div class="mt-2">
        <h3 class="text-sm font-medium text-gray-900 dark:text-white truncate" :title="manga.title">
          {{ manga.title }}
        </h3>
        <p v-if="manga.author" class="text-xs text-gray-500 dark:text-gray-400 truncate">
          {{ manga.author }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useSettingsStore } from '../stores/settings';
import axios from 'axios';

const props = defineProps({
  manga: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['add-to-library']);
const router = useRouter();
const settingsStore = useSettingsStore();

const adding = ref(false);
const inLibrary = ref(props.manga.in_library || false);

const isNsfw = computed(() => props.manga.is_nsfw || props.manga.is_explicit);
const blurNsfw = computed(() => settingsStore.getNsfwBlur);

const viewDetails = () => {
  router.push(`/manga/${props.manga.id}`);
};

const addToLibrary = async () => {
  if (inLibrary.value || adding.value) return;
  
  adding.value = true;
  
  try {
    await emit('add-to-library', props.manga.id);
    inLibrary.value = true;
  } catch (error) {
    console.error('Failed to add to library:', error);
  } finally {
    adding.value = false;
  }
};

const formatStatus = (status) => {
  if (!status) return '';
  
  // Capitalize first letter
  return status.charAt(0).toUpperCase() + status.slice(1);
};
</script>
