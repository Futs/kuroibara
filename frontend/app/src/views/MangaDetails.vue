<template>
  <div class="manga-details">
    <div v-if="loading" class="flex justify-center items-center py-12">
      <svg
        class="animate-spin h-10 w-10 text-primary-600"
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

    <div v-else-if="error" class="bg-red-50 dark:bg-red-900 p-4 rounded-md">
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
              @click="fetchMangaDetails"
              class="font-medium underline hover:text-red-600 dark:hover:text-red-400"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-else-if="manga"
      class="bg-white dark:bg-dark-800 shadow rounded-lg overflow-hidden"
    >
      <!-- Manga Header -->
      <div class="relative">
        <div class="h-48 sm:h-64 w-full bg-gray-200 dark:bg-dark-700">
          <img
            v-if="manga.cover_image"
            :src="getCoverUrl(manga.id)"
            :alt="manga.title"
            class="w-full h-full object-cover"
            @error="onImageError"
          />
        </div>

        <div
          class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4"
        >
          <h1 class="text-2xl sm:text-3xl font-bold text-white">
            {{ manga.title }}
          </h1>
          <p
            v-if="manga.alternative_titles && manga.alternative_titles.length"
            class="text-sm text-gray-300 mt-1"
          >
            {{ manga.alternative_titles.join(" / ") }}
          </p>
        </div>
      </div>

      <!-- Update Notification -->
      <div
        v-if="showUpdateNotification && newChaptersCount > 0"
        class="fixed top-4 right-4 z-50 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2"
      >
        <svg
          class="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span
          >{{ newChaptersCount }} new chapter{{
            newChaptersCount > 1 ? "s" : ""
          }}
          available!</span
        >
        <button
          @click="showUpdateNotification = false"
          class="ml-2 text-white hover:text-gray-200"
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <!-- Manga Content -->
      <div class="p-4 sm:p-6">
        <div class="flex flex-col md:flex-row gap-6">
          <!-- Left Column - Cover and Actions -->
          <div class="w-full md:w-1/3 lg:w-1/4">
            <div
              class="aspect-[2/3] rounded-lg overflow-hidden bg-gray-200 dark:bg-dark-700"
            >
              <img
                v-if="manga.cover_image"
                :src="getCoverUrl(manga.id)"
                :alt="manga.title"
                class="w-full h-full object-center object-cover"
                :class="{ 'blur-md': isNsfw && blurNsfw }"
                @error="onImageError"
              />
              <div
                v-else
                class="w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-500"
              >
                <svg
                  class="h-12 w-12"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>

              <!-- NSFW Badge -->
              <div
                v-if="isNsfw"
                class="absolute top-2 right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded"
              >
                NSFW
              </div>
            </div>

            <div class="mt-4 space-y-3">
              <!-- Remove from Library (only for library items) -->
              <button
                v-if="!isExternal && inLibrary"
                @click="removeFromLibrary"
                class="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <svg
                  class="h-5 w-5 mr-2"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
                Remove from Library
              </button>

              <!-- Add to Library (only for external manga) -->
              <button
                v-else-if="isExternal && !inLibrary"
                @click="addToLibrary"
                class="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg
                  class="h-5 w-5 mr-2"
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
                Add to Library
              </button>

              <!-- Start Reading (always show if chapters exist) -->
              <button
                v-if="
                  (manga.chapters && manga.chapters.length > 0) ||
                  (libraryItemDetails &&
                    libraryItemDetails.chapters &&
                    libraryItemDetails.chapters.length > 0)
                "
                @click="startReading"
                class="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg
                  class="h-5 w-5 mr-2"
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
                Start Reading
              </button>

              <!-- Download All (only for library items) -->
              <div
                v-if="
                  !isExternal &&
                  inLibrary &&
                  manga.provider &&
                  manga.external_id
                "
                class="space-y-2"
              >
                <button
                  @click="downloadManga"
                  :disabled="bulkDownloadProgress.isDownloading"
                  class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg
                    class="h-5 w-5 mr-2"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  {{
                    bulkDownloadProgress.isDownloading
                      ? "Downloading..."
                      : "Download All"
                  }}
                </button>

                <!-- Progress Bar (Example B Style) -->
                <div
                  v-if="bulkDownloadProgress.isDownloading"
                  class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2"
                >
                  <div
                    class="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    :style="{ width: `${bulkDownloadProgress.progress}%` }"
                  ></div>
                </div>
                <div
                  v-if="bulkDownloadProgress.isDownloading"
                  class="text-xs text-gray-600 dark:text-gray-400 text-center"
                >
                  {{ bulkDownloadProgress.completedChapters }}/{{
                    bulkDownloadProgress.totalChapters
                  }}
                  chapters • {{ Math.round(bulkDownloadProgress.progress) }}%
                </div>
              </div>

              <!-- Import Files (only for library items) -->
              <button
                v-if="!isExternal"
                @click="showImportDialog = true"
                class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm text-sm font-medium text-blue-600 dark:text-blue-400 bg-white dark:bg-dark-800 hover:bg-blue-50 dark:hover:bg-blue-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg
                  class="-ml-1 mr-2 h-4 w-4"
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
                Import Files
              </button>

              <!-- Folder Structure Management (only for library items) -->
              <button
                v-if="!isExternal && inLibrary"
                @click="goToMediaManagement"
                class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm text-sm font-medium text-purple-600 dark:text-purple-400 bg-white dark:bg-dark-800 hover:bg-purple-50 dark:hover:bg-purple-900/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                <svg
                  class="-ml-1 mr-2 h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                  />
                </svg>
                Manage Structure
              </button>
            </div>
          </div>

          <!-- Right Column - Details and Chapters -->
          <div class="w-full md:w-2/3 lg:w-3/4">
            <!-- Manga Info -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div v-if="manga.author" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Author:</span
                >
                <span class="text-sm text-gray-900 dark:text-white">{{
                  manga.author
                }}</span>
              </div>

              <div v-if="manga.artist" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Artist:</span
                >
                <span class="text-sm text-gray-900 dark:text-white">{{
                  manga.artist
                }}</span>
              </div>

              <div v-if="manga.status" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Status:</span
                >
                <span
                  class="text-sm text-gray-900 dark:text-white capitalize"
                  >{{ manga.status }}</span
                >
              </div>

              <div v-if="manga.year" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Year:</span
                >
                <span class="text-sm text-gray-900 dark:text-white">{{
                  manga.year
                }}</span>
              </div>

              <div v-if="manga.provider" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Provider:</span
                >
                <span class="text-sm text-gray-900 dark:text-white">{{
                  manga.provider
                }}</span>
              </div>

              <div v-if="manga.last_updated" class="flex items-center">
                <span
                  class="text-sm font-medium text-gray-500 dark:text-gray-400 w-24"
                  >Updated:</span
                >
                <span class="text-sm text-gray-900 dark:text-white">{{
                  formatDate(manga.last_updated)
                }}</span>
              </div>
            </div>

            <!-- Genres -->
            <div v-if="manga.genres && manga.genres.length" class="mt-4">
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Genres:
              </h3>
              <div class="mt-1 flex flex-wrap gap-2">
                <span
                  v-for="genre in manga.genres"
                  :key="genre.id || genre"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200"
                >
                  {{ typeof genre === "object" ? genre.name : genre }}
                </span>
              </div>
            </div>

            <!-- Description -->
            <div v-if="manga.description" class="mt-4">
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">
                Description:
              </h3>
              <div
                class="mt-1 text-sm text-gray-900 dark:text-white prose dark:prose-invert max-w-none"
                v-html="formatDescription(manga.description)"
              ></div>
            </div>

            <!-- Provider Rate Limit Status -->
            <div
              v-if="rateLimitStatus && rateLimitStatus.is_rate_limited"
              class="mt-4"
            >
              <div
                class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-4"
              >
                <div class="flex">
                  <div class="flex-shrink-0">
                    <svg
                      class="h-5 w-5 text-yellow-400"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                        clip-rule="evenodd"
                      />
                    </svg>
                  </div>
                  <div class="ml-3">
                    <h3
                      class="text-sm font-medium text-yellow-800 dark:text-yellow-200"
                    >
                      {{ rateLimitStatus.provider_name }} Rate Limited
                    </h3>
                    <div
                      class="mt-2 text-sm text-yellow-700 dark:text-yellow-300"
                    >
                      <p>
                        Downloads are temporarily limited. Please wait
                        {{ formatTime(rateLimitStatus.seconds_remaining) }}
                        before trying again.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Chapters -->
            <div
              v-if="
                (manga.chapters && manga.chapters.length) ||
                (providerChapters && providerChapters.length)
              "
              class="mt-6"
            >
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white">
                  Chapters ({{
                    providerChapters && providerChapters.length
                      ? providerChapters.length
                      : manga.chapters
                        ? manga.chapters.length
                        : 0
                  }})
                </h3>
                <div class="flex items-center space-x-4">
                  <!-- View Mode Toggle (for library items) -->
                  <div
                    v-if="!isExternal && libraryItemDetails"
                    class="flex items-center space-x-2"
                  >
                    <span class="text-sm text-gray-500 dark:text-gray-400"
                      >View:</span
                    >
                    <div class="flex rounded-md shadow-sm">
                      <button
                        @click="viewMode = 'chapters'"
                        :class="[
                          'px-3 py-1 text-sm font-medium rounded-l-md border',
                          viewMode === 'chapters'
                            ? 'bg-primary-600 text-white border-primary-600'
                            : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-dark-600 hover:bg-gray-50 dark:hover:bg-dark-700',
                        ]"
                      >
                        Chapters
                      </button>
                      <button
                        @click="viewMode = 'volumes'"
                        :class="[
                          'px-3 py-1 text-sm font-medium rounded-r-md border-t border-r border-b',
                          viewMode === 'volumes'
                            ? 'bg-primary-600 text-white border-primary-600'
                            : 'bg-white dark:bg-dark-800 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-dark-600 hover:bg-gray-50 dark:hover:bg-dark-700',
                        ]"
                      >
                        Volumes
                      </button>
                    </div>
                  </div>

                  <!-- Download Summary (for library items) -->
                  <div
                    v-if="!isExternal && libraryItemDetails"
                    class="text-sm text-gray-500 dark:text-gray-400"
                  >
                    {{
                      libraryItemDetails.download_summary.downloaded_chapters
                    }}/{{ libraryItemDetails.download_summary.total_chapters }}
                    downloaded
                  </div>

                  <!-- Manual Refresh Button -->
                  <button
                    v-if="enableManualRefresh && !isExternal && inLibrary"
                    @click="manualRefreshChapters"
                    :disabled="isRefreshing"
                    class="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-dark-600 text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 mr-3"
                    :title="
                      lastUpdateTime
                        ? `Last updated: ${formatDate(lastUpdateTime)}`
                        : 'Refresh chapter list'
                    "
                  >
                    <svg
                      :class="[
                        'w-4 h-4 mr-1',
                        isRefreshing ? 'animate-spin' : '',
                      ]"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                    {{ isRefreshing ? "Refreshing..." : "Refresh" }}
                  </button>

                  <!-- Discover Alternatives Button -->
                  <button
                    v-if="!isExternal && inLibrary"
                    @click="discoverAlternatives"
                    :disabled="isDiscoveringAlternatives"
                    class="inline-flex items-center px-3 py-1 border border-blue-300 dark:border-blue-600 text-sm leading-4 font-medium rounded-md text-blue-700 dark:text-blue-200 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 mr-3"
                    title="Find alternative sources for chapters"
                  >
                    <svg
                      :class="[
                        'w-4 h-4 mr-1',
                        isDiscoveringAlternatives ? 'animate-spin' : '',
                      ]"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                    {{
                      isDiscoveringAlternatives
                        ? "Discovering..."
                        : "Find Alternatives"
                    }}
                  </button>

                  <label
                    for="sort-chapters"
                    class="text-sm text-gray-500 dark:text-gray-400"
                    >Sort:</label
                  >
                  <select
                    id="sort-chapters"
                    v-model="chapterSort"
                    class="text-sm border-gray-300 dark:border-dark-600 rounded-md focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white"
                  >
                    <option value="desc">Newest First</option>
                    <option value="asc">Oldest First</option>
                  </select>
                </div>
              </div>

              <!-- Chapter Management (for library items) -->
              <div v-if="!isExternal && libraryItemDetails" class="mt-4">
                <ChapterManagement
                  :manga-id="mangaId"
                  :chapters="libraryItemDetails.chapters || []"
                  @chapters-updated="refreshMangaDetails"
                />
              </div>

              <!-- Chapter Filters (for library items) -->
              <div v-if="!isExternal && libraryItemDetails" class="mt-4">
                <ChapterFilters
                  :available-languages="availableLanguages"
                  :available-volumes="availableVolumes"
                  :filters="chapterFilters"
                  @update-filters="updateChapterFilters"
                />
              </div>

              <div class="mt-2 border-t border-gray-200 dark:border-dark-600">
                <!-- Volume View (for library items) -->
                <div
                  v-if="
                    !isExternal && libraryItemDetails && viewMode === 'volumes'
                  "
                  class="space-y-4 pt-4"
                >
                  <VolumeDownloadCard
                    v-for="volume in groupedVolumes"
                    :key="volume.number"
                    :volume="volume"
                    @download-volume="downloadVolume"
                    @download-chapter="downloadChapter"
                    @retry-failed="retryFailedChapters"
                  />
                </div>

                <!-- All chapters for library manga (show all chapters with download status) -->
                <div
                  v-else-if="
                    !isExternal &&
                    libraryItemDetails &&
                    viewMode === 'chapters' &&
                    libraryItemDetails.chapters &&
                    libraryItemDetails.chapters.length
                  "
                >
                  <!-- Enhanced Chapter Cards for better UX -->
                  <ul
                    role="list"
                    class="divide-y divide-gray-200 dark:divide-dark-600 mb-6"
                  >
                    <EnhancedChapterCard
                      v-for="chapter in paginatedLibraryChapters"
                      :key="chapter.id"
                      :chapter="chapter"
                      @read-chapter="readChapter"
                      @download-chapter="downloadChapter"
                      @redownload-chapter="redownloadChapter"
                      @delete-chapter="deleteChapter"
                    />
                  </ul>
                  <!-- Pagination Info -->
                  <div class="flex justify-between items-center mb-4">
                    <p class="text-sm text-gray-700 dark:text-gray-300">
                      Showing {{ paginationInfo.start }}-{{
                        paginationInfo.end
                      }}
                      of {{ paginationInfo.total }} chapters
                    </p>
                    <div class="flex items-center space-x-2">
                      <button
                        @click="prevPage"
                        :disabled="currentPage === 1"
                        class="px-3 py-1 text-sm border border-gray-300 dark:border-dark-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-dark-700"
                      >
                        Previous
                      </button>
                      <span class="text-sm text-gray-700 dark:text-gray-300">
                        Page {{ currentPage }} of {{ totalPages }}
                      </span>
                      <button
                        @click="nextPage"
                        :disabled="currentPage === totalPages"
                        class="px-3 py-1 text-sm border border-gray-300 dark:border-dark-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-dark-700"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Basic chapters for external manga -->
                <ul
                  v-else
                  role="list"
                  class="divide-y divide-gray-200 dark:divide-dark-600"
                >
                  <li
                    v-for="chapter in sortedChapters"
                    :key="chapter.id"
                    class="py-4 flex items-center justify-between"
                  >
                    <div class="flex items-center">
                      <div class="flex-1">
                        <p
                          class="text-sm font-medium text-gray-900 dark:text-white"
                        >
                          Chapter {{ chapter.number
                          }}{{ chapter.title ? `: ${chapter.title}` : "" }}
                        </p>
                        <div class="flex items-center space-x-3 mt-1">
                          <p
                            v-if="
                              chapter.publish_at ||
                              chapter.readable_at ||
                              chapter.upload_date ||
                              chapter.release_date ||
                              chapter.created_at ||
                              chapter.updated_at
                            "
                            class="text-xs text-gray-500 dark:text-gray-400"
                          >
                            📅
                            {{
                              formatDate(
                                chapter.publish_at ||
                                  chapter.readable_at ||
                                  chapter.upload_date ||
                                  chapter.release_date ||
                                  chapter.created_at ||
                                  chapter.updated_at,
                              )
                            }}
                          </p>
                          <p
                            v-if="chapter.pages_count || chapter.pages"
                            class="text-xs text-gray-500 dark:text-gray-400"
                          >
                            📄 {{ chapter.pages_count || chapter.pages }} pages
                          </p>
                          <p
                            v-if="chapter.language && chapter.language !== 'en'"
                            class="text-xs text-gray-500 dark:text-gray-400"
                          >
                            🌐 {{ chapter.language.toUpperCase() }}
                          </p>
                          <p
                            v-if="chapter.source || (manga && manga.provider)"
                            class="text-xs text-blue-600 dark:text-blue-400 font-medium"
                          >
                            {{ chapter.source || manga.provider }}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div class="flex items-center space-x-2">
                      <button
                        @click="readChapter(chapter.id)"
                        class="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                      >
                        Read
                      </button>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
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
          :manga="manga"
          @close="showImportDialog = false"
          @imported="onMangaImported"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useLibraryStore } from "../stores/library";
