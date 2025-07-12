<template>
  <div
    class="provider-manga-filters bg-gray-50 dark:bg-dark-700 p-4 rounded-lg border border-gray-200 dark:border-dark-600 mb-4"
  >
    <!-- Primary Filters Row -->
    <div class="flex flex-wrap items-center gap-4 mb-4">
      <!-- Search Filter -->
      <div class="flex items-center space-x-2 min-w-0 flex-1">
        <label
          for="search-filter"
          class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
        >
          Search:
        </label>
        <input
          id="search-filter"
          v-model="localFilters.search"
          @input="debouncedUpdateFilters"
          type="text"
          placeholder="Search manga titles..."
          class="flex-1 text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white"
        />
      </div>

      <!-- Genre Filter -->
      <div class="flex items-center space-x-2">
        <label
          for="genre-filter"
          class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
        >
          Genres:
        </label>
        <div class="relative">
          <button
            @click="showGenreDropdown = !showGenreDropdown"
            class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white px-3 py-2 border bg-white dark:bg-dark-800 min-w-[120px] text-left flex items-center justify-between"
          >
            <span v-if="localFilters.genres.length === 0" class="text-gray-500"
              >All Genres</span
            >
            <span v-else-if="localFilters.genres.length === 1">{{
              localFilters.genres[0]
            }}</span>
            <span v-else>{{ localFilters.genres.length }} selected</span>
            <svg
              class="w-4 h-4 ml-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              ></path>
            </svg>
          </button>

          <div
            v-if="showGenreDropdown"
            class="absolute z-50 mt-1 w-64 bg-white dark:bg-dark-800 border border-gray-300 dark:border-dark-600 rounded-md shadow-lg max-h-60 overflow-y-auto"
          >
            <div class="p-2">
              <div class="flex items-center justify-between mb-2">
                <span
                  class="text-xs font-medium text-gray-700 dark:text-gray-300"
                  >Select Genres</span
                >
                <button
                  v-if="localFilters.genres.length > 0"
                  @click="clearGenres"
                  class="text-xs text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
                >
                  Clear All
                </button>
              </div>
              <div
                v-for="genre in availableGenres"
                :key="genre"
                class="flex items-center space-x-2 py-1 px-2 hover:bg-gray-100 dark:hover:bg-dark-700 rounded cursor-pointer"
                @click="toggleGenre(genre)"
              >
                <input
                  type="checkbox"
                  :checked="localFilters.genres.includes(genre)"
                  class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  @click.stop
                />
                <span class="text-sm text-gray-700 dark:text-gray-300">{{
                  genre
                }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Secondary Filters Row -->
    <div class="flex flex-wrap items-center gap-4">
      <!-- Status Filter -->
      <div class="flex items-center space-x-2">
        <label
          for="status-filter"
          class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
        >
          Status:
        </label>
        <select
          id="status-filter"
          v-model="localFilters.status"
          @change="updateFilters"
          class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white"
        >
          <option value="">All Status</option>
          <option value="ongoing">Ongoing</option>
          <option value="completed">Completed</option>
          <option value="hiatus">Hiatus</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      <!-- Type Filter -->
      <div class="flex items-center space-x-2">
        <label
          for="type-filter"
          class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
        >
          Type:
        </label>
        <select
          id="type-filter"
          v-model="localFilters.type"
          @change="updateFilters"
          class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white"
        >
          <option value="">All Types</option>
          <option value="manga">Manga</option>
          <option value="manhwa">Manhwa</option>
          <option value="manhua">Manhua</option>
          <option value="comic">Comic</option>
        </select>
      </div>

      <!-- Year Filter -->
      <div class="flex items-center space-x-2">
        <label
          for="year-filter"
          class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
        >
          Year:
        </label>
        <select
          id="year-filter"
          v-model="localFilters.year"
          @change="updateFilters"
          class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white"
        >
          <option value="">All Years</option>
          <option v-for="year in availableYears" :key="year" :value="year">
            {{ year }}
          </option>
        </select>
      </div>

      <!-- Content Tags Filter -->
      <div class="flex items-center space-x-2">
        <label
          for="content-filter"
          class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
        >
          Content:
        </label>
        <select
          id="content-filter"
          v-model="localFilters.content"
          @change="updateFilters"
          class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white"
        >
          <option value="">All Content</option>
          <option value="safe">Safe Only</option>
          <option value="nsfw">NSFW Only</option>
        </select>
      </div>

      <!-- Language Filter -->
      <div class="flex items-center space-x-2">
        <label
          for="language-filter"
          class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
        >
          Language:
        </label>
        <select
          id="language-filter"
          v-model="localFilters.language"
          @change="updateFilters"
          class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-800 dark:text-white"
        >
          <option value="">All Languages</option>
          <option value="en">English</option>
          <option value="ja">Japanese</option>
          <option value="ko">Korean</option>
          <option value="zh">Chinese</option>
          <option value="zh-hk">Chinese (Traditional)</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="it">Italian</option>
          <option value="pt">Portuguese</option>
          <option value="ru">Russian</option>
          <option value="ar">Arabic</option>
          <option value="th">Thai</option>
          <option value="vi">Vietnamese</option>
          <option value="id">Indonesian</option>
          <option value="ms">Malay</option>
          <option value="tl">Filipino</option>
          <option value="hi">Hindi</option>
          <option value="bn">Bengali</option>
          <option value="ta">Tamil</option>
          <option value="te">Telugu</option>
          <option value="ml">Malayalam</option>
          <option value="kn">Kannada</option>
          <option value="gu">Gujarati</option>
          <option value="pa">Punjabi</option>
          <option value="ur">Urdu</option>
          <option value="ne">Nepali</option>
          <option value="si">Sinhala</option>
          <option value="my">Myanmar</option>
          <option value="km">Khmer</option>
          <option value="lo">Lao</option>
          <option value="ka">Georgian</option>
          <option value="am">Amharic</option>
          <option value="sw">Swahili</option>
          <option value="zu">Zulu</option>
          <option value="af">Afrikaans</option>
          <option value="he">Hebrew</option>
          <option value="fa">Persian</option>
          <option value="tr">Turkish</option>
          <option value="az">Azerbaijani</option>
          <option value="kk">Kazakh</option>
          <option value="ky">Kyrgyz</option>
          <option value="uz">Uzbek</option>
          <option value="tg">Tajik</option>
          <option value="mn">Mongolian</option>
          <option value="bo">Tibetan</option>
          <option value="ug">Uyghur</option>
          <option value="dz">Dzongkha</option>
          <option value="other">Other</option>
        </select>
      </div>

      <!-- Clear Filters Button -->
      <button
        v-if="hasActiveFilters"
        @click="clearAllFilters"
        class="text-sm px-3 py-1 bg-gray-200 dark:bg-dark-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-dark-500 transition-colors"
      >
        Clear Filters
      </button>
    </div>

    <!-- Active Filters Display -->
    <div
      v-if="hasActiveFilters"
      class="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-gray-200 dark:border-dark-600"
    >
      <span class="text-sm text-gray-600 dark:text-gray-400"
        >Active filters:</span
      >

      <span
        v-if="localFilters.search"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-300"
      >
        Search: "{{ localFilters.search }}"
        <button
          @click="clearFilter('search')"
          class="ml-1 text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200"
        >
          ×
        </button>
      </span>

      <span
        v-for="genre in localFilters.genres"
        :key="genre"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300"
      >
        Genre: {{ genre }}
        <button
          @click="removeGenre(genre)"
          class="ml-1 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
        >
          ×
        </button>
      </span>

      <span
        v-if="localFilters.status"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
      >
        Status: {{ formatStatus(localFilters.status) }}
        <button
          @click="clearFilter('status')"
          class="ml-1 text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200"
        >
          ×
        </button>
      </span>

      <span
        v-if="localFilters.type"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300"
      >
        Type: {{ formatType(localFilters.type) }}
        <button
          @click="clearFilter('type')"
          class="ml-1 text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-200"
        >
          ×
        </button>
      </span>

      <span
        v-if="localFilters.year"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
      >
        Year: {{ localFilters.year }}
        <button
          @click="clearFilter('year')"
          class="ml-1 text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-200"
        >
          ×
        </button>
      </span>

      <span
        v-if="localFilters.content"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
      >
        Content: {{ formatContent(localFilters.content) }}
        <button
          @click="clearFilter('content')"
          class="ml-1 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
        >
          ×
        </button>
      </span>

      <span
        v-if="localFilters.language"
        class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300"
      >
        Language: {{ formatLanguage(localFilters.language) }}
        <button
          @click="clearFilter('language')"
          class="ml-1 text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-200"
        >
          ×
        </button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";

// Simple debounce function
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({
      search: "",
      genres: [],
      status: "",
      type: "",
      year: "",
      content: "",
      language: "",
    }),
  },
  availableGenres: {
    type: Array,
    default: () => [],
  },
  availableYears: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update-filters", "clear-filters"]);

