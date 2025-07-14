/**
 * Comprehensive caching system for API responses, images, and computed data
 */

class CacheManager {
  constructor() {
    this.caches = new Map();
    this.defaultTTL = 5 * 60 * 1000; // 5 minutes
    this.maxSize = 100; // Maximum items per cache
    this.cleanupInterval = 60 * 1000; // 1 minute
    
    // Start cleanup interval
    this.startCleanup();
  }

  /**
   * Create or get a cache instance
   */
  getCache(name, options = {}) {
    if (!this.caches.has(name)) {
      this.caches.set(name, new Cache({
        name,
        ttl: options.ttl || this.defaultTTL,
        maxSize: options.maxSize || this.maxSize,
        storage: options.storage || 'memory',
        serialize: options.serialize || false
      }));
    }
    return this.caches.get(name);
  }

  /**
   * Start periodic cleanup
   */
  startCleanup() {
    setInterval(() => {
      for (const cache of this.caches.values()) {
        cache.cleanup();
      }
    }, this.cleanupInterval);
  }

  /**
   * Clear all caches
   */
  clearAll() {
    for (const cache of this.caches.values()) {
      cache.clear();
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const stats = {};
    for (const [name, cache] of this.caches.entries()) {
      stats[name] = cache.getStats();
    }
    return stats;
  }
}

class Cache {
  constructor(options = {}) {
    this.name = options.name || 'default';
    this.ttl = options.ttl || 5 * 60 * 1000;
    this.maxSize = options.maxSize || 100;
    this.storage = options.storage || 'memory';
    this.serialize = options.serialize || false;
    
    this.data = new Map();
    this.timestamps = new Map();
    this.accessCount = new Map();
    this.hitCount = 0;
    this.missCount = 0;
    
    // Initialize persistent storage if needed
    if (this.storage === 'localStorage' || this.storage === 'sessionStorage') {
      this.loadFromStorage();
    }
  }

  /**
   * Set a value in the cache
   */
  set(key, value, ttl = null) {
    const actualTTL = ttl || this.ttl;
    const now = Date.now();
    
    // Serialize value if needed
    const storedValue = this.serialize ? JSON.stringify(value) : value;
    
    this.data.set(key, storedValue);
    this.timestamps.set(key, now + actualTTL);
    this.accessCount.set(key, 0);
    
    // Enforce max size using LRU
    if (this.data.size > this.maxSize) {
      this.evictLRU();
    }
    
    // Save to persistent storage if needed
    if (this.storage !== 'memory') {
      this.saveToStorage();
    }
  }

  /**
   * Get a value from the cache
   */
  get(key) {
    const now = Date.now();
    
    if (!this.data.has(key)) {
      this.missCount++;
      return null;
    }
    
    const expiry = this.timestamps.get(key);
    if (expiry && now > expiry) {
      this.delete(key);
      this.missCount++;
      return null;
    }
    
    this.hitCount++;
    this.accessCount.set(key, (this.accessCount.get(key) || 0) + 1);
    
    const value = this.data.get(key);
    return this.serialize ? JSON.parse(value) : value;
  }

  /**
   * Check if a key exists and is not expired
   */
  has(key) {
    const now = Date.now();
    
    if (!this.data.has(key)) {
      return false;
    }
    
    const expiry = this.timestamps.get(key);
    if (expiry && now > expiry) {
      this.delete(key);
      return false;
    }
    
    return true;
  }

  /**
   * Delete a key from the cache
   */
  delete(key) {
    this.data.delete(key);
    this.timestamps.delete(key);
    this.accessCount.delete(key);
    
    if (this.storage !== 'memory') {
      this.saveToStorage();
    }
  }

  /**
   * Clear all cache data
   */
  clear() {
    this.data.clear();
    this.timestamps.clear();
    this.accessCount.clear();
    this.hitCount = 0;
    this.missCount = 0;
    
    if (this.storage !== 'memory') {
      this.clearStorage();
    }
  }

  /**
   * Get or set with a factory function
   */
  async getOrSet(key, factory, ttl = null) {
    let value = this.get(key);
    
    if (value === null) {
      value = await factory();
      if (value !== null && value !== undefined) {
        this.set(key, value, ttl);
      }
    }
    
    return value;
  }

  /**
   * Cleanup expired entries
   */
  cleanup() {
    const now = Date.now();
    const expiredKeys = [];
    
    for (const [key, expiry] of this.timestamps.entries()) {
      if (expiry && now > expiry) {
        expiredKeys.push(key);
      }
    }
    
    for (const key of expiredKeys) {
      this.delete(key);
    }
  }