import { useSettingsStore } from "../stores/settings";
import { useDownloadsStore } from "../stores/downloads";
import EnhancedChapterCard from "../components/EnhancedChapterCard.vue";
import ChapterFilters from "../components/ChapterFilters.vue";
import ChapterManagement from "../components/ChapterManagement.vue";
import VolumeDownloadCard from "../components/VolumeDownloadCard.vue";
import ImportDialog from "../components/ImportDialog.vue";

import api from "../services/api";
import imageProxy from "../utils/imageProxy";

const route = useRoute();
const router = useRouter();
const libraryStore = useLibraryStore();
const settingsStore = useSettingsStore();
const downloadsStore = useDownloadsStore();

const mangaId = computed(() => route.params.id);
const provider = computed(() => route.params.provider);
const isExternal = computed(() => !!provider.value);

const manga = ref(null);
const loading = ref(true);
const error = ref(null);
const inLibrary = ref(false);
const chapterSort = ref("desc");
const libraryItemDetails = ref(null);
const providerChapters = ref([]);
const chapterFilters = ref({
  language: "",
  volume: "",
  downloadStatus: "",
  readingStatus: "",
});
const viewMode = ref("chapters"); // "chapters" or "volumes"
const showImportDialog = ref(false);

const currentPage = ref(1);
const chaptersPerPage = 10;

