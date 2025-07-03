<template>
  <div 
    class="provider-card bg-white dark:bg-dark-700 border border-gray-200 dark:border-dark-600 rounded-lg p-4 transition-all duration-200"
    :class="{
      'ring-2 ring-primary-500 border-primary-500': isFavorite,
      'opacity-50': !provider.user_enabled,
      'cursor-move': draggable
    }"
  >
    <div class="flex items-center justify-between">
      <!-- Provider Info -->
      <div class="flex items-center space-x-3 flex-1">
        <!-- Drag Handle (only for favorites) -->
        <div v-if="draggable" class="cursor-move text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
          <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path d="M7 2a1 1 0 011 1v2a1 1 0 01-2 0V3a1 1 0 011-1zM7 8a1 1 0 011 1v2a1 1 0 01-2 0V9a1 1 0 011-1zM7 14a1 1 0 011 1v2a1 1 0 01-2 0v-2a1 1 0 011-1zM13 2a1 1 0 011 1v2a1 1 0 01-2 0V3a1 1 0 011-1zM13 8a1 1 0 011 1v2a1 1 0 01-2 0V9a1 1 0 011-1zM13 14a1 1 0 011 1v2a1 1 0 01-2 0v-2a1 1 0 011-1z" />
          </svg>
        </div>

        <!-- Provider Icon/Status -->
        <div class="flex-shrink-0">
          <div 
            class="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-medium"
            :class="getProviderStatusColor()"
          >
            {{ provider.name.charAt(0).toUpperCase() }}
          </div>
        </div>

        <!-- Provider Details -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center space-x-2">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white truncate">
              {{ provider.name }}
            </h4>
            
            <!-- Favorite Badge -->
            <span v-if="isFavorite" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
              <svg class="h-3 w-3 mr-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              Favorite
            </span>

            <!-- Priority Badge -->
            <span v-if="isFavorite && provider.priority_order" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              Priority {{ provider.priority_order }}
            </span>
          </div>
          
          <div class="mt-1 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
            <!-- Status -->
            <span class="flex items-center">
              <span 
                class="w-2 h-2 rounded-full mr-1"
                :class="getStatusDotColor()"
              ></span>
              {{ getStatusText() }}
            </span>
            
            <!-- Response Time -->
            <span v-if="provider.response_time">
              {{ provider.response_time }}ms
            </span>
            
            <!-- Uptime -->
            <span v-if="provider.uptime_percentage !== undefined">
              {{ provider.uptime_percentage }}% uptime
            </span>
            
            <!-- NSFW Support -->
            <span v-if="provider.supports_nsfw" class="text-orange-500">
              NSFW
            </span>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center space-x-2">
        <!-- Favorite Toggle -->
        <button
          @click="$emit('toggle-favorite', provider.id)"
          class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-dark-600 transition-colors"
          :class="{
            'text-yellow-500 hover:text-yellow-600': isFavorite,
            'text-gray-400 hover:text-gray-500': !isFavorite
          }"
          :title="isFavorite ? 'Remove from favorites' : 'Add to favorites'"
        >
          <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" :fill="isFavorite ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
        </button>

        <!-- Enable/Disable Toggle -->
        <button
          @click="$emit('toggle-enabled', provider.id)"
          class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          :class="{
            'bg-primary-600': provider.user_enabled,
            'bg-gray-200 dark:bg-gray-600': !provider.user_enabled
          }"
          :title="provider.user_enabled ? 'Disable provider' : 'Enable provider'"
        >
          <span
            class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
            :class="{
              'translate-x-5': provider.user_enabled,
              'translate-x-0': !provider.user_enabled
            }"
          ></span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  provider: {
    type: Object,
    required: true,
  },
  isFavorite: {
    type: Boolean,
    default: false,
  },
  draggable: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['toggle-favorite', 'toggle-enabled']);

// Computed
const getProviderStatusColor = () => {
  if (!props.provider.user_enabled) return 'bg-gray-400';
  
  switch (props.provider.status) {
    case 'healthy':
      return 'bg-green-500';
    case 'degraded':
      return 'bg-yellow-500';
    case 'unhealthy':
      return 'bg-red-500';
    default:
      return 'bg-gray-500';
  }
};

const getStatusDotColor = () => {
  if (!props.provider.user_enabled) return 'bg-gray-400';
  
  switch (props.provider.status) {
    case 'healthy':
      return 'bg-green-400';
    case 'degraded':
      return 'bg-yellow-400';
    case 'unhealthy':
      return 'bg-red-400';
    default:
      return 'bg-gray-400';
  }
};

const getStatusText = () => {
  if (!props.provider.user_enabled) return 'Disabled';
  
  switch (props.provider.status) {
    case 'healthy':
      return 'Healthy';
    case 'degraded':
      return 'Degraded';
    case 'unhealthy':
      return 'Unhealthy';
    default:
      return 'Unknown';
  }
};
</script>

<style scoped>
.provider-card {
  transition: all 0.2s ease-in-out;
}

.provider-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dark .provider-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
</style>
