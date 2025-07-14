<template>
  <div class="metadata-editor">
    <!-- Single Item Editor -->
    <div v-if="!batchMode" class="bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Edit Metadata</h2>
        <div class="flex space-x-2">
          <button
            @click="resetForm"
            class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            Reset
          </button>
          <button
            @click="saveMetadata"
            :disabled="saving"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Cover Image -->
        <div class="lg:col-span-1">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Cover Image
          </label>
          <div class="space-y-4">
            <div class="relative">
              <img
                :src="form.cover_url || '/placeholder-cover.jpg'"
                :alt="form.title"
                class="w-full max-w-xs mx-auto rounded-lg shadow-md"
              />
              <button
                @click="showCoverUpload = true"
                class="absolute top-2 right-2 p-2 bg-black bg-opacity-50 text-white rounded-full hover:bg-opacity-70 transition-opacity"
              >
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Cover URL
              </label>
              <input
                v-model="form.cover_url"
                type="url"
                placeholder="https://example.com/cover.jpg"
                class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
              />
            </div>
          </div>
        </div>

        <!-- Metadata Form -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Basic Information -->
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Basic Information</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Title *
                </label>
                <input
                  v-model="form.title"
                  type="text"
                  required
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Alternative Title
                </label>
                <input
                  v-model="form.alt_title"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Status
                </label>
                <select
                  v-model="form.status"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                >
                  <option value="ongoing">Ongoing</option>
                  <option value="completed">Completed</option>
                  <option value="hiatus">Hiatus</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Rating (0-10)
                </label>
                <input
                  v-model.number="form.rating"
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Language
                </label>
                <select
                  v-model="form.language"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                >
                  <option value="en">English</option>
                  <option value="ja">Japanese</option>
                  <option value="ko">Korean</option>
                  <option value="zh">Chinese</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              v-model="form.description"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
              placeholder="Enter manga description..."
            ></textarea>
          </div>

          <!-- Authors -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Authors
            </label>
            <div class="space-y-2">
              <div
                v-for="(author, index) in form.authors"
                :key="index"
                class="flex items-center space-x-2"
              >
                <input
                  v-model="author.name"
                  type="text"
                  placeholder="Author name"
                  class="flex-1 px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                />
                <select
                  v-model="author.role"
                  class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                >
                  <option value="author">Author</option>
                  <option value="artist">Artist</option>
                  <option value="story">Story</option>
                  <option value="art">Art</option>
                </select>
                <button
                  @click="removeAuthor(index)"
                  class="p-2 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-200"
                >
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </button>
              </div>
              <button
                @click="addAuthor"
                class="px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
              >
                Add Author
              </button>
            </div>
          </div>

          <!-- Genres -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Genres
            </label>
            <div class="space-y-2">
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="genre in form.genres"
                  :key="genre"
                  class="inline-flex items-center px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full"
                >
                  {{ genre }}
                  <button
                    @click="removeGenre(genre)"
                    class="ml-2 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
                  >
                    ×
                  </button>
                </span>
              </div>
              <div class="flex space-x-2">
                <input
                  v-model="newGenre"
                  type="text"
                  placeholder="Add genre"
                  class="flex-1 px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
                  @keyup.enter="addGenre"
                />
                <button
                  @click="addGenre"
                  class="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          <!-- Custom Tags -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Custom Tags
            </label>
            <div class="space-y-2">
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="tag in form.custom_tags"
                  :key="tag.name"
                  class="inline-flex items-center px-3 py-1 text-sm text-white rounded-full"
                  :style="{ backgroundColor: tag.color }"
                >
                  {{ tag.name }}
                  <button
                    @click="removeCustomTag(tag.name)"
                    class="ml-2 text-white hover:text-gray-200"
                  >
                    ×
                  </button>
                </span>
              </div>
              
              <!-- Available Tags -->
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="tag in availableCustomTags"
                  :key="tag.id"
                  @click="addCustomTag(tag)"
                  class="px-3 py-1 text-sm border border-gray-300 dark:border-dark-600 rounded-full hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors"
                  :style="{ borderColor: tag.color }"
                >
                  + {{ tag.name }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Batch Editor -->
    <div v-else class="bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
          Batch Edit Metadata ({{ selectedItems.length }} items)
        </h2>
        <div class="flex space-x-2">
          <button
            @click="$emit('close')"
            class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="saveBatchMetadata"
            :disabled="saving"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ saving ? 'Saving...' : 'Apply Changes' }}
          </button>
        </div>
      </div>

      <div class="space-y-6">
        <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <p class="text-sm text-yellow-800 dark:text-yellow-200">
            Only fields with values will be updated. Leave fields empty to keep existing values.
          </p>
        </div>

        <!-- Batch Form Fields -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Status
            </label>
            <select
              v-model="batchForm.status"
              class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
            >
              <option value="">Keep existing</option>
              <option value="ongoing">Ongoing</option>
              <option value="completed">Completed</option>
              <option value="hiatus">Hiatus</option>
              <option value="cancelled">Cancelled</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Language
            </label>
            <select
              v-model="batchForm.language"
              class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
            >
              <option value="">Keep existing</option>
              <option value="en">English</option>
              <option value="ja">Japanese</option>
              <option value="ko">Korean</option>
              <option value="zh">Chinese</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        <!-- Batch Tags -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Add Custom Tags
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="tag in availableCustomTags"
              :key="tag.id"
              @click="toggleBatchTag(tag)"
              class="px-3 py-1 text-sm rounded-full border transition-colors"
              :class="batchForm.custom_tags.some(t => t.id === tag.id)
                ? 'text-white border-transparent'
                : 'border-gray-300 dark:border-dark-600 hover:bg-gray-100 dark:hover:bg-dark-700'"
              :style="batchForm.custom_tags.some(t => t.id === tag.id) ? { backgroundColor: tag.color } : {}"
            >
              {{ tag.name }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useLibraryStore } from '../stores/library';