// Bulk download progress state
const bulkDownloadProgress = ref({
  isDownloading: false,
  progress: 0,
  completedChapters: 0,
  totalChapters: 0,
  downloadId: null,
});

// Check for existing bulk download from downloads store
const activeBulkDownload = computed(() => {
  const bulkDownloads = Array.from(downloadsStore.bulkDownloads.values());
  return bulkDownloads.find(
    (download) =>
      download.manga_id === mangaId.value &&
      (download.status === "downloading" || download.status === "queued"),
  );
});

// Update local progress from downloads store
const updateBulkProgressFromStore = () => {
  const activeBulk = activeBulkDownload.value;
  if (activeBulk) {
    bulkDownloadProgress.value = {
      isDownloading: true,
      progress: activeBulk.progress || 0,
      completedChapters: activeBulk.completed_chapters || 0,
      totalChapters: activeBulk.total_chapters || 0,
      downloadId: activeBulk.id,
    };
  } else {
    // Check if there's an active download in the activeDownloads
    const activeDownloads = Array.from(downloadsStore.activeDownloads.values());
    const mangaBulkDownload = activeDownloads.find(
      (download) =>
        download.manga_id === mangaId.value && download.type === "bulk",
    );

    if (mangaBulkDownload) {
      bulkDownloadProgress.value = {
        isDownloading: true,
        progress: mangaBulkDownload.progress || 0,
        completedChapters: mangaBulkDownload.completed_chapters || 0,
        totalChapters: mangaBulkDownload.total_chapters || 0,
        downloadId: mangaBulkDownload.task_id,
      };
    } else {
      bulkDownloadProgress.value.isDownloading = false;
    }
  }
};

// Watch for changes in downloads store to update bulk progress
watch(
  () => [downloadsStore.activeDownloads, downloadsStore.bulkDownloads],
  () => {
    updateBulkProgressFromStore();
  },
  { deep: true },
);

