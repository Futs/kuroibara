<template>
  <div class="provider-summary-card bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">
    <!-- Provider Header -->
    <div class="px-6 py-4 border-b border-gray-200 dark:border-dark-600">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <!-- Provider Icon/Logo -->
          <div class="flex-shrink-0">
            <div class="h-12 w-12 rounded-lg bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
              <svg
                class="h-6 w-6 text-primary-600 dark:text-primary-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
            </div>
          </div>
          
          <!-- Provider Info -->
          <div>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              {{ provider.name }}
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ provider.url }}
            </p>
          </div>
        </div>

        <!-- Status Badge -->
        <div class="flex items-center space-x-2">
          <span
            :class="[
              'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
              getStatusBadgeClass(provider.status),
            ]"
          >
            <span
              :class="[
                'w-1.5 h-1.5 rounded-full mr-1.5',
                getStatusDotClass(provider.status),
              ]"
            ></span>
            {{ formatStatus(provider.status) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Provider Details -->
    <div class="px-6 py-4">
      <dl class="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
        <div>
          <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
            Status
          </dt>
          <dd class="text-sm text-gray-900 dark:text-white">
            {{ provider.is_healthy ? 'Healthy' : 'Unhealthy' }}
          </dd>
        </div>
        
        <div>
          <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
            Response Time
          </dt>
          <dd class="text-sm text-gray-900 dark:text-white">
            {{ provider.response_time ? `${provider.response_time}ms` : 'N/A' }}
          </dd>
        </div>
        
        <div>
          <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
            Uptime
          </dt>
          <dd class="text-sm text-gray-900 dark:text-white">
            {{ provider.uptime_percentage }}%
          </dd>
        </div>
        
        <div>
          <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
            NSFW Support
          </dt>
          <dd class="text-sm text-gray-900 dark:text-white">
            {{ provider.supports_nsfw ? 'Yes' : 'No' }}
          </dd>
        </div>
        
        <div>
          <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
            Priority
          </dt>
          <dd class="text-sm text-gray-900 dark:text-white">
            {{ provider.is_priority ? 'High' : 'Normal' }}
          </dd>
        </div>
        
        <div>
          <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
            Last Check
          </dt>
          <dd class="text-sm text-gray-900 dark:text-white">
            {{ formatLastCheck(provider.last_check) }}
          </dd>
        </div>
      </dl>
    </div>

    <!-- Actions -->
    <div class="px-6 py-4 bg-gray-50 dark:bg-dark-700 border-t border-gray-200 dark:border-dark-600">
      <div class="flex justify-between items-center">
        <button
          @click="$emit('test-provider')"
          class="btn btn-secondary btn-sm"
          :disabled="testing"
        >
          <svg
            v-if="testing"
            class="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          {{ testing ? 'Testing...' : 'Test Provider' }}
        </button>
        
        <a
          :href="provider.url"
          target="_blank"
          rel="noopener noreferrer"
          class="btn btn-primary btn-sm"
        >
          Visit Site
          <svg
            class="ml-1 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  provider: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["test-provider"]);

const testing = ref(false);

const getStatusBadgeClass = (status) => {
  switch (status) {
    case "healthy":
      return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300";
    case "unhealthy":
      return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300";
    case "warning":
      return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300";
    default:
      return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300";
  }
};

const getStatusDotClass = (status) => {
  switch (status) {
    case "healthy":
      return "bg-green-400";
    case "unhealthy":
      return "bg-red-400";
    case "warning":
      return "bg-yellow-400";
    default:
      return "bg-gray-400";
  }
};

const formatStatus = (status) => {
  if (!status) return "Unknown";
  return status.charAt(0).toUpperCase() + status.slice(1);
};

const formatLastCheck = (lastCheck) => {
  if (!lastCheck) return "Never";
  
  const date = new Date(lastCheck);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
};
</script>

<style scoped>
.provider-summary-card {
  transition: all 0.2s ease-in-out;
}

.provider-summary-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}
</style>
