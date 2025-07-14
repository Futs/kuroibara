/**
 * Comprehensive performance optimization service
 */

import { perf, memory } from "../utils/performance";
import { cache } from "../utils/cache";
import { cdn } from "../utils/cdn";
import backgroundProcessor from "../workers/backgroundProcessor";

class PerformanceService {
  constructor() {
    this.isInitialized = false;
    this.optimizations = new Map();
    this.metrics = new Map();
    this.thresholds = {
      memoryUsage: 80, // Percentage
      loadTime: 3000, // Milliseconds
      imageSize: 500 * 1024, // 500KB
      bundleSize: 2 * 1024 * 1024, // 2MB
      longTask: 50, // Milliseconds
    };

    this.init();
  }

  /**
   * Initialize performance service
   */
  async init() {
    if (this.isInitialized) return;

    try {
      // Set up performance monitoring
      this.setupPerformanceMonitoring();

      // Initialize optimizations
      this.initializeOptimizations();

      // Set up memory monitoring
      this.setupMemoryMonitoring();

      // Configure CDN
      this.configureCDN();

      // Set up cache strategies
      this.setupCacheStrategies();

      this.isInitialized = true;
      console.log("Performance service initialized");
    } catch (error) {
      console.error("Failed to initialize performance service:", error);
    }
  }