// Chapter update settings (from settings store)
const autoRefreshInterval = computed(
  () => settingsStore.getChapterAutoRefreshInterval,
);
const checkOnTabFocus = computed(() => settingsStore.getChapterCheckOnTabFocus);
const showUpdateNotifications = computed(
  () => settingsStore.getChapterShowUpdateNotifications,
);
const enableManualRefresh = computed(
  () => settingsStore.getChapterEnableManualRefresh,
);

// Update tracking
const lastUpdateTime = ref(null);
const isRefreshing = ref(false);
const newChaptersCount = ref(0);
const autoRefreshTimer = ref(null);
const showUpdateNotification = ref(false);
const rateLimitStatus = ref(null);
const isDiscoveringAlternatives = ref(false);

const isNsfw = computed(() => manga.value?.is_nsfw || manga.value?.is_explicit);
const blurNsfw = computed(() => settingsStore.getNsfwBlur);

// Deduplicate chapters by number, keeping the one with most complete information
const deduplicatedChapters = computed(() => {
  if (!manga.value?.chapters) return [];

  const chapterMap = new Map();

  manga.value.chapters.forEach((chapter) => {
    const chapterNum = chapter.number;
    const existing = chapterMap.get(chapterNum);

    if (!existing) {
      chapterMap.set(chapterNum, chapter);
    } else {
      // Keep the chapter with more complete information
      const currentScore = getChapterScore(chapter);
      const existingScore = getChapterScore(existing);

      if (currentScore > existingScore) {
        chapterMap.set(chapterNum, chapter);
      }
    }
  });

  return Array.from(chapterMap.values());
});

const sortedChapters = computed(() => {
  return [...deduplicatedChapters.value].sort((a, b) => {
    const aNum = parseFloat(a.number) || 0;
    const bNum = parseFloat(b.number) || 0;

    if (chapterSort.value === "asc") {
      return aNum - bNum;
    } else {
      return bNum - aNum;
    }
  });
});

const sortedProviderChapters = computed(() => {
  if (!providerChapters.value) return [];

  // First deduplicate chapters by number
  const chapterMap = new Map();
  providerChapters.value.forEach((chapter) => {
    const chapterNum = chapter.number;
    const existing = chapterMap.get(chapterNum);

    if (!existing) {
      chapterMap.set(chapterNum, chapter);
    } else {
      // Keep the chapter with more complete information
      const currentScore = getChapterScore(chapter);
      const existingScore = getChapterScore(existing);

      if (currentScore > existingScore) {
        chapterMap.set(chapterNum, chapter);
      }
    }
  });

  // Then sort the deduplicated chapters
  return Array.from(chapterMap.values()).sort((a, b) => {
    const aNum = parseFloat(a.number) || 0;
    const bNum = parseFloat(b.number) || 0;

    if (chapterSort.value === "asc") {
      return aNum - bNum;
    } else {
      return bNum - aNum;
    }
  });
});

const paginatedProviderChapters = computed(() => {
  const startIndex = (currentPage.value - 1) * chaptersPerPage;
  const endIndex = startIndex + chaptersPerPage;
  return sortedProviderChapters.value.slice(startIndex, endIndex);
});

const totalPages = computed(() => {
  // Use library chapters for internal manga, provider chapters for external manga
  const chaptersLength = isExternal.value
    ? sortedProviderChapters.value.length
    : sortedEnhancedChapters.value.length;
  return Math.ceil(chaptersLength / chaptersPerPage);
});

const paginationInfo = computed(() => {
  // Use library chapters for internal manga, provider chapters for external manga
  const chaptersLength = isExternal.value
    ? sortedProviderChapters.value.length
    : sortedEnhancedChapters.value.length;

  const start = (currentPage.value - 1) * chaptersPerPage + 1;
  const end = Math.min(currentPage.value * chaptersPerPage, chaptersLength);
  const total = chaptersLength;
  return { start, end, total };
});

const availableLanguages = computed(() => {
  if (!libraryItemDetails.value?.chapters) return [];

  const languages = new Set();
  libraryItemDetails.value.chapters.forEach((chapter) => {
    if (chapter.language) {
      languages.add(chapter.language);
    }
  });

  return Array.from(languages).sort();
});

const availableVolumes = computed(() => {
  if (!libraryItemDetails.value?.chapters) return [];

  const volumes = new Set();
  libraryItemDetails.value.chapters.forEach((chapter) => {
    if (chapter.volume) {
      volumes.add(chapter.volume);
    }
  });

  return Array.from(volumes).sort((a, b) => {
    const aNum = parseFloat(a) || 0;
    const bNum = parseFloat(b) || 0;
    return aNum - bNum;
  });
});

const sortedEnhancedChapters = computed(() => {
  // Use unified chapters if available, fallback to library chapters
  const chaptersToUse =
    providerChapters.value?.length > 0
      ? providerChapters.value
      : libraryItemDetails.value?.chapters || [];

  if (chaptersToUse.length === 0) return [];

  // First deduplicate chapters by number
  const chapterMap = new Map();
  chaptersToUse.forEach((chapter) => {
    const chapterNum = chapter.number;
    const existing = chapterMap.get(chapterNum);

    if (!existing) {
      chapterMap.set(chapterNum, chapter);
    } else {
      // Keep the chapter with more complete information
      const currentScore = getChapterScore(chapter);
      const existingScore = getChapterScore(existing);

      if (currentScore > existingScore) {
        chapterMap.set(chapterNum, chapter);
      }
    }
  });

  let chapters = Array.from(chapterMap.values());

  // Apply filters
  if (chapterFilters.value.language) {
    chapters = chapters.filter(
      (chapter) => chapter.language === chapterFilters.value.language,
    );
  }

  if (chapterFilters.value.volume) {
    chapters = chapters.filter(
      (chapter) => chapter.volume === chapterFilters.value.volume,
    );
  }

  if (chapterFilters.value.downloadStatus) {
    chapters = chapters.filter((chapter) => {
      switch (chapterFilters.value.downloadStatus) {
        case "downloaded":
          return chapter.download_status === "downloaded";
        case "not_downloaded":
          return chapter.download_status === "not_downloaded";
        case "error":
          return chapter.download_status === "error";
        default:
          return true;
      }
    });
  }

  if (chapterFilters.value.readingStatus) {
    chapters = chapters.filter((chapter) => {
      const progress = chapter.reading_progress;
      switch (chapterFilters.value.readingStatus) {
        case "unread":
          return !progress;
        case "in_progress":
          return progress && !progress.is_completed;
        case "completed":
          return progress && progress.is_completed;
        default:
          return true;
      }
    });
  }

  // Sort chapters
  return chapters.sort((a, b) => {
    const aNum = parseFloat(a.number) || 0;
    const bNum = parseFloat(b.number) || 0;

    if (chapterSort.value === "asc") {
      return aNum - bNum;
    } else {
      return bNum - aNum;
    }
  });
});

const paginatedAllProviderChapters = computed(() => {
  if (!providerChapters.value) return [];

  const startIndex = (currentPage.value - 1) * chaptersPerPage;
  const endIndex = startIndex + chaptersPerPage;

  return providerChapters.value.slice(startIndex, endIndex);
});