const localFilters = ref({
  search: props.filters.search || "",
  genres: props.filters.genres || [],
  status: props.filters.status || "",
  type: props.filters.type || "",
  year: props.filters.year || "",
  content: props.filters.content || "",
  language: props.filters.language || "",
});

const showGenreDropdown = ref(false);

const hasActiveFilters = computed(() => {
  return (
    localFilters.value.search !== "" ||
    localFilters.value.genres.length > 0 ||
    localFilters.value.status !== "" ||
    localFilters.value.type !== "" ||
    localFilters.value.year !== "" ||
    localFilters.value.content !== "" ||
    localFilters.value.language !== ""
  );
});

const updateFilters = () => {
  emit("update-filters", { ...localFilters.value });
};

// Debounced version for search input
const debouncedUpdateFilters = debounce(updateFilters, 300);

const toggleGenre = (genre) => {
  const index = localFilters.value.genres.indexOf(genre);
  if (index > -1) {
    localFilters.value.genres.splice(index, 1);
  } else {
    localFilters.value.genres.push(genre);
  }
  updateFilters();
};

const removeGenre = (genre) => {
  const index = localFilters.value.genres.indexOf(genre);
  if (index > -1) {
    localFilters.value.genres.splice(index, 1);
    updateFilters();
  }
};

