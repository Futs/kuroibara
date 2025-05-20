<template>
  <div class="library">
    <div class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden">
      <div class="px-4 py-5 sm:px-6 flex flex-col sm:flex-row sm:justify-between sm:items-center">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            My Library
          </h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage your manga collection
          </p>
        </div>
        <div class="mt-4 sm:mt-0 flex space-x-3">
          <button 
            @click="showFilters = !showFilters" 
            class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-dark-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg class="-ml-0.5 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            {{ showFilters ? 'Hide Filters' : 'Show Filters' }}
          </button>
          <router-link 
            to="/search" 
            class="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg class="-ml-0.5 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add Manga
          </router-link>
        </div>
      </div>
      
      <!-- Filters -->
      <div v-if="showFilters" class="px-4 py-5 bg-gray-50 dark:bg-dark-700 border-t border-b border-gray-200 dark:border-dark-600">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label for="category" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Category
            </label>
            <select 
              id="category" 
              v-model="filters.category" 
              class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-dark-600 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white sm:text-sm rounded-md"
            >
              <option value="">All Categories</option>
              <option v-for="category in categories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </div>
          
          <div>
            <label for="status" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
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
            <label for="sort" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
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
            <label for="order" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
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
      
      <!-- Loading State -->
      <div v-if="loading" class="px-4 py-12 flex justify-center">
        <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
      
      <!-- Error State -->
      <div v-else-if="error" class="px-4 py-5 sm:p-6">
        <div class="rounded-md bg-red-50 dark:bg-red-900 p-4">
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
        <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No manga in your library</h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Get started by adding some manga to your library.
        </p>
        <div class="mt-6">
          <router-link 
            to="/search" 
            class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg class="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add Manga
          </router-link>
        </div>
      </div>
      
      <!-- Manga Grid -->
      <div v-else class="px-4 py-5 sm:p-6">
        <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
          <MangaCard 
            v-for="item in manga" 
            :key="item.id" 
            :manga="item" 
            @remove="removeManga"
          />
        </div>
        
        <!-- Pagination -->
        <div v-if="totalPages > 1" class="mt-6 flex justify-center">
          <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
            <button 
              @click="prevPage" 
              :disabled="currentPage === 1" 
              class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 dark:border-dark-600 bg-white dark:bg-dark-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span class="sr-only">Previous</span>
              <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </button>
            
            <button 
              v-for="page in paginationRange" 
              :key="page" 
              @click="goToPage(page)" 
              :class="[
                page === currentPage 
                  ? 'z-10 bg-primary-50 dark:bg-primary-900 border-primary-500 text-primary-600 dark:text-primary-400' 
                  : 'bg-white dark:bg-dark-800 border-gray-300 dark:border-dark-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-700',
                'relative inline-flex items-center px-4 py-2 border text-sm font-medium'
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
              <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
            </button>
          </nav>
        </div>
      </div>
    </div>
  </div>
</template>
