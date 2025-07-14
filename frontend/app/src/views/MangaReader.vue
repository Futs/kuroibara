<template>
  <div class="manga-reader" :class="{ dark: true }">
    <!-- Reader Controls -->
    <div
      class="reader-toolbar fixed z-10 shadow-md transition-all duration-300"
      :class="[
        getToolbarClasses(),
        {
          '-translate-y-full': !showControls && currentUILayout.toolbar.position === 'top',
          'translate-y-full': !showControls && currentUILayout.toolbar.position === 'bottom',
          '-translate-x-full': !showControls && currentUILayout.toolbar.position === 'left',
          'translate-x-full': !showControls && currentUILayout.toolbar.position === 'right',
          'opacity-0 pointer-events-none': !showControls && currentUILayout.toolbar.position === 'hidden'
        }
      ]"
      :style="{
        backgroundColor: currentTheme.ui.toolbarBg,
        boxShadow: currentTheme.ui.shadow,
        opacity: displayOptions.uiOpacity
      }"
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
            @click="toggleBookmark"
            class="p-2 rounded-full text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-800"
            :class="{ 'text-yellow-500': hasBookmarkOnCurrentPage }"
            title="Toggle Bookmark (M)"
          >
            <svg
              class="h-6 w-6"
              xmlns="http://www.w3.org/2000/svg"
              :fill="hasBookmarkOnCurrentPage ? 'currentColor' : 'none'"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
              />
            </svg>
          </button>

          <button
            @click="showBookmarks = true"
            class="p-2 rounded-full text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-800"
            title="View Bookmarks (B)"
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
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          </button>

          <button
            @click="showKeyboardHelp = true"
            class="p-2 rounded-full text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-800"
            title="Keyboard Shortcuts (H)"
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
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </button>

          <button
            @click="toggleSettings"
            class="p-2 rounded-full text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-800"
            title="Settings (S)"
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
                    Reading Mode
                  </label>
                  <div class="mt-2 grid grid-cols-2 gap-2">
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
                    <button
                      @click="updateSettings({ pageLayout: 'list' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.pageLayout === 'list'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      List View
                    </button>
                    <button
                      @click="updateSettings({ pageLayout: 'adaptive' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.pageLayout === 'adaptive'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Adaptive
                    </button>
                  </div>
                </div>

                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Fit Mode
                  </label>
                  <div class="mt-2 grid grid-cols-2 gap-2">
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
                    <button
                      @click="updateSettings({ fitMode: 'original' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.fitMode === 'original'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Original Size
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

                <!-- Image Quality Settings -->
                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Image Quality
                  </label>
                  <div class="mt-2 grid grid-cols-3 gap-2">
                    <button
                      @click="updateSettings({ imageQuality: 'high' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.imageQuality === 'high'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      High
                    </button>
                    <button
                      @click="updateSettings({ imageQuality: 'medium' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.imageQuality === 'medium'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Medium
                    </button>
                    <button
                      @click="updateSettings({ imageQuality: 'low' })"
                      class="px-3 py-2 border rounded-md text-sm font-medium"
                      :class="
                        settings.imageQuality === 'low'
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      Low
                    </button>
                  </div>
                </div>

                <!-- Preload Distance Settings -->
                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Preload Distance: {{ settings.preloadDistance }} pages
                  </label>
                  <div class="mt-2">
                    <input
                      type="range"
                      min="1"
                      max="10"
                      :value="settings.preloadDistance"
                      @input="updateSettings({ preloadDistance: parseInt($event.target.value) })"
                      class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                    />
                    <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                      <span>1</span>
                      <span>5</span>
                      <span>10</span>
                    </div>
                  </div>
                </div>

                <!-- Theme Selection -->
                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Reader Theme
                  </label>
                  <div class="mt-2 grid grid-cols-2 gap-2">
                    <button
                      v-for="(theme, themeId) in themeDefinitions"
                      :key="themeId"
                      @click="updateTheme(themeId)"
                      class="px-3 py-2 border rounded-md text-sm font-medium flex items-center"
                      :class="
                        settings.theme === themeId
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-dark-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-dark-800'
                      "
                    >
                      <div
                        class="w-4 h-4 rounded-full mr-2"
                        :style="{ backgroundColor: theme.colors.background, border: `2px solid ${theme.colors.primary}` }"
                      ></div>
                      {{ theme.name }}
                    </button>
                  </div>
                </div>

                <!-- Display Options -->
                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                  >
                    Display Options
                  </label>
                  <div class="space-y-3">
                    <div>
                      <label class="block text-xs text-gray-600 dark:text-gray-400 mb-1">Page Margin: {{ displayOptions.pageMargin }}px</label>
                      <input
                        type="range"
                        min="0"
                        max="50"
                        :value="displayOptions.pageMargin"
                        @input="updateDisplayOptions({ pageMargin: parseInt($event.target.value) })"
                        class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                      />
                    </div>

                    <div>
                      <label class="block text-xs text-gray-600 dark:text-gray-400 mb-1">Border Radius: {{ displayOptions.borderRadius }}px</label>
                      <input
                        type="range"
                        min="0"
                        max="20"
                        :value="displayOptions.borderRadius"
                        @input="updateDisplayOptions({ borderRadius: parseInt($event.target.value) })"
                        class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                      />
                    </div>

                    <div class="flex items-center justify-between">
                      <label class="text-sm text-gray-600 dark:text-gray-400">Show Shadows</label>
                      <button
                        @click="updateDisplayOptions({ showShadows: !displayOptions.showShadows })"
                        class="relative inline-flex flex-shrink-0 h-5 w-9 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200"
                        :class="displayOptions.showShadows ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'"
                      >
                        <span
                          class="pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200"
                          :class="displayOptions.showShadows ? 'translate-x-4' : 'translate-x-0'"
                        ></span>
                      </button>
                    </div>
                  </div>
                </div>

                <!-- UI Layout Selection -->
                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    UI Layout
                  </label>
                  <div class="mt-2 space-y-2">
                    <div
                      v-for="(layout, layoutId) in uiLayoutDefinitions"
                      :key="layoutId"
                      class="flex items-center"
                    >
                      <input
                        :id="`layout-${layoutId}`"
                        type="radio"
                        :value="layoutId"
                        :checked="settings.uiLayout === layoutId"
                        @change="updateUILayout(layoutId)"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-dark-600"
                      />
                      <label
                        :for="`layout-${layoutId}`"
                        class="ml-3 block text-sm text-gray-700 dark:text-gray-200"
                      >
                        <div class="font-medium">{{ layout.name }}</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400">{{ layout.description }}</div>
                      </label>
                    </div>
                  </div>
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

    <!-- Keyboard Shortcuts Help -->
    <div
      v-if="showKeyboardHelp"
      class="fixed inset-0 z-30 overflow-y-auto"
      @click.self="showKeyboardHelp = false"
    >
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
      >
        <div
          class="fixed inset-0 bg-gray-500 dark:bg-dark-900 bg-opacity-75 dark:bg-opacity-75 transition-opacity"
        ></div>

        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6"
        >
          <div>
            <div class="mt-3 text-center sm:mt-0 sm:text-left">
              <h3
                class="text-lg leading-6 font-medium text-gray-900 dark:text-white"
              >
                Keyboard Shortcuts
              </h3>

              <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 class="font-semibold text-gray-900 dark:text-white mb-2">Navigation</h4>
                  <div class="space-y-1 text-gray-600 dark:text-gray-300">
                    <div class="flex justify-between">
                      <span>← →</span>
                      <span>Previous/Next Page</span>
                    </div>
                    <div class="flex justify-between">
                      <span>↑ ↓</span>
                      <span>Previous/Next Chapter</span>
                    </div>
                    <div class="flex justify-between">
                      <span>D</span>
                      <span>Toggle Reading Direction</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 class="font-semibold text-gray-900 dark:text-white mb-2">Reading Modes</h4>
                  <div class="space-y-1 text-gray-600 dark:text-gray-300">
                    <div class="flex justify-between">
                      <span>1</span>
                      <span>Single Page</span>
                    </div>
                    <div class="flex justify-between">
                      <span>2</span>
                      <span>Double Page</span>
                    </div>
                    <div class="flex justify-between">
                      <span>3</span>
                      <span>List View</span>
                    </div>
                    <div class="flex justify-between">
                      <span>4</span>
                      <span>Adaptive Mode</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 class="font-semibold text-gray-900 dark:text-white mb-2">Fit Modes</h4>
                  <div class="space-y-1 text-gray-600 dark:text-gray-300">
                    <div class="flex justify-between">
                      <span>Q</span>
                      <span>Fit Width</span>
                    </div>
                    <div class="flex justify-between">
                      <span>W</span>
                      <span>Fit Height</span>
                    </div>
                    <div class="flex justify-between">
                      <span>E</span>
                      <span>Fit Both</span>
                    </div>
                    <div class="flex justify-between">
                      <span>R</span>
                      <span>Original Size</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 class="font-semibold text-gray-900 dark:text-white mb-2">Controls</h4>
                  <div class="space-y-1 text-gray-600 dark:text-gray-300">
                    <div class="flex justify-between">
                      <span>S</span>
                      <span>Settings</span>
                    </div>
                    <div class="flex justify-between">
                      <span>F</span>
                      <span>Fullscreen</span>
                    </div>
                    <div class="flex justify-between">
                      <span>H / ?</span>
                      <span>Show Help</span>
                    </div>
                    <div class="flex justify-between">
                      <span>B</span>
                      <span>View Bookmarks</span>
                    </div>
                    <div class="flex justify-between">
                      <span>M</span>
                      <span>Toggle Bookmark</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Esc</span>
                      <span>Close Dialogs</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-5 sm:mt-6">
            <button
              @click="showKeyboardHelp = false"
              class="inline-flex justify-center w-full rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bookmark Dialog -->
    <div
      v-if="showBookmarkDialog"
      class="fixed inset-0 z-30 overflow-y-auto"
      @click.self="showBookmarkDialog = false"
    >
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
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
                Add Bookmark
              </h3>

              <div class="mt-4">
                <label
                  class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Note (optional)
                </label>
                <textarea
                  v-model="bookmarkNote"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-700 dark:text-white"
                  rows="3"
                  placeholder="Add a note for this bookmark..."
                ></textarea>
              </div>
            </div>
          </div>

          <div class="mt-5 sm:mt-6 flex space-x-3">
            <button
              @click="addBookmark"
              class="flex-1 inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:text-sm"
            >
              Add Bookmark
            </button>
            <button
              @click="showBookmarkDialog = false"
              class="flex-1 inline-flex justify-center rounded-md border border-gray-300 dark:border-dark-600 shadow-sm px-4 py-2 bg-white dark:bg-dark-700 text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bookmarks Panel -->
    <div
      v-if="showBookmarks"
      class="fixed inset-0 z-30 overflow-y-auto"
      @click.self="showBookmarks = false"
    >
      <div
        class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
      >
        <div
          class="fixed inset-0 bg-gray-500 dark:bg-dark-900 bg-opacity-75 dark:bg-opacity-75 transition-opacity"
        ></div>

        <div
          class="inline-block align-bottom bg-white dark:bg-dark-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6"
        >
          <div>
            <div class="mt-3 text-center sm:mt-0 sm:text-left">
              <h3
                class="text-lg leading-6 font-medium text-gray-900 dark:text-white"
              >
                Bookmarks
              </h3>

              <div class="mt-4 max-h-96 overflow-y-auto">
                <div v-if="bookmarks.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
                  No bookmarks yet. Press 'M' to bookmark the current page.
                </div>

                <div v-else class="space-y-3">
                  <div
                    v-for="bookmark in bookmarks"
                    :key="bookmark.id"
                    class="flex items-start justify-between p-3 border border-gray-200 dark:border-dark-600 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-700 cursor-pointer"
                    @click="goToBookmark(bookmark)"
                  >
                    <div class="flex-1">
                      <div class="font-medium text-gray-900 dark:text-white">
                        {{ bookmark.mangaTitle }}
                      </div>
                      <div class="text-sm text-gray-600 dark:text-gray-300">
                        {{ bookmark.chapterTitle }} - Page {{ bookmark.page }}
                      </div>
                      <div v-if="bookmark.note" class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {{ bookmark.note }}
                      </div>
                      <div class="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        {{ formatBookmarkDate(bookmark.createdAt) }}
                      </div>
                    </div>

                    <button
                      @click.stop="removeBookmark(bookmark.id)"
                      class="ml-3 p-1 text-red-500 hover:text-red-700"
                    >
                      <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-5 sm:mt-6">
            <button
              @click="showBookmarks = false"
              class="inline-flex justify-center w-full rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Achievement Notifications -->
    <div class="fixed top-4 right-4 z-40 space-y-2">
      <div
        v-for="notification in achievementNotifications"
        :key="notification.id"
        class="achievement-notification bg-green-600 text-white p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300"
        :class="{ 'translate-x-full opacity-0': !notification.show }"
      >
        <div class="flex items-start">
          <div class="text-2xl mr-3">🏆</div>
          <div class="flex-1">
            <div class="font-bold">Achievement Unlocked!</div>
            <div class="text-sm opacity-90">{{ notification.achievement.title }}</div>
            <div class="text-xs opacity-75 mt-1">{{ notification.achievement.description }}</div>
          </div>
          <button
            @click="dismissNotification(notification.id)"
            class="ml-2 text-white hover:text-gray-200"
          >
            <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Reader Content -->
    <div
      class="reader-content min-h-screen flex items-center justify-center transition-colors duration-300"
      :style="{
        backgroundColor: currentTheme.colors.background,
        padding: `${displayOptions.pageMargin}px`
      }"
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

      <!-- Single Page Mode -->
      <div
        v-else-if="currentPageUrl && settings.pageLayout === 'single'"
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
            'w-auto h-auto': settings.fitMode === 'original',
          }"
        />

        <div
          v-if="settings.showPageNumbers"
          class="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm"
        >
          {{ currentPageDisplay }}
        </div>
      </div>

      <!-- Double Page Mode -->
      <div
        v-else-if="currentPagePair.length && settings.pageLayout === 'double'"
        class="reader-page-container max-h-screen overflow-auto"
        :class="{
          'flex justify-center items-center': true,
          'reader-fit-width': settings.fitMode === 'width',
          'reader-fit-height': settings.fitMode === 'height',
          'reader-fit-both': settings.fitMode === 'both',
        }"
      >
        <div class="flex gap-1" :class="{ 'flex-row-reverse': settings.readingDirection === 'rtl' }">
          <img
            v-for="(page, index) in currentPagePair"
            :key="page.id || index"
            :src="page.url"
            :alt="`Page ${page.number || currentPage + index}`"
            class="reader-page"
            :class="{
              'max-w-[50vw]': settings.fitMode === 'width' || settings.fitMode === 'both',
              'max-h-screen': settings.fitMode === 'height' || settings.fitMode === 'both',
              'w-auto h-auto': settings.fitMode === 'original',
            }"
          />
        </div>

        <div
          v-if="settings.showPageNumbers"
          class="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm"
        >
          {{ currentPageDisplay }}
        </div>
      </div>

      <!-- List View Mode -->
      <div
        v-else-if="pages.length && settings.pageLayout === 'list'"
        class="reader-list-container"
        :class="{
          'reader-fit-width': settings.fitMode === 'width',
          'reader-fit-height': settings.fitMode === 'height',
          'reader-fit-both': settings.fitMode === 'both',
        }"
        @scroll="handleListScroll"
      >
        <div class="flex flex-col items-center space-y-2 py-4">
          <img
            v-for="(page, index) in pages"
            :key="page.id || index"
            :src="getQualityImageUrl(page)"
            :alt="`Page ${index + 1}`"
            :id="`list-page-${index + 1}`"
            class="reader-page list-page"
            :class="{
              'max-w-full': settings.fitMode === 'width' || settings.fitMode === 'both',
              'w-auto h-auto': settings.fitMode === 'original',
            }"
            @load="handleImageLoad(index + 1)"
          />
        </div>

        <div
          v-if="settings.showPageNumbers"
          class="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm"
        >
          {{ currentPageInView }} / {{ totalPages }}
        </div>
      </div>

      <!-- Adaptive Mode (fallback to single page while analyzing) -->
      <div
        v-else-if="currentPageUrl && settings.pageLayout === 'adaptive'"
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
            'w-auto h-auto': settings.fitMode === 'original',
          }"
        />

        <div
          v-if="settings.showPageNumbers"
          class="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm"
        >
          {{ currentPageDisplay }}
        </div>

        <!-- Adaptive mode indicator -->
        <div class="fixed top-4 right-4 bg-blue-600 text-white px-3 py-1 rounded-full text-sm">
          Analyzing content...
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
