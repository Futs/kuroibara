<template>
  <div class="manga-reader" :class="{ dark: true }">
    <!-- Reader Controls -->
    <div
      class="fixed top-0 left-0 right-0 z-10 bg-white dark:bg-dark-900 bg-opacity-90 dark:bg-opacity-90 shadow-md transition-transform duration-300"
      :class="{ '-translate-y-full': !showControls }"
    >
      <div
        class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2 flex items-center justify-between"
      >
        <div class="flex items-center space-x-4">
          <router-link
            :to="`/manga/${mangaId}`"
            class="p-2 rounded-full text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-800"
          >
            <svg
              class="h-6 w-6"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
          </router-link>

          <div
            class="text-sm sm:text-base font-medium text-gray-900 dark:text-white truncate"
          >
            {{ manga?.title }}
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <button
            @click="toggleSettings"
            class="p-2 rounded-full text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-800"
          >
            <svg
              class="h-6 w-6"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </button>
        </div>
      </div>

      <div
        class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2 flex items-center justify-between border-t border-gray-200 dark:border-dark-700"
      >
        <div class="flex items-center space-x-4">
          <button
            @click="prevChapter"
            :disabled="!hasPrevChapter"
            class="p-2 rounded-full text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-800 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              class="h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
              />
            </svg>
          </button>

          <div class="relative">
            <button
              @click="showChapterSelector = !showChapterSelector"
              class="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-dark-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800 hover:bg-gray-50 dark:hover:bg-dark-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              {{ chapter?.title || "Select Chapter" }}
              <svg
                class="ml-2 -mr-0.5 h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            <div
              v-if="showChapterSelector"
              class="origin-top-left absolute left-0 mt-2 w-56 rounded-md shadow-lg bg-white dark:bg-dark-800 ring-1 ring-black ring-opacity-5 focus:outline-none z-20"
            >
              <div
                class="py-1 max-h-60 overflow-y-auto"
                role="menu"
                aria-orientation="vertical"
                aria-labelledby="options-menu"
              >
                <button
                  v-for="chap in chapters"
                  :key="chap.id"
                  @click="selectChapter(chap.id)"
                  class="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-700"
                  :class="{
                    'bg-gray-100 dark:bg-dark-700': chap.id === chapter?.id,
                  }"
                  role="menuitem"
                >
                  {{ chap.title }}
                </button>
              </div>
            </div>
          </div>

          <button
            @click="nextChapter"
            :disabled="!hasNextChapter"
            class="p-2 rounded-full text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-800 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              class="h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 5l7 7-7 7M5 5l7 7-7 7"
              />
            </svg>
          </button>
        </div>

        <div class="flex items-center space-x-2">
          <span class="text-sm text-gray-700 dark:text-gray-200">
            {{ currentPage }} / {{ totalPages }}
          </span>
        </div>
      </div>
    </div>

    <!-- Reader Settings -->
    <div
      v-if="showSettings"
      class="fixed inset-0 z-20 overflow-y-auto"
      @click.self="showSettings = false"
    >
      <div
        class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
      >
        <div
          class="fixed inset-0 bg-gray-500 dark:bg-dark-900 bg-opacity-75 dark:bg-opacity-75 transition-opacity"
        ></div>

        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6"
        >
          <div>
            <div class="mt-3 text-center sm:mt-0 sm:text-left">
              <h3
                class="text-lg leading-6 font-medium text-gray-900 dark:text-white"
              >
                Reader Settings
              </h3>

              <div class="mt-4 space-y-4">
                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Reading Direction
                  </label>
                  <div class="mt-2 flex space-x-2">
                    <button
                      @click="updateSettings({ readingDirection: 'rtl' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.readingDirection === 'rtl'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Right to Left
                    </button>
                    <button
                      @click="updateSettings({ readingDirection: 'ltr' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.readingDirection === 'ltr'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Left to Right
                    </button>
                  </div>
                </div>

                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Page Layout
                  </label>
                  <div class="mt-2 flex space-x-2">
                    <button
                      @click="updateSettings({ pageLayout: 'single' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.pageLayout === 'single'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Single Page
                    </button>
                    <button
                      @click="updateSettings({ pageLayout: 'double' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.pageLayout === 'double'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Double Page
                    </button>
                  </div>
                </div>

                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Fit Mode
                  </label>
                  <div class="mt-2 flex space-x-2">
                    <button
                      @click="updateSettings({ fitMode: 'width' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.fitMode === 'width'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Fit Width
                    </button>
                    <button
                      @click="updateSettings({ fitMode: 'height' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.fitMode === 'height'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Fit Height
                    </button>
                    <button
                      @click="updateSettings({ fitMode: 'both' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.fitMode === 'both'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Fit Both
                    </button>
                  </div>
                </div>

                <div class="flex items-center justify-between">
                  <label
                    class="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Show Page Numbers
                  </label>
                  <button
                    @click="
                      updateSettings({
                        showPageNumbers: !settings.showPageNumbers,
                      })
                    "
                    class="relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    :class="
                      settings.showPageNumbers
                        ? 'bg-primary-600'
                        : 'bg-gray-200 dark:bg-dark-600'
                    "
                  >
                    <span
                      class="pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200"
                      :class="
                        settings.showPageNumbers
                          ? 'translate-x-5'
                          : 'translate-x-0'
                      "
                    ></span>
                  </button>
                </div>

                <div class="flex items-center justify-between">
                  <label
                    class="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Auto Advance to Next Chapter
                  </label>
                  <button
                    @click="
                      updateSettings({ autoAdvance: !settings.autoAdvance })
                    "
                    class="relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    :class="
                      settings.autoAdvance
                        ? 'bg-primary-600'
                        : 'bg-gray-200 dark:bg-dark-600'
                    "
                  >
                    <span
                      class="pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200"
                      :class="
                        settings.autoAdvance ? 'translate-x-5' : 'translate-x-0'
                      "
                    ></span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-5 sm:mt-6">
            <button
              @click="showSettings = false"
              class="inline-flex justify-center w-full rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Reader Content -->
    <div
      class="reader-content min-h-screen flex items-center justify-center bg-dark-900"
      @click="handleContentClick"
      @mousemove="handleMouseMove"
    >
      <div v-if="loading" class="flex flex-col items-center justify-center">
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
        <p class="mt-4 text-white">Loading...</p>
      </div>

      <div v-else-if="error" class="text-center p-4">
        <div class="inline-block p-4 bg-red-50 dark:bg-red-900 rounded-lg">
          <svg
            class="h-10 w-10 text-red-500 dark:text-red-400 mx-auto"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 class="mt-2 text-lg font-medium text-red-800 dark:text-red-200">
            {{ error }}
          </h3>
          <div class="mt-4">
            <button
              @click="loadContent"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-red-700 dark:text-red-200 bg-red-100 dark:bg-red-800 hover:bg-red-200 dark:hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>

      <div
        v-else-if="currentPageUrl"
        class="reader-page-container max-h-screen overflow-auto"
        :class="{
          'flex justify-center': true,
          'reader-fit-width': settings.fitMode === 'width',
          'reader-fit-height': settings.fitMode === 'height',
          'reader-fit-both': settings.fitMode === 'both',
        }"
      >
        <img
          :src="currentPageUrl"
          :alt="`Page ${currentPage}`"
          class="reader-page"
          :class="{
            'max-w-full':
              settings.fitMode === 'width' || settings.fitMode === 'both',
            'max-h-screen':
              settings.fitMode === 'height' || settings.fitMode === 'both',
          }"
        />

        <div
          v-if="settings.showPageNumbers"
          class="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm"
        >
          {{ currentPage }} / {{ totalPages }}
        </div>
      </div>
    </div>

    <!-- Navigation Buttons -->
    <button
      v-if="settings.readingDirection === 'rtl'"
      @click="nextPage"
      class="fixed top-0 bottom-0 right-0 w-1/3 h-full opacity-0 cursor-pointer z-0"
    ></button>
    <button
      v-if="settings.readingDirection === 'rtl'"
      @click="prevPage"
      class="fixed top-0 bottom-0 left-0 w-1/3 h-full opacity-0 cursor-pointer z-0"
    ></button>

    <button
      v-if="settings.readingDirection === 'ltr'"
      @click="prevPage"
      class="fixed top-0 bottom-0 left-0 w-1/3 h-full opacity-0 cursor-pointer z-0"
    ></button>
    <button
      v-if="settings.readingDirection === 'ltr'"
      @click="nextPage"
      class="fixed top-0 bottom-0 right-0 w-1/3 h-full opacity-0 cursor-pointer z-0"
    ></button>
  </div>
</template>
