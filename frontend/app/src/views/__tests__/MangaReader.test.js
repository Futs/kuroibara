import { describe, it, expect, beforeEach, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import MangaReader from "../MangaReader.vue";

// Mock API
vi.mock("../../services/api", () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      data: {
        id: "1",
        title: "Test Manga",
        chapters: [
          { id: "1", title: "Chapter 1", pages: ["page1.jpg", "page2.jpg"] },
        ],
      },
    }),
    post: vi.fn(),
  },
}));

// Mock router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/manga/:id/read/:chapter/:page?",
      name: "manga-reader",
      component: MangaReader,
    },
  ],
});

describe("MangaReader Component", () => {
  let wrapper;
  let pinia;

  beforeEach(async () => {
    pinia = createPinia();
    setActivePinia(pinia);

    await router.push("/manga/1/read/1/1");

    // Mock the reader store with initial data
    const { useReaderStore } = await import("../../stores/reader");
    const store = useReaderStore();

    // Set up mock data to prevent API calls
    store.manga = { id: "1", title: "Test Manga" };
    store.chapter = { id: "1", title: "Chapter 1" };
    store.chapters = [{ id: "1", title: "Chapter 1" }];
    store.pages = [
      { url: "https://example.com/page1.jpg" },
      { url: "https://example.com/page2.jpg" },
    ];
    store.currentPage = 1;
    store.loading = false;
    store.error = null;

    // Set default settings for proper rendering
    store.settings = {
      pageLayout: "single",
      fitMode: "width",
      imageQuality: "medium",
      ...store.settings,
    };

    wrapper = mount(MangaReader, {
      global: {
        plugins: [pinia, router],
      },
    });
  });

  describe("Reading Mode Switching", () => {
    it("should render single page mode by default", () => {
      expect(wrapper.find(".reader-page-container").exists()).toBe(true);
    });

    it("should switch to settings panel when settings button is clicked", async () => {
      const settingsButton = wrapper.find('[title="Settings (S)"]');
      await settingsButton.trigger("click");

      expect(wrapper.find("h3").text()).toContain("Reader Settings");
    });

    it("should show keyboard help when help button is clicked", async () => {
      const helpButton = wrapper.find('[title="Keyboard Shortcuts (H)"]');
      await helpButton.trigger("click");

      expect(wrapper.find("h3").text()).toContain("Keyboard Shortcuts");
    });
  });

  describe("Keyboard Shortcuts", () => {
    it("should open settings with S key", async () => {
      await wrapper.trigger("keydown", { key: "s" });
      expect(wrapper.vm.showSettings).toBe(true);
    });

    it("should open help with H key", async () => {
      await wrapper.trigger("keydown", { key: "h" });
      expect(wrapper.vm.showKeyboardHelp).toBe(true);
    });

    it("should close dialogs with Escape key", async () => {
      wrapper.vm.showSettings = true;
      wrapper.vm.showKeyboardHelp = true;

      await wrapper.trigger("keydown", { key: "Escape" });

      expect(wrapper.vm.showSettings).toBe(false);
      expect(wrapper.vm.showKeyboardHelp).toBe(false);
    });

    it("should switch reading modes with number keys", async () => {
      const store = wrapper.vm.readerStore;

      await wrapper.trigger("keydown", { key: "2" });
      expect(store.settings.pageLayout).toBe("double");

      await wrapper.trigger("keydown", { key: "3" });
      expect(store.settings.pageLayout).toBe("list");

      await wrapper.trigger("keydown", { key: "4" });
      expect(store.settings.pageLayout).toBe("adaptive");

      await wrapper.trigger("keydown", { key: "1" });
      expect(store.settings.pageLayout).toBe("single");
    });

    it("should switch fit modes with QWER keys", async () => {
      const store = wrapper.vm.readerStore;

      await wrapper.trigger("keydown", { key: "q" });
      expect(store.settings.fitMode).toBe("width");

      await wrapper.trigger("keydown", { key: "w" });
      expect(store.settings.fitMode).toBe("height");

      await wrapper.trigger("keydown", { key: "e" });
      expect(store.settings.fitMode).toBe("both");

      await wrapper.trigger("keydown", { key: "r" });
      expect(store.settings.fitMode).toBe("original");
    });
  });

  describe("Settings Panel", () => {
    beforeEach(async () => {
      wrapper.vm.showSettings = true;
      await wrapper.vm.$nextTick();
    });

    it("should display all reading mode options", () => {
      const buttons = wrapper.findAll("button");
      const modeButtons = buttons.filter((btn) =>
        ["Single Page", "Double Page", "List View", "Adaptive"].includes(
          btn.text(),
        ),
      );
      expect(modeButtons).toHaveLength(4);
    });

    it("should display all fit mode options", () => {
      const buttons = wrapper.findAll("button");
      const fitButtons = buttons.filter((btn) =>
        ["Fit Width", "Fit Height", "Fit Both", "Original Size"].includes(
          btn.text(),
        ),
      );
      expect(fitButtons).toHaveLength(4);
    });

    it("should display image quality options", () => {
      const buttons = wrapper.findAll("button");
      const qualityButtons = buttons.filter((btn) =>
        ["High", "Medium", "Low"].includes(btn.text()),
      );
      expect(qualityButtons).toHaveLength(3);
    });

    it("should have preload distance slider", () => {
      const slider = wrapper.find('input[type="range"]');
      expect(slider.exists()).toBe(true);
      expect(slider.attributes("min")).toBe("1");
      expect(slider.attributes("max")).toBe("10");
    });
  });

  describe("Image Quality Management", () => {
    it("should generate quality URLs correctly", () => {
      const page = { url: "https://example.com/page1.jpg?test=1" };

      // Test medium quality
      wrapper.vm.readerStore.settings.imageQuality = "medium";
      const mediumUrl = wrapper.vm.getQualityImageUrl(page);
      expect(mediumUrl).toContain("quality=75");
      expect(mediumUrl).toContain("width=1200");

      // Test low quality
      wrapper.vm.readerStore.settings.imageQuality = "low";
      const lowUrl = wrapper.vm.getQualityImageUrl(page);
      expect(lowUrl).toContain("quality=60");
      expect(lowUrl).toContain("width=800");

      // Test high quality (original)
      wrapper.vm.readerStore.settings.imageQuality = "high";
      const highUrl = wrapper.vm.getQualityImageUrl(page);
      expect(highUrl).toBe(page.url);
    });
  });
});