const clearGenres = () => {
  localFilters.value.genres = [];
  updateFilters();
};

const clearAllFilters = () => {
  localFilters.value = {
    search: "",
    genres: [],
    status: "",
    type: "",
    year: "",
    content: "",
    language: "",
  };
  showGenreDropdown.value = false;
  emit("clear-filters");
};

const clearFilter = (filterKey) => {
  if (filterKey === "genres") {
    localFilters.value[filterKey] = [];
  } else {
    localFilters.value[filterKey] = "";
  }
  updateFilters();
};

// Watch for external filter changes
watch(
  () => props.filters,
  (newFilters) => {
    localFilters.value = {
      search: newFilters.search || "",
      genres: newFilters.genres || [],
      status: newFilters.status || "",
      type: newFilters.type || "",
      year: newFilters.year || "",
      content: newFilters.content || "",
      language: newFilters.language || "",
    };
  },
  { deep: true },
);

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest(".relative")) {
    showGenreDropdown.value = false;
  }
};

// Add event listener for clicking outside
onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});

// Formatting functions for display
const formatStatus = (status) => {
  const statusMap = {
    ongoing: "Ongoing",
    completed: "Completed",
    hiatus: "Hiatus",
    cancelled: "Cancelled",
  };
  return statusMap[status] || status;
};

const formatType = (type) => {
  const typeMap = {
    manga: "Manga",
    manhwa: "Manhwa",
    manhua: "Manhua",
    comic: "Comic",
  };
  return typeMap[type] || type;
};

const formatContent = (content) => {
  const contentMap = {
    safe: "Safe Only",
    nsfw: "NSFW Only",
  };
  return contentMap[content] || content;
};

const formatLanguage = (language) => {
  const languageMap = {
    en: "English",
    ja: "Japanese",
    ko: "Korean",
    zh: "Chinese",
    "zh-hk": "Chinese (Traditional)",
    es: "Spanish",
    fr: "French",
    de: "German",
    it: "Italian",
    pt: "Portuguese",
    ru: "Russian",
    ar: "Arabic",
    th: "Thai",
    vi: "Vietnamese",
    id: "Indonesian",
    ms: "Malay",
    tl: "Filipino",
    hi: "Hindi",
    bn: "Bengali",
    ta: "Tamil",
    te: "Telugu",
    ml: "Malayalam",
    kn: "Kannada",
    gu: "Gujarati",
    pa: "Punjabi",
    ur: "Urdu",
    ne: "Nepali",
    si: "Sinhala",
    my: "Myanmar",
    km: "Khmer",
    lo: "Lao",
    ka: "Georgian",
    am: "Amharic",
    sw: "Swahili",
    zu: "Zulu",
    af: "Afrikaans",
    he: "Hebrew",
    fa: "Persian",
    tr: "Turkish",
    az: "Azerbaijani",
    kk: "Kazakh",
    ky: "Kyrgyz",
    uz: "Uzbek",
    tg: "Tajik",
    mn: "Mongolian",
    bo: "Tibetan",
    ug: "Uyghur",
    dz: "Dzongkha",
    other: "Other",
  };
  return languageMap[language] || language;
};
</script>

<style scoped>
.provider-manga-filters {
  transition: all 0.2s ease-in-out;
}
</style>
