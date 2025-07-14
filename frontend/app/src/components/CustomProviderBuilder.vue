<template>
  <div class="custom-provider-builder bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Custom Provider Builder</h2>
      <div class="flex space-x-2">
        <button
          @click="loadTemplate"
          class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
        >
          Load Template
        </button>
        <button
          @click="testProvider"
          :disabled="!canTest"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          Test Provider
        </button>
        <button
          @click="saveProvider"
          :disabled="!canSave"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          Save Provider
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Configuration Panel -->
      <div class="space-y-6">
        <!-- Basic Information -->
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Basic Information</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Provider Name *
              </label>
              <input
                v-model="provider.name"
                type="text"
                placeholder="My Custom Provider"
                class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                required
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <textarea
                v-model="provider.description"
                rows="3"
                placeholder="Description of what this provider does..."
                class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
              ></textarea>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Language
                </label>
                <select
                  v-model="provider.language"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
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
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Content Rating
                </label>
                <select
                  v-model="provider.content_rating"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                >
                  <option value="safe">Safe</option>
                  <option value="suggestive">Suggestive</option>
                  <option value="mature">Mature</option>
                  <option value="explicit">Explicit</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- API Configuration -->
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">API Configuration</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Base URL *
              </label>
              <input
                v-model="provider.base_url"
                type="url"
                placeholder="https://api.example.com"
                class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                required
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Search Endpoint
              </label>
              <input
                v-model="provider.search_endpoint"
                type="text"
                placeholder="/search?q={query}&page={page}"
                class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
              />
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Use {query}, {page}, {limit} as placeholders
              </p>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Details Endpoint
              </label>
              <input
                v-model="provider.details_endpoint"
                type="text"
                placeholder="/manga/{id}"
                class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
              />
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Use {id} as placeholder for manga ID
              </p>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Chapters Endpoint
              </label>
              <input
                v-model="provider.chapters_endpoint"
                type="text"
                placeholder="/manga/{id}/chapters"
                class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
              />
            </div>
          </div>
        </div>

        <!-- Headers and Authentication -->
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Headers & Authentication</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Custom Headers
              </label>
              <div class="space-y-2">
                <div
                  v-for="(header, index) in provider.headers"
                  :key="index"
                  class="flex space-x-2"
                >
                  <input
                    v-model="header.key"
                    type="text"
                    placeholder="Header name"
                    class="flex-1 px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                  />
                  <input
                    v-model="header.value"
                    type="text"
                    placeholder="Header value"
                    class="flex-1 px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                  />
                  <button
                    @click="removeHeader(index)"
                    class="px-3 py-2 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-200"
                  >
                    ×
                  </button>
                </div>
                <button
                  @click="addHeader"
                  class="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Add Header
                </button>
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Rate Limit (req/min)
                </label>
                <input
                  v-model.number="provider.rate_limit"
                  type="number"
                  min="1"
                  max="1000"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Timeout (seconds)
                </label>
                <input
                  v-model.number="provider.timeout"
                  type="number"
                  min="5"
                  max="120"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Data Extraction Rules -->
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Data Extraction Rules</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Response Format
              </label>
              <select
                v-model="provider.response_format"
                class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
              >
                <option value="json">JSON</option>
                <option value="xml">XML</option>
                <option value="html">HTML</option>
              </select>
            </div>
            
            <div v-if="provider.response_format === 'json'">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                JSON Path Mappings
              </label>
              <div class="space-y-2">
                <div class="grid grid-cols-2 gap-2">
                  <input
                    v-model="provider.mappings.title"
                    type="text"
                    placeholder="$.data[*].title"
                    class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                  />
                  <span class="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 flex items-center">Title</span>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <input
                    v-model="provider.mappings.id"
                    type="text"
                    placeholder="$.data[*].id"
                    class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                  />
                  <span class="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 flex items-center">ID</span>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <input
                    v-model="provider.mappings.cover"
                    type="text"
                    placeholder="$.data[*].cover_url"
                    class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                  />
                  <span class="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 flex items-center">Cover URL</span>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <input
                    v-model="provider.mappings.description"
                    type="text"
                    placeholder="$.data[*].description"
                    class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                  />
                  <span class="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 flex items-center">Description</span>
                </div>
              </div>
            </div>
            
            <div v-else-if="provider.response_format === 'html'">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                CSS Selector Mappings
              </label>
              <div class="space-y-2">
                <div class="grid grid-cols-2 gap-2">
                  <input
                    v-model="provider.selectors.title"
                    type="text"
                    placeholder=".manga-title"
                    class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                  />
                  <span class="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 flex items-center">Title</span>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <input
                    v-model="provider.selectors.cover"
                    type="text"
                    placeholder=".manga-cover img"
                    class="px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-800 dark:text-white"
                  />
                  <span class="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 flex items-center">Cover</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Preview Panel -->
      <div class="space-y-6">
        <!-- Test Results -->
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Test Results</h3>
          
          <div v-if="testing" class="flex items-center justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span class="ml-2 text-gray-600 dark:text-gray-400">Testing provider...</span>
          </div>
          
          <div v-else-if="testResults" class="space-y-4">
            <div class="flex items-center space-x-2">
              <div 
                class="w-3 h-3 rounded-full"
                :class="testResults.success ? 'bg-green-500' : 'bg-red-500'"
              ></div>
              <span class="font-medium">
                {{ testResults.success ? 'Test Successful' : 'Test Failed' }}
              </span>
            </div>
            
            <div v-if="testResults.error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
              {{ testResults.error }}
            </div>
            
            <div v-if="testResults.data" class="space-y-2">
              <div class="text-sm font-medium text-gray-700 dark:text-gray-300">Sample Results:</div>
              <div class="max-h-64 overflow-y-auto">
                <pre class="text-xs bg-gray-100 dark:bg-dark-800 p-2 rounded">{{ JSON.stringify(testResults.data, null, 2) }}</pre>
              </div>
            </div>
            
            <div v-if="testResults.metrics" class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-600 dark:text-gray-400">Response Time:</span>
                <span class="font-medium ml-1">{{ testResults.metrics.responseTime }}ms</span>
              </div>
              <div>
                <span class="text-gray-600 dark:text-gray-400">Results Found:</span>
                <span class="font-medium ml-1">{{ testResults.metrics.resultCount }}</span>
              </div>
            </div>
          </div>
          
          <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
            Configure your provider and click "Test Provider" to see results
          </div>
        </div>

        <!-- Provider Preview -->
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Provider Preview</h3>
          
          <div class="space-y-3">
            <div class="flex items-center space-x-3">
              <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <span class="text-blue-600 dark:text-blue-400 font-bold text-lg">
                  {{ provider.name ? provider.name.charAt(0).toUpperCase() : '?' }}
                </span>
              </div>
              <div>
                <div class="font-medium text-gray-900 dark:text-white">
                  {{ provider.name || 'Unnamed Provider' }}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">
                  {{ provider.description || 'No description provided' }}
                </div>
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-600 dark:text-gray-400">Language:</span>
                <span class="font-medium ml-1">{{ provider.language || 'Not set' }}</span>
              </div>
              <div>
                <span class="text-gray-600 dark:text-gray-400">Content:</span>
                <span class="font-medium ml-1">{{ provider.content_rating || 'Not set' }}</span>
              </div>
              <div>
                <span class="text-gray-600 dark:text-gray-400">Rate Limit:</span>
                <span class="font-medium ml-1">{{ provider.rate_limit || 60 }}/min</span>
              </div>
              <div>
                <span class="text-gray-600 dark:text-gray-400">Timeout:</span>
                <span class="font-medium ml-1">{{ provider.timeout || 30 }}s</span>
              </div>
            </div>
            
            <div v-if="provider.base_url" class="text-sm">
              <span class="text-gray-600 dark:text-gray-400">Base URL:</span>
              <span class="font-medium ml-1 break-all">{{ provider.base_url }}</span>
            </div>
          </div>
        </div>

        <!-- Templates -->
        <div class="bg-gray-50 dark:bg-dark-700 p-4 rounded-lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Templates</h3>
          
          <div class="space-y-2">
            <button
              v-for="template in templates"
              :key="template.id"
              @click="loadProviderTemplate(template)"
              class="w-full text-left p-3 border border-gray-200 dark:border-dark-600 rounded hover:bg-gray-100 dark:hover:bg-dark-600 transition-colors"
            >
              <div class="font-medium text-gray-900 dark:text-white">{{ template.name }}</div>
              <div class="text-sm text-gray-600 dark:text-gray-400">{{ template.description }}</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useProvidersStore } from '../stores/providers';

