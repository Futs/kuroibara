<template>
  <div
    class="theme-customizer bg-white dark:bg-dark-800 rounded-lg shadow-lg p-6"
  >
    <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
      Theme Customizer
    </h2>

    <!-- Theme Presets -->
    <div class="mb-8">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Theme Presets
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="(theme, themeId) in themeDefinitions"
          :key="themeId"
          class="theme-preset cursor-pointer p-4 rounded-lg border-2 transition-all duration-200"
          :class="
            currentTheme.id === themeId
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-200 dark:border-dark-600 hover:border-gray-300 dark:hover:border-dark-500'
          "
          @click="selectTheme(themeId)"
        >
          <div class="flex items-center mb-3">
            <div
              class="w-8 h-8 rounded-full mr-3 border-2"
              :style="{
                backgroundColor: theme.colors.background,
                borderColor: theme.colors.primary,
              }"
            ></div>
            <div>
              <div class="font-semibold text-gray-900 dark:text-white">
                {{ theme.name }}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-300">
                {{ theme.description }}
              </div>
            </div>
          </div>

          <!-- Theme Preview -->
          <div
            class="theme-preview rounded-md overflow-hidden"
            :style="{ backgroundColor: theme.colors.background }"
          >
            <div
              class="h-2"
              :style="{ backgroundColor: theme.colors.primary }"
            ></div>
            <div class="p-2 space-y-1">
              <div
                class="h-1 rounded"
                :style="{ backgroundColor: theme.colors.text, opacity: 0.8 }"
              ></div>
              <div
                class="h-1 rounded w-3/4"
                :style="{
                  backgroundColor: theme.colors.textSecondary,
                  opacity: 0.6,
                }"
              ></div>
              <div
                class="h-1 rounded w-1/2"
                :style="{ backgroundColor: theme.colors.accent, opacity: 0.7 }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Custom Theme Editor -->
    <div v-if="currentTheme.id === 'custom'" class="mb-8">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Custom Theme Editor
      </h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Color Settings -->
        <div>
          <h4 class="font-medium text-gray-900 dark:text-white mb-3">Colors</h4>
          <div class="space-y-3">
            <div
              v-for="(value, colorKey) in currentTheme.colors"
              :key="colorKey"
              class="flex items-center"
            >
              <label
                class="w-24 text-sm text-gray-600 dark:text-gray-300 capitalize"
              >
                {{ colorKey.replace(/([A-Z])/g, " $1").toLowerCase() }}
              </label>
              <input
                type="color"
                :value="value"
                @input="updateCustomColor(colorKey, $event.target.value)"
                class="w-12 h-8 rounded border border-gray-300 dark:border-dark-600 cursor-pointer"
              />
              <input
                type="text"
                :value="value"
                @input="updateCustomColor(colorKey, $event.target.value)"
                class="ml-2 flex-1 px-2 py-1 text-sm border border-gray-300 dark:border-dark-600 rounded dark:bg-dark-700 dark:text-white"
              />
            </div>
          </div>
        </div>

        <!-- UI Settings -->
        <div>
          <h4 class="font-medium text-gray-900 dark:text-white mb-3">
            UI Elements
          </h4>
          <div class="space-y-3">
            <div
              v-for="(value, uiKey) in currentTheme.ui"
              :key="uiKey"
              class="flex items-center"
            >
              <label
                class="w-24 text-sm text-gray-600 dark:text-gray-300 capitalize"
              >
                {{ uiKey.replace(/([A-Z])/g, " $1").toLowerCase() }}
              </label>
              <input
                type="text"
                :value="value"
                @input="updateCustomUI(uiKey, $event.target.value)"
                class="flex-1 px-2 py-1 text-sm border border-gray-300 dark:border-dark-600 rounded dark:bg-dark-700 dark:text-white"
                :placeholder="getUIPlaceholder(uiKey)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Typography Settings -->
    <div class="mb-8">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Typography
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >Font Family</label
          >
          <select
            :value="typography.fontFamily"
            @change="updateTypography({ fontFamily: $event.target.value })"
            class="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-md dark:bg-dark-700 dark:text-white"
          >
            <option value="system-ui">System UI</option>
            <option value="serif">Serif</option>
            <option value="sans-serif">Sans Serif</option>
            <option value="monospace">Monospace</option>
            <option value="'Times New Roman', serif">Times New Roman</option>
            <option value="'Arial', sans-serif">Arial</option>
            <option value="'Helvetica', sans-serif">Helvetica</option>
            <option value="'Georgia', serif">Georgia</option>
          </select>
        </div>

        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Font Size: {{ typography.fontSize }}
          </label>
          <input
            type="range"
            min="12"
            max="24"
            :value="parseInt(typography.fontSize)"
            @input="updateTypography({ fontSize: $event.target.value + 'px' })"
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
        </div>

        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Line Height: {{ typography.lineHeight }}
          </label>
          <input
            type="range"
            min="1.2"
            max="2.0"
            step="0.1"
            :value="typography.lineHeight"
            @input="updateTypography({ lineHeight: $event.target.value })"
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
        </div>

        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Letter Spacing: {{ typography.letterSpacing }}
          </label>
          <input
            type="range"
            min="-2"
            max="4"
            step="0.5"
            :value="parseFloat(typography.letterSpacing)"
            @input="
              updateTypography({ letterSpacing: $event.target.value + 'px' })
            "
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
        </div>
      </div>
    </div>

    <!-- Display Options -->
    <div class="mb-8">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Display Options
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Page Margin: {{ displayOptions.pageMargin }}px
          </label>
          <input
            type="range"
            min="0"
            max="100"
            :value="displayOptions.pageMargin"
            @input="
              updateDisplayOptions({
                pageMargin: parseInt($event.target.value),
              })
            "
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
        </div>

        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Page Padding: {{ displayOptions.pagePadding }}px
          </label>
          <input
            type="range"
            min="0"
            max="50"
            :value="displayOptions.pagePadding"
            @input="
              updateDisplayOptions({
                pagePadding: parseInt($event.target.value),
              })
            "
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
        </div>

        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Border Radius: {{ displayOptions.borderRadius }}px
          </label>
          <input
            type="range"
            min="0"
            max="20"
            :value="displayOptions.borderRadius"
            @input="
              updateDisplayOptions({
                borderRadius: parseInt($event.target.value),
              })
            "
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
        </div>

        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            UI Opacity: {{ Math.round(displayOptions.uiOpacity * 100) }}%
          </label>
          <input
            type="range"
            min="0.5"
            max="1"
            step="0.05"
            :value="displayOptions.uiOpacity"
            @input="
              updateDisplayOptions({
                uiOpacity: parseFloat($event.target.value),
              })
            "
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
        </div>

        <div class="flex items-center justify-between">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300"
            >Show Shadows</label
          >
          <button
            @click="
              updateDisplayOptions({ showShadows: !displayOptions.showShadows })
            "
            class="relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200"
            :class="
              displayOptions.showShadows
                ? 'bg-blue-600'
                : 'bg-gray-200 dark:bg-gray-600'
            "
          >
            <span
              class="pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200"
              :class="
                displayOptions.showShadows ? 'translate-x-5' : 'translate-x-0'
              "
            ></span>
          </button>
        </div>
      </div>
    </div>

    <!-- Theme Actions -->
    <div class="flex flex-wrap gap-3">
      <button
        @click="exportTheme"
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
      >
        Export Theme
      </button>

      <label
        class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors cursor-pointer"
      >
        Import Theme
        <input
          type="file"
          accept=".json"
          @change="importTheme"
          class="hidden"
        />
      </label>

      <button
        @click="resetTheme"
        class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
      >
        Reset to Default
      </button>

      <button
        v-if="currentTheme.id !== 'custom'"
        @click="createCustomFromCurrent"
        class="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
      >
        Customize This Theme
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useReaderStore } from "../stores/reader";