const props = defineProps({
  manga: {
    type: Object,
    default: null
  },
  selectedItems: {
    type: Array,
    default: () => []
  },
  batchMode: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['close', 'saved']);

const libraryStore = useLibraryStore();

// Local state
const saving = ref(false);
const showCoverUpload = ref(false);
const newGenre = ref('');

// Form data
const form = ref({
  title: '',
  alt_title: '',
  description: '',
  status: 'unknown',
  rating: 0,
  language: 'en',
  cover_url: '',
  authors: [],
  genres: [],
  custom_tags: []
});

const batchForm = ref({
  status: '',
  language: '',
  custom_tags: []
});

// Computed properties
const availableCustomTags = computed(() => {
  const currentTags = props.batchMode 
    ? batchForm.value.custom_tags.map(t => t.id)
    : form.value.custom_tags.map(t => t.id);
  
  return libraryStore.getCustomTags.filter(tag => !currentTags.includes(tag.id));
});

// Methods
const resetForm = () => {
  if (props.manga) {
    form.value = {
      title: props.manga.title || '',
      alt_title: props.manga.alt_title || '',
      description: props.manga.description || '',
      status: props.manga.status || 'unknown',
      rating: props.manga.rating || 0,
      language: props.manga.language || 'en',
      cover_url: props.manga.cover_url || '',
      authors: props.manga.authors ? [...props.manga.authors] : [],
      genres: props.manga.genres ? props.manga.genres.map(g => g.name) : [],
      custom_tags: props.manga.custom_tags ? [...props.manga.custom_tags] : []
    };
  }
};

const addAuthor = () => {
  form.value.authors.push({ name: '', role: 'author' });
};

const removeAuthor = (index) => {
  form.value.authors.splice(index, 1);
};

const addGenre = () => {
  if (newGenre.value.trim() && !form.value.genres.includes(newGenre.value.trim())) {
    form.value.genres.push(newGenre.value.trim());
    newGenre.value = '';
  }
};

const removeGenre = (genre) => {
  const index = form.value.genres.indexOf(genre);
  if (index > -1) {
    form.value.genres.splice(index, 1);
  }
};

const addCustomTag = (tag) => {
  if (!form.value.custom_tags.some(t => t.id === tag.id)) {
    form.value.custom_tags.push(tag);
  }
};

const removeCustomTag = (tagName) => {
  form.value.custom_tags = form.value.custom_tags.filter(t => t.name !== tagName);
};

const toggleBatchTag = (tag) => {
  const index = batchForm.value.custom_tags.findIndex(t => t.id === tag.id);
  if (index > -1) {
    batchForm.value.custom_tags.splice(index, 1);
  } else {
    batchForm.value.custom_tags.push(tag);
  }
};

const saveMetadata = async () => {
  if (!props.manga) return;
  
  saving.value = true;
  try {
    await libraryStore.updateMangaMetadata(props.manga.id, form.value);
    emit('saved');
  } catch (error) {
    console.error('Error saving metadata:', error);
  } finally {
    saving.value = false;
  }
};

const saveBatchMetadata = async () => {
  if (props.selectedItems.length === 0) return;
  
  saving.value = true;
  try {
    const updates = {};
    if (batchForm.value.status) updates.status = batchForm.value.status;
    if (batchForm.value.language) updates.language = batchForm.value.language;
    if (batchForm.value.custom_tags.length > 0) updates.custom_tags = batchForm.value.custom_tags;
    
    await libraryStore.bulkUpdateMetadata(props.selectedItems.map(item => item.id), updates);
    emit('saved');
  } catch (error) {
    console.error('Error saving batch metadata:', error);
  } finally {
    saving.value = false;
  }
};

// Initialize form when manga prop changes
watch(() => props.manga, resetForm, { immediate: true });
</script>

<style scoped>
.metadata-editor {
  max-height: 80vh;
  overflow-y: auto;
}

/* Custom scrollbar */
.metadata-editor::-webkit-scrollbar {
  width: 6px;
}

.metadata-editor::-webkit-scrollbar-track {
  background: transparent;
}

.metadata-editor::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 3px;
}
</style>
