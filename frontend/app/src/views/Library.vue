<template>
  <div class="library">
    <div class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">
      <div
        class="px-4 py-5 sm:px-6 flex flex-col sm:flex-row sm:justify-between sm:items-center"
      >
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            My Library
          </h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage your manga collection
          </p>
        </div>
        <div class="mt-4 sm:mt-0 flex flex-wrap gap-2">
          <button
            @click="showAdvancedFilters = !showAdvancedFilters"
            class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg
              class="-ml-0.5 mr-2 h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
              />
            </svg>
            Advanced Filters
          </button>

          <button
            @click="showStatistics = !showStatistics"
            class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg
              class="-ml-0.5 mr-2 h-4 w-4"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"
              />
            </svg>
            Statistics
          </button>

          <button
            @click="showDuplicates = !showDuplicates"
            class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg
              class="-ml-0.5 mr-2 h-4 w-4"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                d="M7 9a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2H9a2 2 0 01-2-2V9z"
              />
              <path d="M5 3a2 2 0 00-2 2v6a2 2 0 002 2V5h8a2 2 0 00-2-2H5z" />
            </svg>
            Duplicates
          </button>

          <!-- View Mode Toggle -->
          <div
            class="flex border border-gray-300 dark:border-dark-600 rounded-md"
          >
            <button
              @click="setViewMode('grid')"
              :class="[
                'px-3 py-2 text-sm font-medium rounded-l-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
                viewMode === 'grid'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-700',
              ]"
              title="Grid View"
            >
              <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                />
              </svg>
            </button>
            <button
              @click="setViewMode('list')"
              :class="[
                'px-3 py-2 text-sm font-medium border-l border-gray-300 dark:border-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
                viewMode === 'list'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-700',
              ]"
              title="List View"
            >
              <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
            <button
              @click="setViewMode('detailed')"
              :class="[
                'px-3 py-2 text-sm font-medium rounded-r-md border-l border-gray-300 dark:border-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
                viewMode === 'detailed'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-700',
              ]"
              title="Detailed View"
            >
              <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                  clip-rule="evenodd"
                />
                <path
                  d="M16 7a1 1 0 100-2 1 1 0 000 2zM16 11a1 1 0 100-2 1 1 0 000 2zM16 15a1 1 0 100-2 1 1 0 000 2z"
                />
              </svg>
            </button>
          </div>

          <button
            @click="showImportDialog = true"
            class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg
              class="-ml-0.5 mr-2 h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
              />
            </svg>
            Import
          </button>

          <router-link
            to="/search"
            class="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg
              class="-ml-0.5 mr-2 h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
            Add Manga
          </router-link>
        </div>
      </div>

      <!-- Filters -->
      <div
        v-if="showFilters"
        class="px-4 py-5 bg-gray-50 dark:bg-dark-700 border-t border-b border-gray-200 dark:border-dark-600"
      >
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label
              for="category"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Category
            </label>
            <select
              id="category"
              v-model="filters.category"
              class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-dark-600 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm rounded-md"
            >
              <option value="">All Categories</option>
              <option
                v-for="category in categories"
                :key="category.id"
                :value="category.id"
              >
                {{ category.name }}
              </option>
            </select>
          </div>

          <div>
            <label
              for="status"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Status
            </label>
            <select
              id="status"
              v-model="filters.status"
              class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-dark-600 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm rounded-md"
            >
              <option value="">All Statuses</option>
              <option value="ongoing">Ongoing</option>
              <option value="completed">Completed</option>
              <option value="hiatus">Hiatus</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div>
            <label
              for="sort"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Sort By
            </label>
            <select
              id="sort"
              v-model="filters.sort"
              class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-dark-600 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm rounded-md"
            >
              <option value="title">Title</option>
              <option value="added_date">Date Added</option>
              <option value="last_read">Last Read</option>
              <option value="release_date">Release Date</option>
            </select>
          </div>

          <div>
            <label
              for="order"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Order
            </label>
            <select
              id="order"
              v-model="filters.order"
              class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-dark-600 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm rounded-md"
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </div>
        </div>

        <div class="mt-4 flex justify-end">
          <button
            @click="resetFilters"
            class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 mr-3"
          >
            Reset
          </button>
          <button
            @click="applyFilters"
            class="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Apply Filters
          </button>
        </div>
      </div>

      <!-- Advanced Filters Panel -->
      <div
        v-if="showAdvancedFilters"
        class="border-t border-gray-200 dark:border-dark-600"
      >
        <LibraryFilters />
      </div>

      <!-- Statistics Panel -->
      <div
        v-if="showStatistics"
        class="border-t border-gray-200 dark:border-dark-600 p-6"
      >
        <LibraryStatistics />
      </div>

      <!-- Duplicates Panel -->
      <div
        v-if="showDuplicates"
        class="border-t border-gray-200 dark:border-dark-600 p-6"
      >
        <DuplicateDetection />
      </div>

      <!-- Bulk Operations -->
      <div class="border-t border-gray-200 dark:border-dark-600">
        <BulkOperations />
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="px-4 py-12 flex justify-center">
        <svg
          class="animate-spin h-8 w-8 text-primary-600"
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
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="px-4 py-5 sm:p-6">
        <div class="rounded-md bg-red-50 dark:bg-red-900 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg
                class="h-5 w-5 text-red-400 dark:text-red-300"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
                {{ error }}
              </h3>
              <div class="mt-2 text-sm text-red-700 dark:text-red-300">
                <button
                  @click="fetchLibrary"
                  class="font-medium underline hover:text-red-600 dark:hover:text-red-400"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="manga.length === 0" class="px-4 py-12 text-center">
        <svg
          class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
          />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
          No manga in your library
        </h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Get started by adding some manga to your library.
        </p>
        <div class="mt-6">
          <router-link
            to="/search"
            class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg
              class="-ml-1 mr-2 h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
            Add Manga
          </router-link>
        </div>
      </div>

      <!-- Manga Display -->
      <div v-else class="px-4 py-5 sm:p-6">
        <!-- Grid View -->
        <div
          v-if="viewMode === 'grid'"
          class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6"
        >
          <MangaCard
            v-for="item in manga"
            :key="item.id"
            :manga="item"
            @remove="removeManga"
            @download="downloadManga"
            @import="openImportForManga"
          />
        </div>

        <!-- List View -->
        <div v-else-if="viewMode === 'list'" class="space-y-4">
          <div
            v-for="item in manga"
            :key="item.id"
            class="flex items-center space-x-4 p-4 bg-white dark:bg-dark-800 rounded-lg shadow hover:shadow-md transition-shadow"
          >
            <div class="flex-shrink-0">
              <img
                :src="getMangaCover(item)"
                :alt="getMangaTitle(item)"
                class="h-16 w-12 object-cover rounded"
                @error="$event.target.src = '/placeholder-cover.jpg'"
              />
            </div>
            <div class="flex-1 min-w-0">
              <h3
                class="text-lg font-medium text-gray-900 dark:text-white truncate"
              >
                {{ item.title || item.manga?.title }}
              </h3>
              <p class="text-sm text-gray-500 dark:text-gray-400 truncate">
                {{ item.author || item.manga?.author }}
              </p>
              <div class="flex items-center space-x-4 mt-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  Status: {{ item.status || item.manga?.status || "Unknown" }}
                </span>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  Added: {{ formatDate(item.added_date) }}
                </span>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <router-link
                :to="`/manga/${item.manga_id || item.id}`"
                class="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
              >
                View
              </router-link>
              <button
                @click="downloadManga(item.id)"
                class="text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300"
              >
                Download
              </button>
              <button
                @click="openImportForManga(item.id)"
                class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
              >
                Import
              </button>
              <button
                @click="removeManga(item.id)"
                class="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
              >
                Remove
              </button>
            </div>
          </div>
        </div>

        <!-- Detailed View -->
        <div v-else-if="viewMode === 'detailed'" class="space-y-6">
          <DetailedMangaCard
            v-for="item in manga"
            :key="item.id"
            :manga="item"
            @remove="removeManga"
            @download="downloadManga"
            @import="openImportForManga"
          />
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="mt-6 flex justify-center">
          <nav
            class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px"
            aria-label="Pagination"
          >
            <button
              @click="prevPage"
              :disabled="currentPage === 1"
              class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span class="sr-only">Previous</span>
              <svg
                class="h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fill-rule="evenodd"
                  d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>

            <button
              v-for="page in paginationRange"
              :key="page"
              @click="goToPage(page)"
              :class="[
                page === currentPage
                  ? 'z-10 bg-white dark:bg-primary-900 border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'bg-white dark:bg-dark-800 border-gray-300 dark:border-dark-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-700',
                'relative inline-flex items-center px-4 py-2 border text-sm font-medium',
              ]"
            >
              {{ page }}
            </button>

            <button
              @click="nextPage"
              :disabled="currentPage === totalPages"
              class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span class="sr-only">Next</span>
              <svg
                class="h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fill-rule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
          </nav>
        </div>
      </div>
    </div>

    <!-- Import Dialog Modal -->
    <div v-if="showImportDialog" class="fixed inset-0 z-50 overflow-y-auto">
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
        @click.self="showImportDialog = false"
      >
        <!-- Backdrop -->
        <div
          class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          @click="showImportDialog = false"
        ></div>

        <!-- Modal Content -->
        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full relative z-10"
          @click.stop
        >
          <ImportDialog
            :manga="selectedMangaForImport"
            @close="showImportDialog = false"
            @imported="onMangaImported"
          />
        </div>
      </div>
    </div>

    <!-- Metadata Editor Modal -->
    <div
      v-if="showMetadataEditor"
      class="fixed inset-0 z-50 overflow-y-auto"
      @click.self="showMetadataEditor = false"
    >
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
      >
        <div
          class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
        ></div>

        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full"
        >
          <MetadataEditor
            :manga="selectedMangaForEdit"
            @close="showMetadataEditor = false"
            @saved="onMetadataSaved"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useLibraryStore } from "../stores/library";