const paginatedLibraryChapters = computed(() => {
  if (!sortedEnhancedChapters.value) return [];

  const startIndex = (currentPage.value - 1) * chaptersPerPage;
  const endIndex = startIndex + chaptersPerPage;

  return sortedEnhancedChapters.value.slice(startIndex, endIndex);
});

const groupedVolumes = computed(() => {
  if (!libraryItemDetails.value?.chapters) return [];

  const volumeMap = new Map();

  libraryItemDetails.value.chapters.forEach((chapter) => {
    const volumeNumber = chapter.volume || "Unknown";

    if (!volumeMap.has(volumeNumber)) {
      volumeMap.set(volumeNumber, {
        number: volumeNumber,
        chapters: [],
        language: chapter.language,
      });
    }

    volumeMap.get(volumeNumber).chapters.push(chapter);
  });

  // Sort volumes and chapters within each volume
  const volumes = Array.from(volumeMap.values()).sort((a, b) => {
    const aNum = parseFloat(a.number) || 0;
    const bNum = parseFloat(b.number) || 0;
    return aNum - bNum;
  });

  volumes.forEach((volume) => {
    volume.chapters.sort((a, b) => {
      const aNum = parseFloat(a.number) || 0;
      const bNum = parseFloat(b.number) || 0;
      return aNum - bNum;
    });
  });

  return volumes;
});

const getCoverUrl = (mangaId) => {
  // For external manga, use the image proxy utility
  if (isExternal.value && manga.value) {
    return imageProxy.getCoverUrl(manga.value, mangaId);
  }
  // For internal manga, use the cover endpoint
  return `/api/v1/manga/${mangaId}/cover`;
};

const fetchMangaDetails = async () => {
  loading.value = true;
  error.value = null;

  try {
    let response;
    if (isExternal.value) {
      // For external manga, use the external endpoint
      response = await api.get(
        `/v1/manga/external/${provider.value}/${mangaId.value}`,
      );
    } else {
      // For internal manga, use the regular endpoint
      response = await api.get(`/v1/manga/${mangaId.value}`);
    }

    manga.value = response.data;

    // Check if manga is in library and load enhanced details
    if (isExternal.value) {
      // For external manga, check if it exists in library by provider and external_id
      await checkExternalLibraryStatus();
      if (inLibrary.value) {
        await loadLibraryItemDetails();
        // Load chapters from provider to show all available chapters
        await loadProviderChapters();
      }
    } else {
      // For library items, load enhanced details
      await checkLibraryStatus();
      if (inLibrary.value) {
        await loadLibraryItemDetails();
        // Load chapters from provider to show all available chapters
        await loadProviderChapters();
      }
    }
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to load manga details";
    console.error("Error fetching manga details:", err);
  } finally {
    loading.value = false;
    // Fetch rate limit status after manga details are loaded
    fetchRateLimitStatus();
  }
};

const checkLibraryStatus = async () => {
  try {
    const response = await api.get(`/v1/library/check/${mangaId.value}`);
    inLibrary.value = response.data.in_library;
  } catch (err) {
    console.error("Error checking library status:", err);
  }
};

const checkExternalLibraryStatus = async () => {
  try {
    const response = await api.get("/v1/library/check-external", {
      params: {
        provider: provider.value,
        external_id: mangaId.value,
      },
    });
    inLibrary.value = response.data.in_library;
    // If it's in library, update mangaId to the local manga ID for subsequent operations
    if (response.data.in_library && response.data.manga_id) {
      // Store the original external ID for provider operations
      const originalExternalId = mangaId.value;
      // Update mangaId to the local manga ID for library operations
      mangaId.value = response.data.manga_id;
      // Store external ID for provider operations
      manga.value = { ...manga.value, external_id: originalExternalId };
    }
  } catch (err) {
    console.error("Error checking external library status:", err);
    inLibrary.value = false;
  }
};

const loadLibraryItemDetails = async () => {
  try {
    // Find the library item ID for this manga
    const libraryResponse = await api.get("/v1/library", {
      params: { manga_id: mangaId.value },
    });

    if (libraryResponse.data.items && libraryResponse.data.items.length > 0) {
      const libraryItemId = libraryResponse.data.items[0].id;
      libraryItemDetails.value =
        await libraryStore.fetchLibraryItemDetailed(libraryItemId);
    }
  } catch (err) {
    console.error("Error loading library item details:", err);
  }
};

// Unified Chapter Data Structure
const createUnifiedChapter = (
  databaseChapter,
  providerChapter,
  libraryChapter,
) => {
  // Database chapter is the source of truth for IDs and core data
  const unified = {
    // Core identifiers (always from database)
    id: databaseChapter?.id || null,
    library_chapter_id: databaseChapter?.id || null,

    // Core metadata (prefer database, fallback to provider)
    title:
      databaseChapter?.title || providerChapter?.title || "Unknown Chapter",
    number: databaseChapter?.number || providerChapter?.number || "Unknown",
    volume: databaseChapter?.volume || providerChapter?.volume || null,
    language: databaseChapter?.language || providerChapter?.language || "en",

    // Database-specific fields
    download_status:
      libraryChapter?.download_status ||
      databaseChapter?.download_status ||
      "not_downloaded",
    file_path: databaseChapter?.file_path || null,
    file_size: databaseChapter?.file_size || null,
    pages_count: databaseChapter?.pages_count || 0,
    created_at: databaseChapter?.created_at || null,
    updated_at: databaseChapter?.updated_at || null,

    // Provider-specific fields
    external_id: databaseChapter?.external_id || providerChapter?.id || null,
    provider_id: providerChapter?.id || null,
    provider_url: providerChapter?.url || null,
    available_on_provider: !!providerChapter,

    // Enhanced fields
    reading_progress: libraryChapter?.reading_progress || null,
    publish_at:
      databaseChapter?.publish_at || providerChapter?.publish_at || null,
    readable_at:
      databaseChapter?.readable_at || providerChapter?.readable_at || null,

    // Fallback provider support
    provider_external_ids: databaseChapter?.provider_external_ids || {},
    fallback_providers: databaseChapter?.fallback_providers || [],

    // Source tracking
    source: databaseChapter ? "database" : "provider",
    has_database_entry: !!databaseChapter,
    has_provider_entry: !!providerChapter,
    has_library_entry: !!libraryChapter,
  };

  return unified;
};

