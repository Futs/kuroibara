<template>
  <div class="backup-page">
    <!-- Header -->
    <div class="bg-white dark:bg-dark-800 shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <div class="md:flex md:items-center md:justify-between">
            <div class="flex-1 min-w-0">
              <h1 class="text-2xl font-bold leading-7 text-gray-900 dark:text-white sm:text-3xl sm:truncate">
                Backup & Restore
              </h1>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Manage backups of your manga library and database
              </p>
            </div>
            <div class="mt-4 flex md:mt-0 md:ml-4">
              <router-link
                to="/recovery"
                class="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-700 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg class="h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Storage Recovery
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
              About Backups
            </h3>
            <div class="mt-2 text-sm text-blue-700 dark:text-blue-300">
              <p>
                Backups include your database (manga metadata, reading progress, settings) and optionally your storage files.
                Regular backups protect against data loss and make it easy to migrate to new servers.
              </p>
              <ul class="mt-2 list-disc list-inside space-y-1">
                <li><strong>Database Only:</strong> Fast backups with metadata, progress, and settings</li>
                <li><strong>Full Backup:</strong> Includes all manga files (larger, takes longer)</li>
                <li><strong>Scheduled:</strong> Automatic daily, weekly, and monthly backups</li>
                <li><strong>Restore:</strong> Upload backup files to restore your library</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Backup Schedule Info -->
      <div v-if="scheduleInfo" class="mb-8 bg-gray-50 dark:bg-dark-700 rounded-lg p-6">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Backup Schedule
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="text-center">
            <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">
              {{ scheduleInfo.daily_enabled ? '✓' : '✗' }}
            </div>
            <div class="text-sm font-medium text-gray-900 dark:text-white">Daily Backups</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ scheduleInfo.daily_enabled ? 'Database only at 2 AM' : 'Disabled' }}
            </div>
            <div v-if="scheduleInfo.next_daily_backup" class="text-xs text-gray-600 dark:text-gray-300 mt-1">
              Next: {{ formatDate(scheduleInfo.next_daily_backup) }}
            </div>
          </div>
          
          <div class="text-center">
            <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">
              {{ scheduleInfo.weekly_enabled ? '✓' : '✗' }}
            </div>
            <div class="text-sm font-medium text-gray-900 dark:text-white">Weekly Backups</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ scheduleInfo.weekly_enabled ? 'Full backup on Sunday at 3 AM' : 'Disabled' }}
            </div>
            <div v-if="scheduleInfo.next_weekly_backup" class="text-xs text-gray-600 dark:text-gray-300 mt-1">
              Next: {{ formatDate(scheduleInfo.next_weekly_backup) }}
            </div>
          </div>
          
          <div class="text-center">
            <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">
              {{ scheduleInfo.monthly_enabled ? '✓' : '✗' }}
            </div>
            <div class="text-sm font-medium text-gray-900 dark:text-white">Monthly Backups</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ scheduleInfo.monthly_enabled ? 'Full backup on 1st at 4 AM' : 'Disabled' }}
            </div>
            <div v-if="scheduleInfo.next_monthly_backup" class="text-xs text-gray-600 dark:text-gray-300 mt-1">
              Next: {{ formatDate(scheduleInfo.next_monthly_backup) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Orphaned Storage Check -->
      <div v-if="orphanedCheck && orphanedCheck.has_orphaned_files" class="mb-8 bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-md p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-yellow-800 dark:text-yellow-200">
              Orphaned Files Detected
            </h3>
            <div class="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
              <p>{{ orphanedCheck.message }}</p>
              <router-link
                v-if="orphanedCheck.recovery_url"
                :to="orphanedCheck.recovery_url"
                class="mt-2 inline-flex items-center text-sm font-medium text-yellow-800 dark:text-yellow-200 hover:text-yellow-900 dark:hover:text-yellow-100"
              >
                Go to Storage Recovery
                <svg class="ml-1 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Backup Manager Component -->
      <BackupManager />

      <!-- Help Section -->
      <div class="mt-12 bg-gray-50 dark:bg-dark-700 rounded-lg p-6">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Backup Best Practices
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Regular Backups
            </h4>
            <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• Automatic daily database backups</li>
              <li>• Weekly full backups with storage</li>
              <li>• Monthly long-term archive backups</li>
              <li>• Manual backups before major changes</li>
            </ul>
          </div>
          <div>
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Storage & Security
            </h4>
            <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• Download backups to external storage</li>
              <li>• Keep multiple backup generations</li>
              <li>• Test restore procedures regularly</li>
              <li>• Store backups in different locations</li>
            </ul>
          </div>
        </div>
        
        <div class="mt-6 pt-6 border-t border-gray-200 dark:border-dark-600">
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Backup Types
          </h4>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p class="font-medium text-gray-700 dark:text-gray-300">Database Only</p>
                <p>Fast backups containing metadata, reading progress, settings, and user data. Ideal for daily backups.</p>
              </div>
              <div>
                <p class="font-medium text-gray-700 dark:text-gray-300">Full Backup</p>
                <p>Complete backup including all manga files and database. Takes longer but provides complete recovery.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import BackupManager from '@/components/BackupManager.vue';

// Set page title
import { useHead } from '@vueuse/head';

useHead({
  title: 'Backup & Restore - Kuroibara',
  meta: [
    {
      name: 'description',
      content: 'Manage backups and restore your manga library'
    }
  ]
});

// Reactive state
const scheduleInfo = ref(null);
const orphanedCheck = ref(null);

// Methods
const loadScheduleInfo = async () => {
  try {
    const response = await axios.get('/api/v1/backup/schedule');
    scheduleInfo.value = response.data;
  } catch (err) {
    console.error('Failed to load schedule info:', err);
  }
};

const checkOrphanedStorage = async () => {
  try {
    const response = await axios.get('/api/v1/backup/check-orphaned');
    orphanedCheck.value = response.data;
  } catch (err) {
    console.error('Failed to check orphaned storage:', err);
  }
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
};

// Load data on mount
onMounted(() => {
  loadScheduleInfo();
  checkOrphanedStorage();
});
</script>

<style scoped>
/* Add any specific styles for the backup page here */
</style>
