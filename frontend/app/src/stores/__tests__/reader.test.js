import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useReaderStore } from '../reader';

// Mock API
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Reader Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe('Settings Management', () => {
    it('should initialize with default settings', () => {
      const store = useReaderStore();
      
      expect(store.settings.readingDirection).toBe('rtl');
      expect(store.settings.pageLayout).toBe('single');
      expect(store.settings.fitMode).toBe('width');
      expect(store.settings.preloadDistance).toBe(3);
      expect(store.settings.imageQuality).toBe('high');
    });

    it('should update settings and persist to localStorage', () => {
      const store = useReaderStore();
      const mockSetItem = vi.spyOn(Storage.prototype, 'setItem');
      
      store.updateSettings({ pageLayout: 'double', fitMode: 'height' });
      
      expect(store.settings.pageLayout).toBe('double');
      expect(store.settings.fitMode).toBe('height');
      expect(mockSetItem).toHaveBeenCalledWith('pageLayout', 'double');
      expect(mockSetItem).toHaveBeenCalledWith('fitMode', 'height');
    });
  });

  describe('Double-Page Mode', () => {
    it('should return single page for single page mode', () => {
      const store = useReaderStore();
      store.pages = [
        { id: 1, url: 'page1.jpg' },
        { id: 2, url: 'page2.jpg' },
      ];
      store.currentPage = 1;
      store.settings.pageLayout = 'single';
      
      const pagePair = store.getCurrentPagePair;
      expect(pagePair).toHaveLength(1);
    });

    it('should return page pair for double page mode', () => {
      const store = useReaderStore();
      store.pages = [
        { id: 1, url: 'page1.jpg' },
        { id: 2, url: 'page2.jpg' },
        { id: 3, url: 'page3.jpg' },
      ];
      store.currentPage = 1;
      store.settings.pageLayout = 'double';
      
      const pagePair = store.getCurrentPagePair;
      expect(pagePair).toHaveLength(2);
    });

    it('should handle RTL reading direction correctly', () => {
      const store = useReaderStore();
      store.pages = [
        { id: 1, url: 'page1.jpg' },
        { id: 2, url: 'page2.jpg' },
      ];
      store.currentPage = 1;
      store.settings.pageLayout = 'double';
      store.settings.readingDirection = 'rtl';
      
      const pagePair = store.getCurrentPagePair;
      expect(pagePair[0].id).toBe(2); // Right page first in RTL
      expect(pagePair[1].id).toBe(1); // Left page second in RTL
    });
  });

  describe('Navigation', () => {
    beforeEach(() => {
      const store = useReaderStore();
      store.pages = [
        { id: 1, url: 'page1.jpg' },
        { id: 2, url: 'page2.jpg' },
        { id: 3, url: 'page3.jpg' },
        { id: 4, url: 'page4.jpg' },
      ];
      store.currentPage = 1;
    });

    it('should navigate correctly in single page mode', () => {
      const store = useReaderStore();
      store.settings.pageLayout = 'single';
      
      store.nextPage();
      expect(store.currentPage).toBe(2);
      
      store.prevPage();
      expect(store.currentPage).toBe(1);
    });

    it('should navigate correctly in double page mode', () => {
      const store = useReaderStore();
      store.settings.pageLayout = 'double';
      
      store.nextPage();
      expect(store.currentPage).toBe(3);
      
      store.prevPage();
      expect(store.currentPage).toBe(1);
    });
  });

  describe('Image Quality', () => {
    it('should return original URL for high quality', () => {
      const store = useReaderStore();
      store.pages = [{ id: 1, url: 'https://example.com/page1.jpg' }];
      store.currentPage = 1;
      store.settings.imageQuality = 'high';
      
      const url = store.getCurrentPageUrl;
      expect(url).toBe('https://example.com/page1.jpg');
    });

    it('should add quality parameters for medium quality', () => {
      const store = useReaderStore();
      store.pages = [{ id: 1, url: 'https://example.com/page1.jpg?test=1' }];
      store.currentPage = 1;
      store.settings.imageQuality = 'medium';
      
      const url = store.getCurrentPageUrl;
      expect(url).toContain('quality=75');
      expect(url).toContain('width=1200');
    });
  });

  describe('Preloading', () => {
    it('should preload images within distance', () => {
      const store = useReaderStore();
      store.pages = [
        { id: 1, url: 'page1.jpg' },
        { id: 2, url: 'page2.jpg' },
        { id: 3, url: 'page3.jpg' },
        { id: 4, url: 'page4.jpg' },
        { id: 5, url: 'page5.jpg' },
      ];
      store.currentPage = 2;
      store.settings.preloadDistance = 2;

      // Mock Image constructor
      global.Image = vi.fn(() => ({
        onload: null,
        onerror: null,
        src: '',
      }));

      store.preloadImages();

      // Should preload pages 2, 3, 4 (current + distance)
      expect(store.preloadQueue).toContain('page2.jpg');
      expect(store.preloadQueue).toContain('page3.jpg');
      expect(store.preloadQueue).toContain('page4.jpg');
    });
  });

  describe('Reading Statistics', () => {
    it('should track reading session', () => {
      const store = useReaderStore();

      store.startReadingSession('manga1', 'chapter1');
      expect(store.readingSession.mangaId).toBe('manga1');
      expect(store.readingSession.chapterId).toBe('chapter1');
      expect(store.readingSession.startTime).toBeTruthy();
    });

    it('should track page reads', () => {
      const store = useReaderStore();
      store.startReadingSession('manga1', 'chapter1');

      store.trackPageRead();
      store.trackPageRead();

      expect(store.readingSession.pagesRead).toBe(2);
    });

    it('should update reading streak correctly', () => {
      const store = useReaderStore();

      // First day reading
      store.updateReadingStreak();
      expect(store.readingStats.currentStreak).toBe(1);

      // Simulate reading yesterday
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      store.readingStats.lastReadDate = yesterday.toDateString();

      // Reading today should continue streak
      store.updateReadingStreak();
      expect(store.readingStats.currentStreak).toBe(2);
    });
  });

  describe('Bookmarks', () => {
    it('should add bookmark', () => {
      const store = useReaderStore();
      store.manga = { id: 'manga1', title: 'Test Manga' };
      store.chapter = { id: 'chapter1', title: 'Chapter 1' };
      store.currentPage = 5;

      const bookmark = store.addBookmark('Important scene');

      expect(bookmark.mangaId).toBe('manga1');
      expect(bookmark.chapterId).toBe('chapter1');
      expect(bookmark.page).toBe(5);
      expect(bookmark.note).toBe('Important scene');
      expect(store.bookmarks).toContain(bookmark);
    });

    it('should remove bookmark', () => {
      const store = useReaderStore();
      store.manga = { id: 'manga1', title: 'Test Manga' };
      store.chapter = { id: 'chapter1', title: 'Chapter 1' };
      store.currentPage = 5;

      const bookmark = store.addBookmark('Test bookmark');
      expect(store.bookmarks).toHaveLength(1);

      store.removeBookmark(bookmark.id);
      expect(store.bookmarks).toHaveLength(0);
    });

    it('should check if current page has bookmark', () => {
      const store = useReaderStore();
      store.manga = { id: 'manga1', title: 'Test Manga' };
      store.chapter = { id: 'chapter1', title: 'Chapter 1' };
      store.currentPage = 5;

      expect(store.hasBookmarkOnCurrentPage()).toBe(false);

      store.addBookmark('Test bookmark');
      expect(store.hasBookmarkOnCurrentPage()).toBe(true);
    });
  });

  describe('Achievements', () => {
    it('should check page-based achievements', () => {
      const store = useReaderStore();
      store.readingStats.totalPagesRead = 100;

      const newAchievements = store.checkAchievements();
      const pageAchievements = newAchievements.filter(a =>
        a.requirement.type === 'pages' && a.requirement.value <= 100
      );

      expect(pageAchievements.length).toBeGreaterThan(0);
    });

    it('should track reading mode usage', () => {
      const store = useReaderStore();

      store.trackReadingModeUsage('double');
      store.trackReadingModeUsage('list');

      const usedModes = JSON.parse(localStorage.getItem('usedReadingModes'));
      expect(usedModes).toContain('double');
      expect(usedModes).toContain('list');
    });

    it('should calculate achievement progress', () => {
      const store = useReaderStore();
      store.readingStats.totalPagesRead = 50;

      // For 100-page achievement, should be 50% progress
      const progress = store.getAchievementProgress('page_turner');
      expect(progress).toBe(50);
    });
  });

  describe('Theme Management', () => {
    it('should get theme definitions', () => {
      const store = useReaderStore();
      const themes = store.getThemeDefinitions();

      expect(themes).toHaveProperty('dark');
      expect(themes).toHaveProperty('light');
      expect(themes).toHaveProperty('sepia');
      expect(themes).toHaveProperty('night');
      expect(themes.dark).toHaveProperty('colors');
      expect(themes.dark).toHaveProperty('ui');
    });

    it('should get current theme', () => {
      const store = useReaderStore();
      const theme = store.getCurrentTheme();

      expect(theme).toHaveProperty('id');
      expect(theme).toHaveProperty('colors');
      expect(theme).toHaveProperty('ui');
    });

    it('should update theme', () => {
      const store = useReaderStore();
      const mockSetItem = vi.spyOn(Storage.prototype, 'setItem');

      store.updateTheme('sepia');

      expect(store.settings.theme).toBe('sepia');
      expect(mockSetItem).toHaveBeenCalledWith('readerTheme', 'sepia');
    });

    it('should create custom theme', () => {
      const store = useReaderStore();
      const customizations = {
        colors: { background: '#123456' },
        ui: { toolbarBg: 'rgba(18, 52, 86, 0.9)' }
      };

      const customTheme = store.createCustomTheme('dark', customizations);

      expect(customTheme.id).toBe('custom');
      expect(customTheme.colors.background).toBe('#123456');
      expect(store.settings.theme).toBe('custom');
    });

    it('should export theme', () => {
      const store = useReaderStore();
      const exportData = store.exportTheme();
      const parsed = JSON.parse(exportData);

      expect(parsed).toHaveProperty('theme');
      expect(parsed).toHaveProperty('typography');
      expect(parsed).toHaveProperty('displayOptions');
      expect(parsed).toHaveProperty('version');
    });

    it('should import theme', () => {
      const store = useReaderStore();
      const themeData = {
        theme: {
          id: 'custom',
          colors: { background: '#654321' }
        },
        typography: { fontSize: '18px' }
      };

      const success = store.importTheme(themeData);

      expect(success).toBe(true);
      expect(store.settings.customTheme.colors.background).toBe('#654321');
      expect(store.settings.typography.fontSize).toBe('18px');
    });
  });

  describe('Typography and Display Options', () => {
    it('should update typography', () => {
      const store = useReaderStore();
      const mockSetItem = vi.spyOn(Storage.prototype, 'setItem');

      store.updateTypography({ fontSize: '20px', lineHeight: '1.8' });

      expect(store.settings.typography.fontSize).toBe('20px');
      expect(store.settings.typography.lineHeight).toBe('1.8');
      expect(mockSetItem).toHaveBeenCalledWith('typography', JSON.stringify(store.settings.typography));
    });

    it('should update display options', () => {
      const store = useReaderStore();
      const mockSetItem = vi.spyOn(Storage.prototype, 'setItem');

      store.updateDisplayOptions({ pageMargin: 30, showShadows: false });

      expect(store.settings.displayOptions.pageMargin).toBe(30);
      expect(store.settings.displayOptions.showShadows).toBe(false);
      expect(mockSetItem).toHaveBeenCalledWith('displayOptions', JSON.stringify(store.settings.displayOptions));
    });
  });

  describe('UI Layout', () => {
    it('should get UI layout definitions', () => {
      const store = useReaderStore();
      const layouts = store.getUILayoutDefinitions();

      expect(layouts).toHaveProperty('default');
      expect(layouts).toHaveProperty('minimal');
      expect(layouts).toHaveProperty('immersive');
      expect(layouts.default).toHaveProperty('toolbar');
      expect(layouts.default).toHaveProperty('pageNumbers');
    });

    it('should get current UI layout', () => {
      const store = useReaderStore();
      const layout = store.getCurrentUILayout();

      expect(layout).toHaveProperty('id');
      expect(layout).toHaveProperty('toolbar');
      expect(layout).toHaveProperty('pageNumbers');
    });

    it('should update UI layout', () => {
      const store = useReaderStore();
      const mockSetItem = vi.spyOn(Storage.prototype, 'setItem');

      store.updateUILayout('minimal');

      expect(store.settings.uiLayout).toBe('minimal');
      expect(mockSetItem).toHaveBeenCalledWith('uiLayout', 'minimal');
    });
  });
});