const mergeChapterSources = (
  databaseChapters = [],
  providerChapters = [],
  libraryChapters = [],
) => {
  console.log("Merging chapter sources:", {
    database: databaseChapters.length,
    provider: providerChapters.length,
    library: libraryChapters.length,
  });

  const unifiedChapters = [];
  const processedNumbers = new Set();

  // First pass: Process database chapters (primary source)
  databaseChapters.forEach((dbChapter) => {
    const libraryChapter = libraryChapters.find((lc) => lc.id === dbChapter.id);
    const providerChapter = providerChapters.find(
      (pc) =>
        pc.external_id === dbChapter.external_id ||
        pc.id === dbChapter.external_id ||
        pc.title === dbChapter.title ||
        pc.number === dbChapter.number,
    );

    const unified = createUnifiedChapter(
      dbChapter,
      providerChapter,
      libraryChapter,
    );
    unifiedChapters.push(unified);
    processedNumbers.add(dbChapter.number);
  });

  // Second pass: Add provider-only chapters (not in database)
  providerChapters.forEach((providerChapter) => {
    if (!processedNumbers.has(providerChapter.number)) {
      const unified = createUnifiedChapter(null, providerChapter, null);
      unifiedChapters.push(unified);
      processedNumbers.add(providerChapter.number);
    }
  });

  console.log("Unified chapters created:", unifiedChapters.length);
  return unifiedChapters;
};

const loadProviderChapters = async () => {
  try {
    if (!manga.value?.provider || !manga.value?.external_id) {
      console.log("No provider information available");
      return;
    }

    // Get chapters from the provider
    const response = await api.get(
      `/v1/providers/${manga.value.provider}/manga/${manga.value.external_id}`,
    );

    if (response.data.chapters) {
      // Get all data sources
      const databaseChapters = manga.value?.chapters || [];
      const providerChaptersData = response.data.chapters || [];
      const libraryChapters = libraryItemDetails.value?.chapters || [];

      // Create unified chapters using the merger function
      const unifiedChapters = mergeChapterSources(
        databaseChapters,
        providerChaptersData,
        libraryChapters,
      );

      // Store unified chapters
      providerChapters.value = unifiedChapters;

      console.log("Unified chapters loaded:", {
        total: unifiedChapters.length,
        withDatabase: unifiedChapters.filter((c) => c.has_database_entry)
          .length,
        withProvider: unifiedChapters.filter((c) => c.has_provider_entry)
          .length,
        withLibrary: unifiedChapters.filter((c) => c.has_library_entry).length,
      });

      // Update last refresh time
      if (!lastUpdateTime.value) {
        lastUpdateTime.value = new Date();
      }
    }
  } catch (error) {
    console.error("Error loading provider chapters:", error);
  }
};

const addToLibrary = async () => {
  try {
    let actualMangaId = mangaId.value;

    // If this is an external manga, create a local record first
    if (isExternal.value) {
      const response = await api.post(
        "/v1/manga/from-external",
        {},
        {
          params: {
            provider: provider.value,
            external_id: mangaId.value,
          },
        },
      );
      actualMangaId = response.data.id;
    }

    await libraryStore.addToLibrary(actualMangaId);
    inLibrary.value = true;
  } catch (err) {
    console.error("Error adding to library:", err);

    // Handle detailed error response (like duplicate manga)
    const errorDetail = err.response?.data?.detail;
    let errorMessage = "Failed to add manga to library";

    if (typeof errorDetail === "object" && errorDetail.message) {
      // Handle structured error response (duplicate manga)
      errorMessage =
        `${errorDetail.message} ${errorDetail.suggestion || ""}`.trim();
    } else if (typeof errorDetail === "string") {
      // Handle simple string error
      errorMessage = `Failed to add manga to library: ${errorDetail}`;
    } else if (err.message) {
      // Fallback to error message
      errorMessage = `Failed to add manga to library: ${err.message}`;
    }

    alert(errorMessage);
  }
};

const removeFromLibrary = async () => {
  if (
    confirm("Are you sure you want to remove this manga from your library?")
  ) {
    try {
      // Find the library item ID for this manga
      const libraryResponse = await api.get("/v1/library", {
        params: { manga_id: mangaId.value },
      });

      if (
        !libraryResponse.data.items ||
        libraryResponse.data.items.length === 0
      ) {
        throw new Error("Manga not found in library");
      }

      const libraryItemId = libraryResponse.data.items[0].id;
      await libraryStore.removeFromLibrary(libraryItemId);
      inLibrary.value = false;
    } catch (err) {
      console.error("Error removing from library:", err);
    }
  }
};

const startReading = () => {
  if (manga.value?.chapters && manga.value.chapters.length > 0) {
    const firstChapter =
      sortedChapters.value[
        chapterSort.value === "asc" ? 0 : sortedChapters.value.length - 1
      ];
    readChapter(firstChapter.id);
  }
};

const readChapter = (chapterOrId) => {
  const chapterId =
    typeof chapterOrId === "object" ? chapterOrId.id : chapterOrId;
  router.push(`/read/${mangaId.value}/${chapterId}`);
};

const updateChapterFilters = (newFilters) => {
  chapterFilters.value = { ...newFilters };
};

const downloadVolume = async (volumeData) => {
  try {
    // Import downloads store
    const { useDownloadsStore } = await import("../stores/downloads");
    const downloadsStore = useDownloadsStore();

    const libraryResponse = await api.get("/v1/library", {
      params: { manga_id: mangaId.value },
    });

    if (
      !libraryResponse.data.items ||
      libraryResponse.data.items.length === 0
    ) {
      throw new Error("Manga not found in library");
    }

    const libraryItemId = libraryResponse.data.items[0].id;

    // Create bulk download tracking
    const bulkId = `volume_${volumeData.number}_${Date.now()}`;
    const chaptersToDownload = volumeData.chapters.filter(
      (chapter) => chapter.download_status !== "downloaded",
    );

    if (chaptersToDownload.length === 0) {
      alert("All chapters in this volume are already downloaded");
      return;
    }

    downloadsStore.startBulkDownload(
      bulkId,
      mangaId.value,
      chaptersToDownload.length,
    );

    // Download all chapters in the volume
    for (const chapter of chaptersToDownload) {
      try {
        // Determine the correct external chapter ID
        const externalChapterId = chapter.external_id || chapter.id;

        const result = await libraryStore.downloadChapter(
          libraryItemId,
          chapter.library_chapter_id || null,
          manga.value.provider || "mangadex",
          manga.value.external_id || mangaId.value,
          externalChapterId, // Use the correct external chapter ID
        );

        // Track chapter download in bulk download
        if (result.task_id) {
          downloadsStore.updateBulkDownloadProgress(
            bulkId,
            result.task_id,
            "started",
          );
        }
      } catch (chapterError) {
        console.error(`Error downloading chapter ${chapter.id}:`, chapterError);
        downloadsStore.updateBulkDownloadProgress(bulkId, null, "failed");
      }
    }

    // Reload library item details to update download status
    await loadLibraryItemDetails();

    console.log("Volume download started successfully");
  } catch (err) {
    console.error("Error downloading volume:", err);
    alert(
      "Failed to download volume: " +
        (err.response?.data?.detail || err.message),
    );
  }
};

