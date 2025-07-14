import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useLibraryStore } from '../library';

// Mock API
vi.mock('../../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

describe('Library Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('Basic Functionality', () => {
    it('should initialize with default state', () => {
      const store = useLibraryStore();
      
      expect(store.manga).toEqual([]);
      expect(store.loading).toBe(false);
      expect(store.error).toBe(null);
      expect(store.bulkOperationMode).toBe(false);
      expect(store.selectedManga.size).toBe(0);
    });

    it('should set filters', () => {
      const store = useLibraryStore();
      
      store.setFilters({ category: 'action', status: 'ongoing' });
      
      expect(store.filters.category).toBe('action');
      expect(store.filters.status).toBe('ongoing');
    });
  });

  describe('Advanced Filtering', () => {
    it('should filter by read status', () => {
      const store = useLibraryStore();
      store.manga = [
        { id: 1, read_status: 'reading', manga: { title: 'Test 1' } },
        { id: 2, read_status: 'completed', manga: { title: 'Test 2' } },
        { id: 3, read_status: 'unread', manga: { title: 'Test 3' } },
      ];
      
      store.setAdvancedFilter('readStatus', ['reading', 'completed']);
      const filtered = store.getFilteredManga;
      
      expect(filtered).toHaveLength(2);
      expect(filtered.map(m => m.id)).toEqual([1, 2]);
    });

    it('should filter by rating range', () => {
      const store = useLibraryStore();
      store.manga = [
        { id: 1, rating: 8.5, manga: { title: 'Test 1' } },
        { id: 2, rating: 6.0, manga: { title: 'Test 2' } },
        { id: 3, rating: 9.2, manga: { title: 'Test 3' } },
      ];
      
      store.setAdvancedFilter('rating', { min: 7, max: 9 });
      const filtered = store.getFilteredManga;
      
      expect(filtered).toHaveLength(1);
      expect(filtered[0].id).toBe(1);
    });

    it('should filter by genres', () => {
      const store = useLibraryStore();
      store.manga = [
        { id: 1, manga: { title: 'Test 1', genres: [{ name: 'Action' }, { name: 'Adventure' }] } },
        { id: 2, manga: { title: 'Test 2', genres: [{ name: 'Romance' }] } },
        { id: 3, manga: { title: 'Test 3', genres: [{ name: 'Action' }, { name: 'Comedy' }] } },
      ];
      
      store.setAdvancedFilter('genres', ['Action']);
      const filtered = store.getFilteredManga;
      
      expect(filtered).toHaveLength(2);
      expect(filtered.map(m => m.id)).toEqual([1, 3]);
    });
  });

  describe('Bulk Operations', () => {
    it('should toggle bulk mode', () => {
      const store = useLibraryStore();
      
      expect(store.bulkOperationMode).toBe(false);
      store.toggleBulkMode();
      expect(store.bulkOperationMode).toBe(true);
      
      store.toggleBulkMode();
      expect(store.bulkOperationMode).toBe(false);
      expect(store.selectedManga.size).toBe(0);
    });

    it('should select and deselect manga', () => {
      const store = useLibraryStore();
      
      store.selectManga('manga1');
      store.selectManga('manga2');
      
      expect(store.selectedManga.has('manga1')).toBe(true);
      expect(store.selectedManga.has('manga2')).toBe(true);
      expect(store.getSelectedCount).toBe(2);
      
      store.deselectManga('manga1');
      expect(store.selectedManga.has('manga1')).toBe(false);
      expect(store.getSelectedCount).toBe(1);
    });

    it('should select all manga', () => {
      const store = useLibraryStore();
      store.manga = [
        { id: 'manga1', manga: { title: 'Test 1' } },
        { id: 'manga2', manga: { title: 'Test 2' } },
        { id: 'manga3', manga: { title: 'Test 3' } },
      ];
      
      store.selectAllManga();
      expect(store.getSelectedCount).toBe(3);
      expect(store.selectedManga.has('manga1')).toBe(true);
      expect(store.selectedManga.has('manga2')).toBe(true);
      expect(store.selectedManga.has('manga3')).toBe(true);
    });
  });

  describe('Statistics', () => {
    it('should calculate local statistics', () => {
      const store = useLibraryStore();
      store.manga = [
        { 
          id: 1, 
          read_status: 'reading', 
          is_favorite: true,
          manga: { 
            title: 'Test 1',
            genres: [{ name: 'Action' }, { name: 'Adventure' }],
            authors: [{ name: 'Author 1' }]
          } 
        },
        { 
          id: 2, 
          read_status: 'completed', 
          is_favorite: false,
          manga: { 
            title: 'Test 2',
            genres: [{ name: 'Romance' }],
            authors: [{ name: 'Author 2' }]
          } 
        },
        { 
          id: 3, 
          read_status: 'reading', 
          is_favorite: true,
          manga: { 
            title: 'Test 3',
            genres: [{ name: 'Action' }],
            authors: [{ name: 'Author 1' }]
          } 
        },
      ];
      
      const stats = store.calculateLocalStatistics();
      
      expect(stats.total).toBe(3);
      expect(stats.reading).toBe(2);
      expect(stats.completed).toBe(1);
      expect(stats.favorites).toBe(2);
      expect(stats.genreDistribution.Action).toBe(2);
      expect(stats.genreDistribution.Romance).toBe(1);
      expect(stats.authorDistribution['Author 1']).toBe(2);
    });
  });

  describe('Custom Tags', () => {
    it('should create custom tag', () => {
      const store = useLibraryStore();
      const mockSetItem = vi.spyOn(Storage.prototype, 'setItem');
      
      store.createCustomTag({
        name: 'Test Tag',
        color: '#FF0000',
        description: 'Test description'
      });
      
      expect(store.customTags).toHaveLength(1);
      expect(store.customTags[0].name).toBe('Test Tag');
      expect(store.customTags[0].color).toBe('#FF0000');
      expect(mockSetItem).toHaveBeenCalledWith('customTags', expect.any(String));
    });

    it('should update custom tag', () => {
      const store = useLibraryStore();
      store.customTags = [
        { id: '1', name: 'Test Tag', color: '#FF0000' }
      ];
      
      store.updateCustomTag('1', { name: 'Updated Tag', color: '#00FF00' });
      
      expect(store.customTags[0].name).toBe('Updated Tag');
      expect(store.customTags[0].color).toBe('#00FF00');
    });

    it('should delete custom tag', () => {
      const store = useLibraryStore();
      store.customTags = [
        { id: '1', name: 'Test Tag', color: '#FF0000' },
        { id: '2', name: 'Another Tag', color: '#0000FF' }
      ];
      
      store.deleteCustomTag('1');
      
      expect(store.customTags).toHaveLength(1);
      expect(store.customTags[0].id).toBe('2');
    });
  });

  describe('Duplicate Detection', () => {
    it('should find local duplicates', () => {
      const store = useLibraryStore();
      store.manga = [
        { id: 1, manga: { title: 'Test Manga', authors: [{ name: 'Author 1' }] } },
        { id: 2, manga: { title: 'Test manga', authors: [{ name: 'Author 1' }] } }, // Similar title
        { id: 3, manga: { title: 'Different Manga', authors: [{ name: 'Author 2' }] } },
      ];
      
      const duplicates = store.findLocalDuplicates();
      
      expect(duplicates).toHaveLength(1);
      expect(duplicates[0].items).toHaveLength(2);
      expect(duplicates[0].similarity).toBeGreaterThan(0);
    });

    it('should calculate similarity score', () => {
      const store = useLibraryStore();
      
      const manga1 = {
        title: 'Test Manga',
        authors: [{ name: 'Author 1' }],
        genres: [{ name: 'Action' }],
        description: 'This is a test manga description'
      };
      
      const manga2 = {
        title: 'Test Manga',
        authors: [{ name: 'Author 1' }],
        genres: [{ name: 'Action' }],
        description: 'This is a test manga description'
      };
      
      const similarity = store.calculateSimilarity(manga1, manga2);
      expect(similarity).toBe(100); // Perfect match
    });
  });

  describe('Metadata Management', () => {
    it('should save and load searches', () => {
      const store = useLibraryStore();
      const mockSetItem = vi.spyOn(Storage.prototype, 'setItem');
      
      const savedSearch = store.saveSearch('test query', { genre: 'action' });
      
      expect(savedSearch.name).toBe('test query');
      expect(savedSearch.query).toBe('test query');
      expect(savedSearch.filters.genre).toBe('action');
      expect(mockSetItem).toHaveBeenCalledWith('savedSearches', expect.any(String));
    });

    it('should export library data', async () => {
      const store = useLibraryStore();
      store.manga = [{ id: 1, manga: { title: 'Test' } }];
      store.customTags = [{ id: '1', name: 'Tag' }];
      
      const exportData = await store.exportLibrary();
      const parsed = JSON.parse(exportData);
      
      expect(parsed.manga).toHaveLength(1);
      expect(parsed.customTags).toHaveLength(1);
      expect(parsed.version).toBe('1.0');
    });
  });
});
