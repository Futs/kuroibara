<template>
  <div class="manga-card">
    <div class="relative group cursor-pointer" @click="viewDetails">
      <div class="aspect-w-2 aspect-h-3 rounded-lg overflow-hidden bg-gray-200 dark:bg-dark-700">
        <img
          v-if="getMangaCover"
          :src="getMangaCover"
          :alt="getMangaTitle"
          class="w-full h-full object-center object-cover"
          :class="{ 'blur-md': isNsfw && blurNsfw }"
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

        <!-- Reading Progress -->
        <div v-if="manga.reading_progress && manga.reading_progress.percentage > 0" class="absolute bottom-0 left-0 right-0 h-1 bg-gray-700 dark:bg-gray-600">
          <div
            class="h-full bg-primary-500"
            :style="{ width: `${manga.reading_progress.percentage}%` }"
          ></div>
        </div>

        <!-- Hover Actions -->
        <div class="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
          <router-link
            v-if="getChapters && getChapters.length > 0"
            :to="`/read/${getMangaId}/${manga.reading_progress?.current_chapter || getChapters[0].id}`"
            class="p-2 bg-white dark:bg-dark-800 rounded-full text-gray-700 dark:text-gray-200 hover:text-primary-600 dark:hover:text-primary-400"
            title="Read"
            @click.stop
          >
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </router-link>

          <button
            @click.stop="$emit('remove', getLibraryItemId)"
            class="p-2 bg-white dark:bg-dark-800 rounded-full text-gray-700 dark:text-gray-200 hover:text-red-600 dark:hover:text-red-400"
            title="Remove from Library"
          >
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <div class="mt-2">
        <h3 class="text-sm font-medium text-gray-900 dark:text-white truncate" :title="getMangaTitle">
          {{ getMangaTitle }}
        </h3>
        <p v-if="getMangaAuthor" class="text-xs text-gray-500 dark:text-gray-400 truncate">
          {{ getMangaAuthor }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useSettingsStore } from '../stores/settings';

const props = defineProps({
  manga: {
    type: Object,
    required: true,
  },
});

const router = useRouter();
const settingsStore = useSettingsStore();

// Handle both library items (MangaUserLibrary) and direct manga objects
const getMangaId = computed(() => {
  // If this is a library item, use manga_id or manga.id
  if (props.manga.manga_id) {
    return props.manga.manga_id;
  }
  // If this is a nested manga object, use manga.id
  if (props.manga.manga && props.manga.manga.id) {
    return props.manga.manga.id;
  }
  // Otherwise, it's a direct manga object
  return props.manga.id;
});

const getLibraryItemId = computed(() => {
  // For library items, the main ID is the library item ID
  // For direct manga objects, there's no library item ID
  return props.manga.id;
});

const getMangaTitle = computed(() => {
  // Check for custom title first (library items)
  if (props.manga.custom_title) {
    return props.manga.custom_title;
  }
  // Check nested manga object
  if (props.manga.manga && props.manga.manga.title) {
    return props.manga.manga.title;
  }
  // Direct manga object
  return props.manga.title;
});

const getMangaCover = computed(() => {
  // Check for custom cover first (library items)
  if (props.manga.custom_cover) {
    return props.manga.custom_cover;
  }
  // Check nested manga object
  if (props.manga.manga && props.manga.manga.cover_image) {
    return props.manga.manga.cover_image;
  }
  // Direct manga object
  return props.manga.cover_image || props.manga.cover_url;
});

const getMangaAuthor = computed(() => {
  // Check nested manga object first
  if (props.manga.manga && props.manga.manga.authors && props.manga.manga.authors.length > 0) {
    return props.manga.manga.authors[0].name;
  }
  // Direct manga object
  if (props.manga.authors && props.manga.authors.length > 0) {
    return props.manga.authors[0].name;
  }
  // Fallback to author field
  return props.manga.author;
});

const getChapters = computed(() => {
  // Check nested manga object
  if (props.manga.manga && props.manga.manga.chapters) {
    return props.manga.manga.chapters;
  }
  // Direct manga object
  return props.manga.chapters;
});

const isNsfw = computed(() => {
  // Check nested manga object
  if (props.manga.manga) {
    return props.manga.manga.is_nsfw || props.manga.manga.is_explicit;
  }
  // Direct manga object
  return props.manga.is_nsfw || props.manga.is_explicit;
});

const blurNsfw = computed(() => settingsStore.getNsfwBlur);

// Methods
const viewDetails = (event) => {
  // Prevent navigation if clicking on action buttons
  if (event.target.closest('button') || event.target.closest('a')) {
    return;
  }

  router.push(`/manga/${getMangaId.value}`);
};

defineEmits(['remove']);
</script>
