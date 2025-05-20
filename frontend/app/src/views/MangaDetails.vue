<template>
  <div class="manga-details">
    <div v-if="loading" class="flex justify-center items-center py-12">
      <svg class="animate-spin h-10 w-10 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>
    
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900 p-4 rounded-md">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400 dark:text-red-300" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
            {{ error }}
          </h3>
          <div class="mt-2 text-sm text-red-700 dark:text-red-300">
            <button 
              @click="fetchMangaDetails" 
              class="font-medium underline hover:text-red-600 dark:hover:text-red-400"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else-if="manga" class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">
      <!-- Manga Header -->
      <div class="relative">
        <div class="h-48 sm:h-64 w-full bg-gray-200 dark:bg-dark-700">
          <img 
            v-if="manga.banner_url" 
            :src="manga.banner_url" 
            :alt="manga.title" 
            class="w-full h-full object-cover"
          />
        </div>
        
        <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4">
          <h1 class="text-2xl sm:text-3xl font-bold text-white">
            {{ manga.title }}
          </h1>
          <p v-if="manga.alternative_titles && manga.alternative_titles.length" class="text-sm text-gray-300 mt-1">
            {{ manga.alternative_titles.join(' / ') }}
          </p>
        </div>
      </div>
      
      <!-- Manga Content -->
      <div class="p-4 sm:p-6">
        <div class="flex flex-col md:flex-row gap-6">
          <!-- Left Column - Cover and Actions -->
          <div class="w-full md:w-1/3 lg:w-1/4">
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
            </div>
            
            <div class="mt-4 space-y-3">
              <button 
                v-if="inLibrary" 
                @click="removeFromLibrary" 
                class="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <svg class="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Remove from Library
              </button>
              
              <button 
                v-else 
                @click="addToLibrary" 
                class="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg class="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add to Library
              </button>
              
              <button 
                v-if="manga.chapters && manga.chapters.length > 0"
                @click="startReading" 
                class="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-secondary-600 hover:bg-secondary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500"
              >
                <svg class="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                Start Reading
              </button>
              
              <button 
                v-if="manga.chapters && manga.chapters.length > 0"
                @click="downloadManga" 
                class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg class="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download
              </button>
            </div>
          </div>
          
          <!-- Right Column - Details and Chapters -->
          <div class="w-full md:w-2/3 lg:w-3/4">
            <!-- Manga Info -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div v-if="manga.author" class="flex items-center">
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24">Author:</span>
                <span class="text-sm text-gray-900 dark:text-white">{{ manga.author }}</span>
              </div>
              
              <div v-if="manga.artist" class="flex items-center">
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24">Artist:</span>
                <span class="text-sm text-gray-900 dark:text-white">{{ manga.artist }}</span>
              </div>
              
              <div v-if="manga.status" class="flex items-center">
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24">Status:</span>
                <span class="text-sm text-gray-900 dark:text-white capitalize">{{ manga.status }}</span>
              </div>
              
              <div v-if="manga.year" class="flex items-center">
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24">Year:</span>
                <span class="text-sm text-gray-900 dark:text-white">{{ manga.year }}</span>
              </div>
              
              <div v-if="manga.provider" class="flex items-center">
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24">Provider:</span>
                <span class="text-sm text-gray-900 dark:text-white">{{ manga.provider }}</span>
              </div>
              
              <div v-if="manga.last_updated" class="flex items-center">
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24">Updated:</span>
                <span class="text-sm text-gray-900 dark:text-white">{{ formatDate(manga.last_updated) }}</span>
              </div>
            </div>
            
            <!-- Genres -->
            <div v-if="manga.genres && manga.genres.length" class="mt-4">
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Genres:</h3>
              <div class="mt-1 flex flex-wrap gap-2">
                <span 
                  v-for="genre in manga.genres" 
                  :key="genre" 
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200"
                >
                  {{ genre }}
                </span>
              </div>
            </div>
            
            <!-- Description -->
            <div v-if="manga.description" class="mt-4">
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Description:</h3>
              <div class="mt-1 text-sm text-gray-900 dark:text-white prose dark:prose-invert max-w-none" v-html="formatDescription(manga.description)"></div>
            </div>
            
            <!-- Chapters -->
            <div v-if="manga.chapters && manga.chapters.length" class="mt-6">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white">Chapters</h3>
                <div class="flex items-center space-x-2">
                  <label for="sort-chapters" class="text-sm text-gray-500 dark:text-gray-400">Sort:</label>
                  <select 
                    id="sort-chapters" 
                    v-model="chapterSort" 
                    class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white"
                  >
                    <option value="desc">Newest First</option>
                    <option value="asc">Oldest First</option>
                  </select>
                </div>
              </div>
              
              <div class="mt-2 border-t border-gray-200 dark:border-dark-600">
                <ul role="list" class="divide-y divide-gray-200 dark:divide-dark-600">
                  <li 
                    v-for="chapter in sortedChapters" 
                    :key="chapter.id" 
                    class="py-4 flex items-center justify-between"
                  >
                    <div class="flex items-center">
                      <div>
                        <p class="text-sm font-medium text-gray-900 dark:text-white">
                          {{ chapter.title }}
                        </p>
                        <p v-if="chapter.upload_date" class="text-xs text-gray-500 dark:text-gray-400">
                          {{ formatDate(chapter.upload_date) }}
                        </p>
                      </div>
                    </div>
                    <div class="flex items-center space-x-2">
                      <button 
                        @click="readChapter(chapter.id)" 
                        class="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                      >
                        Read
                      </button>
                      <button 
                        @click="downloadChapter(chapter.id)" 
                        class="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-dark-600 text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                      >
                        <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                      </button>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useLibraryStore } from '../stores/library';
