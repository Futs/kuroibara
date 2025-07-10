<template>
  <div class="recovery-page">
    <!-- Header -->
    <div class="bg-white dark:bg-dark-800 shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <div class="md:flex md:items-center md:justify-between">
            <div class="flex-1 min-w-0">
              <h1 class="text-2xl font-bold leading-7 text-gray-900 dark:text-white sm:text-3xl sm:truncate">
                Storage Recovery
              </h1>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Recover manga from storage after database loss or corruption
              </p>
            </div>
            <div class="mt-4 flex md:mt-0 md:ml-4">
              <router-link
                to="/settings"
                class="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-700 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg class="h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Settings
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Info Banner -->
      <div class="mb-8 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-md p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-blue-800 dark:text-blue-200">
              About Storage Recovery
            </h3>
            <div class="mt-2 text-sm text-blue-700 dark:text-blue-300">
              <p>
                This tool helps you recover manga from your storage volume when the database has been lost or corrupted.
                It scans your organized manga files and allows you to re-import them into a new database.
              </p>
              <ul class="mt-2 list-disc list-inside space-y-1">
                <li>Scans for organized manga in your storage volume</li>
                <li>Extracts metadata from folder structure and CBZ files</li>
                <li>Recreates database entries for recovered manga</li>
                <li>Preserves your organized file structure</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Warning Banner -->
      <div class="mb-8 bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-md p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-yellow-800 dark:text-yellow-200">
              Important Notes
            </h3>
            <div class="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
              <ul class="list-disc list-inside space-y-1">
                <li><strong>Backup first:</strong> Always backup your storage volume before recovery operations</li>
                <li><strong>Reading progress:</strong> Reading progress and bookmarks will be lost and reset</li>
                <li><strong>Custom metadata:</strong> Any custom descriptions or tags will need to be re-added</li>
                <li><strong>File paths:</strong> Original file paths will be updated to match the new organization</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Recovery Component -->
      <StorageRecovery />

      <!-- Help Section -->
      <div class="mt-12 bg-gray-50 dark:bg-dark-700 rounded-lg p-6">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Need Help?
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              When to Use Recovery
            </h4>
            <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• Database corruption or loss</li>
              <li>• Moving to a new server instance</li>
              <li>• After system crashes</li>
              <li>• Restoring from storage backups</li>
            </ul>
          </div>
          <div>
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              What Gets Recovered
            </h4>
            <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• Manga titles and basic metadata</li>
              <li>• Chapter organization and files</li>
              <li>• Volume structure</li>
              <li>• CBZ file metadata (if available)</li>
            </ul>
          </div>
        </div>
        
        <div class="mt-6 pt-6 border-t border-gray-200 dark:border-dark-600">
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Prevention Tips
          </h4>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            <p class="mb-2">To avoid needing recovery in the future:</p>
            <ul class="space-y-1">
              <li>• Set up regular database backups</li>
              <li>• Use persistent volumes for Docker deployments</li>
              <li>• Keep both database and storage backups together</li>
              <li>• Test your backup and restore procedures</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import StorageRecovery from '@/components/StorageRecovery.vue';

// Set page title
import { useHead } from '@vueuse/head';

useHead({
  title: 'Storage Recovery - Kuroibara',
  meta: [
    {
      name: 'description',
      content: 'Recover manga from storage after database loss or corruption'
    }
  ]
});
</script>

<style scoped>
/* Add any specific styles for the recovery page here */
</style>