  /**
   * Set up performance monitoring
   */
  setupPerformanceMonitoring() {
    // Monitor page load performance
    if ("PerformanceObserver" in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.recordMetric("navigation", {
            name: entry.name,
            duration: entry.duration,
            type: entry.entryType,
          });

          // Check against thresholds
          if (entry.duration > this.thresholds.loadTime) {
            this.triggerOptimization("slow-load", { duration: entry.duration });
          }
        }
      });

      observer.observe({ entryTypes: ["navigation", "resource"] });
    }

    // Monitor long tasks
    if ("longtask" in PerformanceObserver.supportedEntryTypes) {
      const longTaskObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.duration > this.thresholds.longTask) {
            this.recordMetric("longtask", {
              duration: entry.duration,
              startTime: entry.startTime,
            });

            this.triggerOptimization("long-task", { duration: entry.duration });
          }
        }
      });

      longTaskObserver.observe({ entryTypes: ["longtask"] });
    }
  }

  /**
   * Set up memory monitoring
   */
  setupMemoryMonitoring() {
    if ("memory" in performance) {
      const checkMemory = () => {
        const usage = memory.getUsage();
        if (usage && usage.percentage > this.thresholds.memoryUsage) {
          this.triggerOptimization("high-memory", usage);
        }
      };

      // Check memory every 30 seconds
      setInterval(checkMemory, 30000);
    }
  }

  /**
   * Initialize performance optimizations
   */
  initializeOptimizations() {
    // Image optimization
    this.optimizations.set("image-optimization", {
      name: "Image Optimization",
      trigger: ["slow-load", "high-memory"],
      action: this.optimizeImages.bind(this),
      enabled: true,
    });

    // Bundle optimization
    this.optimizations.set("bundle-optimization", {
      name: "Bundle Optimization",
      trigger: ["slow-load"],
      action: this.optimizeBundle.bind(this),
      enabled: true,
    });

    // Memory cleanup
    this.optimizations.set("memory-cleanup", {
      name: "Memory Cleanup",
      trigger: ["high-memory"],
      action: this.cleanupMemory.bind(this),
      enabled: true,
    });

    // Cache optimization
    this.optimizations.set("cache-optimization", {
      name: "Cache Optimization",
      trigger: ["slow-load"],
      action: this.optimizeCache.bind(this),
      enabled: true,
    });

    // Background processing
    this.optimizations.set("background-processing", {
      name: "Background Processing",
      trigger: ["long-task"],
      action: this.moveToBackground.bind(this),
      enabled: true,
    });
  }

  /**
   * Configure CDN settings
   */
  configureCDN() {
    // Detect connection speed and adjust quality
    if ("connection" in navigator) {
      const connection = navigator.connection;
      let quality = 80;

      switch (connection.effectiveType) {
        case "slow-2g":
        case "2g":
          quality = 40;
          break;
        case "3g":
          quality = 60;
          break;
        case "4g":
        default:
          quality = 80;
          break;
      }

      cdn.config({ defaultQuality: quality });
    }
  }

  /**
   * Set up cache strategies
   */
  setupCacheStrategies() {
    // Configure cache TTLs based on content type
    const strategies = {
      images: { ttl: 30 * 60 * 1000, maxSize: 500 }, // 30 minutes
      api: { ttl: 5 * 60 * 1000, maxSize: 200 }, // 5 minutes
      metadata: { ttl: 15 * 60 * 1000, maxSize: 1000 }, // 15 minutes
      search: { ttl: 10 * 60 * 1000, maxSize: 100 }, // 10 minutes
    };

    // Apply strategies
    for (const [type, config] of Object.entries(strategies)) {
      cache[`${type}Cache`]?.updateConfig?.(config);
    }
  }

  /**
   * Record performance metric
   */
  recordMetric(category, data) {
    if (!this.metrics.has(category)) {
      this.metrics.set(category, []);
    }

    const metrics = this.metrics.get(category);
    metrics.push({
      ...data,
      timestamp: Date.now(),
    });

    // Keep only last 100 entries
    if (metrics.length > 100) {
      metrics.splice(0, metrics.length - 100);
    }
  }

  /**
   * Trigger optimization
   */
  triggerOptimization(trigger, data) {
    for (const [id, optimization] of this.optimizations.entries()) {
      if (optimization.enabled && optimization.trigger.includes(trigger)) {
        try {
          optimization.action(data);
          console.log(`Triggered optimization: ${optimization.name}`);
        } catch (error) {
          console.error(`Optimization ${optimization.name} failed:`, error);
        }
      }
    }
  }

  /**
   * Optimize images
   */
  async optimizeImages(data) {
    // Reduce image quality for slow connections
    if (data.duration > this.thresholds.loadTime) {
      cdn.config({ defaultQuality: 60 });
    }

    // Preload critical images
    const criticalImages = this.getCriticalImages();
    if (criticalImages.length > 0) {
      await cdn.preload(criticalImages, { quality: 60, width: 400 });
    }
  }

  /**
   * Optimize bundle
   */
  optimizeBundle(data) {
    // Enable code splitting hints
    if (window.__webpack_require__) {
      // Webpack-specific optimizations
      console.log("Bundle optimization triggered");
    }

    // Lazy load non-critical components
    this.enableLazyLoading();
  }

  /**
   * Clean up memory
   */
  cleanupMemory(data) {
    // Clear old cache entries
    cache.clearAll();

    // Force garbage collection if available
    memory.gc();

    // Clear unused images
    this.clearUnusedImages();

    console.log("Memory cleanup performed");
  }

  /**
   * Optimize cache
   */
  optimizeCache(data) {
    // Reduce cache sizes
    const newSizes = {
      images: 250,
      api: 100,
      metadata: 500,
      search: 50,
    };

    for (const [type, size] of Object.entries(newSizes)) {
      cache[`${type}Cache`]?.updateConfig?.({ maxSize: size });
    }
  }

  /**
   * Move heavy operations to background
   */
  async moveToBackground(data) {
    // Move duplicate detection to background
    if (window.pendingDuplicateDetection) {
      await backgroundProcessor.detectDuplicates(
        window.pendingDuplicateDetection,
        { threshold: 0.8 },
      );
      window.pendingDuplicateDetection = null;
    }

    // Move statistics calculation to background
    if (window.pendingStatistics) {
      await backgroundProcessor.calculateStats(window.pendingStatistics);
      window.pendingStatistics = null;
    }
  }

  /**
   * Get critical images for preloading
   */
  getCriticalImages() {
    const images = [];

    // Get visible manga covers
    const visibleCards = document.querySelectorAll(".manga-card img[src]");
    visibleCards.forEach((img) => {
      if (img.src && this.isInViewport(img)) {
        images.push(img.src);
      }
    });

    return images.slice(0, 10); // Limit to 10 images
  }

  /**
   * Check if element is in viewport
   */
  isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= window.innerHeight &&
      rect.right <= window.innerWidth
    );
  }

  /**
   * Enable lazy loading for components
   */
  enableLazyLoading() {
    // Add lazy loading attributes to images
    const images = document.querySelectorAll("img:not([loading])");
    images.forEach((img) => {
      img.loading = "lazy";
    });
  }

  /**
   * Clear unused images from memory
   */
  clearUnusedImages() {
    // Remove images that are not visible
    const images = document.querySelectorAll("img");
    images.forEach((img) => {
      if (!this.isInViewport(img) && img.src) {
        // Create a small placeholder
        const placeholder =
          "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMSIgaGVpZ2h0PSIxIiB2aWV3Qm94PSIwIDAgMSAxIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxIiBoZWlnaHQ9IjEiIGZpbGw9IiNGM0Y0RjYiLz48L3N2Zz4=";
        img.dataset.originalSrc = img.src;
        img.src = placeholder;
      }
    });
  }

  /**
   * Get performance metrics
   */
  getMetrics() {
    return {
      performance: this.metrics,
      cache: cache.getStats(),
      memory: memory.getUsage(),
      cdn: cdn.status(),
    };
  }

  /**
   * Get optimization status
   */
  getOptimizationStatus() {
    const status = {};
    for (const [id, optimization] of this.optimizations.entries()) {
      status[id] = {
        name: optimization.name,
        enabled: optimization.enabled,
        triggers: optimization.trigger,
      };
    }
    return status;
  }

  /**
   * Enable/disable optimization
   */
  toggleOptimization(id, enabled) {
    if (this.optimizations.has(id)) {
      this.optimizations.get(id).enabled = enabled;
    }
  }

  /**
   * Update thresholds
   */
  updateThresholds(newThresholds) {
    this.thresholds = { ...this.thresholds, ...newThresholds };
  }
}

// Create singleton instance
const performanceService = new PerformanceService();

export default performanceService;