const retryFailedChapters = async (volumeData) => {
  try {
    const libraryResponse = await api.get("/v1/library", {
      params: { manga_id: mangaId.value },
    });

    if (
      !libraryResponse.data.items ||
      libraryResponse.data.items.length === 0
    ) {
      throw new Error("Manga not found in library");
    }

    const libraryItemId = libraryResponse.data.items[0].id;

    // Retry failed chapters in the volume
    for (const chapter of volumeData.chapters) {
      if (chapter.download_status === "error") {
        // Determine the correct external chapter ID
        const externalChapterId = chapter.external_id || chapter.id;

        await libraryStore.downloadChapter(
          libraryItemId,
          chapter.library_chapter_id || null,
          manga.value.provider || "mangadex",
          manga.value.external_id || mangaId.value,
          externalChapterId, // Use the correct external chapter ID
        );
      }
    }

    // Reload library item details to update download status
    await loadLibraryItemDetails();

    console.log("Failed chapters retry started successfully");
  } catch (err) {
    console.error("Error retrying failed chapters:", err);
    alert(
      "Failed to retry chapters: " +
        (err.response?.data?.detail || err.message),
    );
  }
};

const downloadManga = async () => {
  try {
    // First, we need to add the manga to library if it's not already there
    if (!inLibrary.value) {
      await addToLibrary();
    }

    // Get the library item ID
    const libraryResponse = await api.get("/v1/library", {
      params: { manga_id: mangaId.value },
    });
    const libraryItem = libraryResponse.data.items?.[0];

    if (!libraryItem) {
      throw new Error("Manga not found in library");
    }

    // Initialize bulk download progress
    const totalChapters = manga.value?.chapters?.length || 0;
    bulkDownloadProgress.value = {
      isDownloading: true,
      progress: 0,
      completedChapters: 0,
      totalChapters: totalChapters,
      downloadId: `bulk_${libraryItem.id}_${Date.now()}`,
    };

    // Import downloads store
    const { useDownloadsStore } = await import("../stores/downloads");
    const downloadsStore = useDownloadsStore();

    // Add to downloads store for tracking
    downloadsStore.addBulkDownload({
      id: bulkDownloadProgress.value.downloadId,
      manga_title: manga.value.title,
      manga_id: mangaId.value,
      type: "bulk",
      status: "downloading",
      progress: 0,
      total_chapters: totalChapters,
      completed_chapters: 0,
      started_at: new Date().toISOString(),
    });

    // Start the download
    const downloadResponse = await api.post(
      `/v1/library/${libraryItem.id}/download`,
      {},
      {
        params: {
          provider: manga.value.provider || "mangadex",
          external_id: manga.value.external_id || mangaId.value,
        },
      },
    );

    console.log("Download response:", downloadResponse.data);

    // Update bulk download with real task ID
    if (downloadResponse.data.task_id) {
      bulkDownloadProgress.value.downloadId = downloadResponse.data.task_id;

      // Update downloads store with real task ID
      downloadsStore.updateBulkDownloadProgress(
        downloadResponse.data.task_id,
        null,
        "downloading",
        0,
        0,
      );
    }

    alert("Download started! Check your downloads page for progress.");
  } catch (err) {
    console.error("Error downloading manga:", err);
    bulkDownloadProgress.value.isDownloading = false;
    alert(
      "Failed to download manga: " +
        (err.response?.data?.detail || err.message),
    );
  }
};

const downloadChapter = async (chapter) => {
  console.log("downloadChapter called with:", chapter);
  try {
    if (!libraryItemDetails.value) {
      throw new Error("Library item details not available");
    }

    // Find the library item ID
    const libraryResponse = await api.get("/v1/library", {
      params: { manga_id: mangaId.value },
    });

    if (
      !libraryResponse.data.items ||
      libraryResponse.data.items.length === 0
    ) {
      throw new Error("Manga not found in library");
    }

    const libraryItemId = libraryResponse.data.items[0].id;
    console.log("Library item ID:", libraryItemId);
    console.log("Unified chapter data:", {
      id: chapter.id,
      library_chapter_id: chapter.library_chapter_id,
      external_id: chapter.external_id,
      provider_id: chapter.provider_id,
      source: chapter.source,
      has_database_entry: chapter.has_database_entry,
      provider: manga.value.provider,
    });

    // For unified chapters, always use the database chapter ID if available
    // The external_id should be used for provider communication
    const chapterIdToUse = chapter.has_database_entry ? chapter.id : null;
    const externalChapterId =
      chapter.external_id || chapter.provider_id || chapter.id;

    // Only download if we have a database chapter (in library)
    if (!chapter.has_database_entry) {
      throw new Error(
        "Chapter not in library. Please add manga to library first.",
      );
    }

    const downloadResult = await libraryStore.downloadChapter(
      libraryItemId,
      chapterIdToUse, // Use database chapter ID
      manga.value.provider || "mangadex",
      manga.value.external_id || mangaId.value,
      externalChapterId, // Use the correct external chapter ID
    );

    console.log("Download result:", downloadResult);

    // The library store already adds the download to the downloads store
    // Real progress updates will come from WebSocket connections

    // Reload library item details to update download status
    await loadLibraryItemDetails();

    console.log("Chapter download started successfully");
  } catch (err) {
    console.error("Error downloading chapter:", err);
    alert(
      "Failed to download chapter: " +
        (err.response?.data?.detail || err.message),
    );
  }
};

const downloadProviderChapter = async (chapter) => {
  try {
    // Find the library item ID
    const libraryResponse = await api.get("/v1/library", {
      params: { manga_id: mangaId.value },
    });

    if (
      !libraryResponse.data.items ||
      libraryResponse.data.items.length === 0
    ) {
      throw new Error("Manga not found in library");
    }

    const libraryItemId = libraryResponse.data.items[0].id;

    // Download the specific chapter from provider
    await libraryStore.downloadChapter(
      libraryItemId,
      null, // No existing chapter ID
      manga.value.provider,
      manga.value.external_id,
      chapter.id, // Provider chapter ID
    );

    // Reload library item details and provider chapters to update download status
    await loadLibraryItemDetails();
    await loadProviderChapters();

    console.log("Provider chapter download started successfully");
  } catch (err) {
    console.error("Error downloading provider chapter:", err);
    alert(
      "Failed to download chapter: " +
        (err.response?.data?.detail || err.message),
    );
  }
};