import MangaCard from "../components/MangaCard.vue";
import DetailedMangaCard from "../components/DetailedMangaCard.vue";
import LibraryFilters from "../components/LibraryFilters.vue";
import BulkOperations from "../components/BulkOperations.vue";
import LibraryStatistics from "../components/LibraryStatistics.vue";
import DuplicateDetection from "../components/DuplicateDetection.vue";
import MetadataEditor from "../components/MetadataEditor.vue";
import ImportDialog from "../components/ImportDialog.vue";
import VirtualScroller from "../components/VirtualScroller.vue";
import { perf } from "../utils/performance";
import { getCoverUrl } from "../utils/imageProxy";

// Store
const libraryStore = useLibraryStore();

// Reactive data
const showFilters = ref(false);
const showAdvancedFilters = ref(false);
const showStatistics = ref(false);
const showDuplicates = ref(false);
const showImportDialog = ref(false);
const showMetadataEditor = ref(false);
const selectedMangaForEdit = ref(null);
const selectedMangaForImport = ref(null);
const viewMode = ref("grid");
const categories = ref([]);

// Computed properties
const manga = computed(() => libraryStore.getManga);
const loading = computed(() => libraryStore.loading);
const error = computed(() => libraryStore.error);
const filters = computed(() => libraryStore.getFilters);
const pagination = computed(() => libraryStore.getPagination);
const currentPage = computed(() => pagination.value.page);
const totalPages = computed(() =>
  Math.ceil(pagination.value.total / pagination.value.limit),
);