  /**
   * Evict least recently used items
   */
  evictLRU() {
    // Find the least accessed item
    let lruKey = null;
    let minAccess = Infinity;
    
    for (const [key, accessCount] of this.accessCount.entries()) {
      if (accessCount < minAccess) {
        minAccess = accessCount;
        lruKey = key;
      }
    }
    
    if (lruKey) {
      this.delete(lruKey);
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const total = this.hitCount + this.missCount;
    return {
      name: this.name,
      size: this.data.size,
      maxSize: this.maxSize,
      hitCount: this.hitCount,
      missCount: this.missCount,
      hitRate: total > 0 ? (this.hitCount / total) * 100 : 0,
      ttl: this.ttl,
      storage: this.storage
    };
  }

  /**
   * Load cache from persistent storage
   */
  loadFromStorage() {
    try {
      const storage = this.storage === 'localStorage' ? localStorage : sessionStorage;
      const data = storage.getItem(`cache_${this.name}`);
      
      if (data) {
        const parsed = JSON.parse(data);
        this.data = new Map(parsed.data);
        this.timestamps = new Map(parsed.timestamps);
        this.accessCount = new Map(parsed.accessCount);
        this.hitCount = parsed.hitCount || 0;
        this.missCount = parsed.missCount || 0;
        
        // Cleanup expired items
        this.cleanup();
      }
    } catch (error) {
      console.warn(`Failed to load cache ${this.name} from storage:`, error);
    }
  }

  /**
   * Save cache to persistent storage
   */
  saveToStorage() {
    try {
      const storage = this.storage === 'localStorage' ? localStorage : sessionStorage;
      const data = {
        data: Array.from(this.data.entries()),
        timestamps: Array.from(this.timestamps.entries()),
        accessCount: Array.from(this.accessCount.entries()),
        hitCount: this.hitCount,
        missCount: this.missCount
      };
      
      storage.setItem(`cache_${this.name}`, JSON.stringify(data));
    } catch (error) {
      console.warn(`Failed to save cache ${this.name} to storage:`, error);
    }
  }

  /**
   * Clear persistent storage
   */
  clearStorage() {
    try {
      const storage = this.storage === 'localStorage' ? localStorage : sessionStorage;
      storage.removeItem(`cache_${this.name}`);
    } catch (error) {
      console.warn(`Failed to clear cache ${this.name} from storage:`, error);
    }
  }
}

// Create global cache manager
const cacheManager = new CacheManager();

// Pre-configured cache instances
export const apiCache = cacheManager.getCache('api', {
  ttl: 5 * 60 * 1000, // 5 minutes
  maxSize: 200,
  storage: 'sessionStorage',
  serialize: true
});

export const imageCache = cacheManager.getCache('images', {
  ttl: 30 * 60 * 1000, // 30 minutes
  maxSize: 500,
  storage: 'memory'
});

export const metadataCache = cacheManager.getCache('metadata', {
  ttl: 15 * 60 * 1000, // 15 minutes
  maxSize: 1000,
  storage: 'localStorage',
  serialize: true
});

export const searchCache = cacheManager.getCache('search', {
  ttl: 10 * 60 * 1000, // 10 minutes
  maxSize: 100,
  storage: 'sessionStorage',
  serialize: true
});

// Utility functions
export const cache = {
  /**
   * Create a cached version of an async function
   */
  memoize(fn, cacheInstance = apiCache, keyGenerator = (...args) => JSON.stringify(args)) {
    return async (...args) => {
      const key = keyGenerator(...args);
      return await cacheInstance.getOrSet(key, () => fn(...args));
    };
  },

  /**
   * Cache API responses with automatic key generation
   */
  cacheApiCall(url, options = {}) {
    const key = `${options.method || 'GET'}_${url}_${JSON.stringify(options.params || {})}`;
    return apiCache.getOrSet(key, async () => {
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    });
  },

  /**
   * Cache image loading
   */
  async cacheImage(url) {
    return await imageCache.getOrSet(url, () => {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = url;
      });
    });
  },

  /**
   * Get cache statistics
   */
  getStats() {
    return cacheManager.getStats();
  },

  /**
   * Clear all caches
   */
  clearAll() {
    cacheManager.clearAll();
  }
};

export default cacheManager;