const readerStore = useReaderStore();

// Computed properties
const currentTheme = computed(() => readerStore.getCurrentTheme());
const themeDefinitions = computed(() => readerStore.getThemeDefinitions());
const typography = computed(() => readerStore.settings.typography);
const displayOptions = computed(() => readerStore.settings.displayOptions);

// Methods
const selectTheme = (themeId) => {
  readerStore.updateTheme(themeId);
};

const updateCustomColor = (colorKey, value) => {
  const customTheme = { ...readerStore.settings.customTheme };
  if (!customTheme.colors) customTheme.colors = {};
  customTheme.colors[colorKey] = value;
  readerStore.updateTheme("custom", customTheme);
};

const updateCustomUI = (uiKey, value) => {
  const customTheme = { ...readerStore.settings.customTheme };
  if (!customTheme.ui) customTheme.ui = {};
  customTheme.ui[uiKey] = value;
  readerStore.updateTheme("custom", customTheme);
};

const updateTypography = (updates) => {
  readerStore.updateTypography(updates);
};

const updateDisplayOptions = (updates) => {
  readerStore.updateDisplayOptions(updates);
};

const exportTheme = () => {
  const themeData = readerStore.exportTheme();
  const blob = new Blob([themeData], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `kuroibara-theme-${new Date().toISOString().split("T")[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

const importTheme = (event) => {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const success = readerStore.importTheme(e.target.result);
      if (!success) {
        alert("Failed to import theme. Please check the file format.");
      }
    };
    reader.readAsText(file);
  }
};

const resetTheme = () => {
  if (
    confirm("Are you sure you want to reset all customizations to default?")
  ) {
    readerStore.resetToDefaultTheme();
  }
};

const createCustomFromCurrent = () => {
  const baseTheme = currentTheme.value;
  readerStore.createCustomTheme(baseTheme.id, {
    colors: { ...baseTheme.colors },
    ui: { ...baseTheme.ui },
  });
};

const getUIPlaceholder = (key) => {
  const placeholders = {
    toolbarBg: "rgba(45, 45, 45, 0.95)",
    overlayBg: "rgba(0, 0, 0, 0.8)",
    buttonHover: "rgba(255, 255, 255, 0.1)",
    shadow: "0 4px 12px rgba(0, 0, 0, 0.3)",
  };
  return placeholders[key] || "";
};
</script>

<style scoped>
.theme-preset:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.theme-preview {
  height: 60px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

input[type="color"] {
  -webkit-appearance: none;
  border: none;
  cursor: pointer;
}

input[type="color"]::-webkit-color-swatch-wrapper {
  padding: 0;
}

input[type="color"]::-webkit-color-swatch {
  border: none;
  border-radius: 4px;
}
</style>