const providersStore = useProvidersStore();

// Local state
const testing = ref(false);
const testResults = ref(null);

// Provider configuration
const provider = ref({
  name: '',
  description: '',
  language: 'en',
  content_rating: 'safe',
  base_url: '',
  search_endpoint: '',
  details_endpoint: '',
  chapters_endpoint: '',
  headers: [],
  rate_limit: 60,
  timeout: 30,
  response_format: 'json',
  mappings: {
    title: '',
    id: '',
    cover: '',
    description: '',
    authors: '',
    genres: '',
  },
  selectors: {
    title: '',
    cover: '',
    description: '',
    authors: '',
    genres: '',
  },
});

// Templates
const templates = ref([
  {
    id: 'generic-json',
    name: 'Generic JSON API',
    description: 'Standard REST API with JSON responses',
    config: {
      response_format: 'json',
      search_endpoint: '/search?q={query}&page={page}',
      details_endpoint: '/manga/{id}',
      chapters_endpoint: '/manga/{id}/chapters',
      mappings: {
        title: '$.data[*].title',
        id: '$.data[*].id',
        cover: '$.data[*].cover_url',
        description: '$.data[*].description',
      }
    }
  },
  {
    id: 'html-scraper',
    name: 'HTML Scraper',
    description: 'Web scraping with CSS selectors',
    config: {
      response_format: 'html',
      search_endpoint: '/search?q={query}',
      selectors: {
        title: '.manga-title',
        cover: '.manga-cover img',
        description: '.manga-description',
      }
    }
  }
]);

// Computed properties
const canTest = computed(() => {
  return provider.value.name && provider.value.base_url;
});

const canSave = computed(() => {
  return canTest.value && provider.value.search_endpoint;
});

// Methods
const addHeader = () => {
  provider.value.headers.push({ key: '', value: '' });
};

const removeHeader = (index) => {
  provider.value.headers.splice(index, 1);
};

const loadTemplate = () => {
  // Show template selection modal or dropdown
  console.log('Load template');
};

const loadProviderTemplate = (template) => {
  Object.assign(provider.value, template.config);
};

const testProvider = async () => {
  testing.value = true;
  testResults.value = null;
  
  try {
    const response = await fetch('/api/v1/providers/test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        config: provider.value,
        test_query: 'test'
      })
    });
    
    const result = await response.json();
    testResults.value = result;
  } catch (error) {
    testResults.value = {
      success: false,
      error: error.message
    };
  } finally {
    testing.value = false;
  }
};

const saveProvider = async () => {
  try {
    await providersStore.createCustomProvider(provider.value);
    // Reset form or show success message
    console.log('Provider saved successfully');
  } catch (error) {
    console.error('Error saving provider:', error);
  }
};
</script>

<style scoped>
.custom-provider-builder {
  max-height: 90vh;
  overflow-y: auto;
}
</style>