const formatDate = (dateString) => {
  if (!dateString) return "N/A";

  const date = new Date(dateString);
  const now = new Date();
  const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

  // For recent dates (within 7 days), show relative time
  if (diffInDays === 0) {
    return (
      new Intl.DateTimeFormat("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      }).format(date) + " today"
    );
  } else if (diffInDays === 1) {
    return (
      new Intl.DateTimeFormat("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      }).format(date) + " yesterday"
    );
  } else if (diffInDays <= 7) {
    return new Intl.DateTimeFormat("en-US", {
      weekday: "short",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    }).format(date);
  } else {
    // For older dates, show full date
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(date);
  }
};

// Helper function to score chapters based on completeness of information
const getChapterScore = (chapter) => {
  let score = 0;
  if (chapter.title) score += 3; // Title is most important
  if (chapter.pages_count || chapter.pages) score += 2; // Page count is important
  if (chapter.publish_at || chapter.readable_at) score += 2; // Release dates are very important
  if (
    chapter.upload_date ||
    chapter.release_date ||
    chapter.created_at ||
    chapter.updated_at
  )
    score += 1; // Other dates
  if (chapter.source) score += 1; // Source information
  if (chapter.language && chapter.language !== "unknown") score += 1; // Language info
  if (chapter.volume) score += 1; // Volume information

  return score;
};

const formatDescription = (description) => {
  if (!description) return "";

  // Convert newlines to <br> tags
  return description.replace(/\n/g, "<br>");
};

const onImageError = (event) => {
  // Hide the image if it fails to load
  event.target.style.display = "none";
  console.warn(
    `Failed to load cover image for ${manga.value?.title}: ${event.target.src}`,
  );
};

const onMangaImported = () => {
  showImportDialog.value = false;
  // Refresh manga details to show newly imported chapters
  fetchMangaDetails();
  if (!isExternal.value) {
    loadLibraryItemDetails();
  }
};

const redownloadChapter = async (chapter) => {
  try {
    await api.post(`/v1/chapters/${chapter.id}/redownload`);
    alert("Re-download started! The chapter will be downloaded again.");
    await refreshMangaDetails();
  } catch (error) {
    console.error("Error re-downloading chapter:", error);
    alert(
      "Failed to re-download chapter: " +
        (error.response?.data?.detail || error.message),
    );
  }
};

const deleteChapter = async (chapter) => {
  try {
    await api.delete(`/v1/chapters/${chapter.id}`);
    alert("Chapter deleted successfully!");
    // Refresh both manga details and library item details to update UI
    await refreshMangaDetails();
    if (!isExternal.value && inLibrary.value) {
      await loadLibraryItemDetails();
    }
  } catch (error) {
    console.error("Error deleting chapter:", error);
    alert(
      "Failed to delete chapter: " +
        (error.response?.data?.detail || error.message),
    );
  }
};

const refreshMangaDetails = async () => {
  await fetchMangaDetails();
  if (!isExternal.value && inLibrary.value) {
    await loadProviderChapters();
  }
};

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
  }
};

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
  }
};

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
  }
};

// Chapter update functions
const manualRefreshChapters = async () => {
  if (isRefreshing.value) return;

  isRefreshing.value = true;
  try {
    const previousCount = providerChapters.value.length;
    await loadProviderChapters();
    const newCount = providerChapters.value.length;

    lastUpdateTime.value = new Date();

    if (newCount > previousCount && showUpdateNotifications.value) {
      newChaptersCount.value = newCount - previousCount;
      showUpdateNotification.value = true;

      // Auto-hide notification after 5 seconds
      setTimeout(() => {
        showUpdateNotification.value = false;
      }, 5000);
    }
  } catch (error) {
    console.error("Error refreshing chapters:", error);
  } finally {
    isRefreshing.value = false;
  }
};

const startAutoRefresh = () => {
  if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value);
  }

  if (autoRefreshInterval.value > 0 && !isExternal.value && inLibrary.value) {
    autoRefreshTimer.value = setInterval(() => {
      manualRefreshChapters();
    }, autoRefreshInterval.value * 1000);
  }
};

const stopAutoRefresh = () => {
  if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value);
    autoRefreshTimer.value = null;
  }
};

const handleVisibilityChange = () => {
  if (document.hidden) {
    // Tab is hidden, stop auto-refresh to save resources
    stopAutoRefresh();
  } else {
    // Tab is visible again
    if (checkOnTabFocus.value && !isExternal.value && inLibrary.value) {
      // Check for updates when tab becomes active
      manualRefreshChapters();
    }
    // Restart auto-refresh
    startAutoRefresh();
  }
};

// Navigate to Settings > Media Management
const goToMediaManagement = () => {
  router.push("/settings?tab=media");
};

// Format time remaining for rate limit
const formatTime = (seconds) => {
  if (seconds < 60) {
    return `${seconds} seconds`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes} minute${minutes > 1 ? "s" : ""}`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours} hour${hours > 1 ? "s" : ""}${minutes > 0 ? ` ${minutes} minute${minutes > 1 ? "s" : ""}` : ""}`;
  }
};

// Fetch rate limit status for the provider
const fetchRateLimitStatus = async () => {
  if (!manga.value?.provider) return;

  try {
    const response = await api.get(
      `/v1/providers/${manga.value.provider}/rate-limit-status`,
    );
    rateLimitStatus.value = response.data;

    // If rate limited, set up a timer to refresh the status
    if (response.data.is_rate_limited && response.data.seconds_remaining > 0) {
      setTimeout(
        () => {
          fetchRateLimitStatus();
        },
        Math.min(response.data.seconds_remaining * 1000, 30000),
      ); // Check again in 30 seconds or when limit expires
    }
  } catch (error) {
    console.error("Error fetching rate limit status:", error);
    rateLimitStatus.value = null;
  }
};

// Discover alternative sources for chapters
const discoverAlternatives = async () => {
  if (!manga.value?.id) return;

  isDiscoveringAlternatives.value = true;
  try {
    // Show progress message
    const progressMessage =
      "Searching across multiple providers for alternative sources...";
    console.log(progressMessage);

    const result = await libraryStore.discoverChapterAlternatives(
      manga.value.id,
    );

    if (result.discovered_count > 0) {
      alert(
        `✅ Success! Discovered alternatives for ${result.discovered_count} out of ${result.total_chapters} chapters.\n\nDownloads will now automatically use alternative providers when the primary source fails.`,
      );
    } else {
      alert(
        `ℹ️ No alternatives found for any chapters.\n\nThis might be because:\n• The manga is unique to this provider\n• Chapter titles don't match across providers\n• Alternative providers are currently unavailable`,
      );
    }

    // Refresh manga details to show updated chapter info
    await fetchMangaDetails();
  } catch (error) {
    console.error("Error discovering alternatives:", error);

    if (error.message.includes("timeout")) {
      alert(
        "⏱️ Discovery timed out. This can happen when providers are slow to respond.\n\nTry again later or the system will automatically discover alternatives during downloads.",
      );
    } else {
      alert("❌ Failed to discover alternatives: " + error.message);
    }
  } finally {
    isDiscoveringAlternatives.value = false;
  }
};

onMounted(() => {
  fetchMangaDetails();
  fetchRateLimitStatus();

  // Initialize downloads store if not already initialized
  if (!downloadsStore.pollingInterval) {
    downloadsStore.init();
  }

  // Update bulk download progress from store
  updateBulkProgressFromStore();

  // Set up auto-refresh after initial load
  setTimeout(() => {
    if (!isExternal.value && inLibrary.value) {
      startAutoRefresh();
    }
  }, 1000);

  // Set up visibility change listener for tab focus detection
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onUnmounted(() => {
  // Clean up auto-refresh timer
  stopAutoRefresh();

  // Remove visibility change listener
  document.removeEventListener("visibilitychange", handleVisibilityChange);
});
</script>