import { useSettingsStore } from '../stores/settings';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const libraryStore = useLibraryStore();
const settingsStore = useSettingsStore();

const mangaId = computed(() => route.params.id);
const manga = ref(null);
const loading = ref(true);
const error = ref(null);
const inLibrary = ref(false);
const chapterSort = ref('desc');

const isNsfw = computed(() => manga.value?.is_nsfw || manga.value?.is_explicit);
const blurNsfw = computed(() => settingsStore.getNsfwBlur);

const sortedChapters = computed(() => {
  if (!manga.value?.chapters) return [];
  
  return [...manga.value.chapters].sort((a, b) => {
    const aNum = parseFloat(a.number) || 0;
    const bNum = parseFloat(b.number) || 0;
    
    if (chapterSort.value === 'asc') {
      return aNum - bNum;
    } else {
      return bNum - aNum;
    }
  });
});

const fetchMangaDetails = async () => {
  loading.value = true;
  error.value = null;
  
  try {
    const response = await axios.get(`/api/v1/manga/${mangaId.value}`);
    manga.value = response.data;
    
    // Check if manga is in library
    checkLibraryStatus();
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load manga details';
    console.error('Error fetching manga details:', err);
  } finally {
    loading.value = false;
  }
};

const checkLibraryStatus = async () => {
  try {
    const response = await axios.get(`/api/v1/library/check/${mangaId.value}`);
    inLibrary.value = response.data.in_library;
  } catch (err) {
    console.error('Error checking library status:', err);
  }
};

const addToLibrary = async () => {
  try {
    await libraryStore.addToLibrary(mangaId.value);
    inLibrary.value = true;
  } catch (err) {
    console.error('Error adding to library:', err);
  }
};

const removeFromLibrary = async () => {
  if (confirm('Are you sure you want to remove this manga from your library?')) {
    try {
      await libraryStore.removeFromLibrary(mangaId.value);
      inLibrary.value = false;
    } catch (err) {
      console.error('Error removing from library:', err);
    }
  }
};

const startReading = () => {
  if (manga.value?.chapters && manga.value.chapters.length > 0) {
    const firstChapter = sortedChapters.value[chapterSort.value === 'asc' ? 0 : sortedChapters.value.length - 1];
    readChapter(firstChapter.id);
  }
};

const readChapter = (chapterId) => {
  router.push(`/read/${mangaId.value}/${chapterId}`);
};

const downloadManga = async () => {
  try {
    const response = await axios.post(`/api/v1/manga/${mangaId.value}/download`, {
      quality: settingsStore.getDownloadQuality
    }, {
      responseType: 'blob'
    });
    
    // Create a download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${manga.value.title}.cbz`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (err) {
    console.error('Error downloading manga:', err);
    alert('Failed to download manga');
  }
};

const downloadChapter = async (chapterId) => {
  try {
    const chapter = manga.value.chapters.find(c => c.id === chapterId);
    
    const response = await axios.post(`/api/v1/manga/${mangaId.value}/chapters/${chapterId}/download`, {
      quality: settingsStore.getDownloadQuality
    }, {
      responseType: 'blob'
    });
    
    // Create a download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${manga.value.title} - ${chapter.title}.cbz`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (err) {
    console.error('Error downloading chapter:', err);
    alert('Failed to download chapter');
  }
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);
};

const formatDescription = (description) => {
  if (!description) return '';
  
  // Convert newlines to <br> tags
  return description.replace(/\n/g, '<br>');
};

onMounted(() => {
  fetchMangaDetails();
});
</script>