// Pagination range for display
const paginationRange = computed(() => {
  const range = [];
  const start = Math.max(1, currentPage.value - 2);
  const end = Math.min(totalPages.value, currentPage.value + 2);

  for (let i = start; i <= end; i++) {
    range.push(i);
  }

  return range;
});

// Performance tracking
const enableVirtualScrolling = computed(() => manga.value.length > 100);

// Methods
const fetchLibrary = async () => {
  perf.start("library-fetch");
  await libraryStore.fetchLibrary();
  perf.end("library-fetch");
};

const fetchCategories = async () => {
  try {
    // This would need to be implemented in a categories store or API call
    // For now, we'll leave it empty
    categories.value = [];
  } catch (error) {
    console.error("Failed to fetch categories:", error);
  }
};

const applyFilters = () => {
  libraryStore.setFilters(filters.value);
};

const resetFilters = () => {
  libraryStore.setFilters({
    category: null,
    status: null,
    sort: "title",
    order: "asc",
  });
};

const removeManga = async (mangaId) => {
  // Find the manga to get its title for the confirmation dialog
  const mangaItem = manga.value.find((item) => item.id === mangaId);
  const mangaTitle =
    mangaItem?.title || mangaItem?.manga?.title || "this manga";

  if (
    confirm(
      `Are you sure you want to remove "${mangaTitle}" from your library?`,
    )
  ) {
    try {
      await libraryStore.removeFromLibrary(mangaId);
    } catch (error) {
      console.error("Failed to remove manga:", error);
    }
  }
};

const prevPage = () => {
  if (currentPage.value > 1) {
    libraryStore.setPage(currentPage.value - 1);
  }
};

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    libraryStore.setPage(currentPage.value + 1);
  }
};

const goToPage = (page) => {
  libraryStore.setPage(page);
};

// New methods for enhanced library features
const setViewMode = (mode) => {
  viewMode.value = mode;
  libraryStore.setViewMode(mode);
};

const editMangaMetadata = (manga) => {
  selectedMangaForEdit.value = manga;
  showMetadataEditor.value = true;
};

const onMangaImported = () => {
  showImportDialog.value = false;
  selectedMangaForImport.value = null;
  // Refresh library to show newly imported manga
  libraryStore.fetchLibrary();
};

const openImportForManga = (mangaId) => {
  const mangaItem = manga.value.find((item) => item.id === mangaId);
  selectedMangaForImport.value = mangaItem;
  showImportDialog.value = true;
};

const onMetadataSaved = () => {
  showMetadataEditor.value = false;
  selectedMangaForEdit.value = null;
  fetchLibrary(); // Refresh the library
};

const toggleMangaSelection = (mangaId) => {
  libraryStore.toggleMangaSelection(mangaId);
};

const formatDate = (dateString) => {
  if (!dateString) return "Unknown";
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

const downloadManga = async (mangaId) => {
  try {
    await libraryStore.downloadManga(mangaId);
  } catch (error) {
    console.error("Failed to download manga:", error);
  }
};

// Helper methods for manga data access
const getMangaCover = (item) => {
  // Check for custom cover first (library items)
  if (item.custom_cover) {
    return item.custom_cover;
  }

  // For library items with nested manga object
  if (item.manga) {
    return getCoverUrl(item.manga, item.manga.id);
  }

  // For direct manga objects
  return getCoverUrl(item, item.id);
};

const getMangaTitle = (item) => {
  return item.title || item.manga?.title || "Unknown Title";
};

// Watch for filter changes
watch(
  filters,
  () => {
    applyFilters();
  },
  { deep: true },
);

// Lifecycle
onMounted(async () => {
  await fetchLibrary();
  await fetchCategories();
});
</script>
