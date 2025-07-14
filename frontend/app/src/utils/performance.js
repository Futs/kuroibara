/**
 * Performance monitoring and optimization utilities
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
    this.observers = new Map();
    this.budgets = new Map();
    this.isEnabled =
      process.env.NODE_ENV === "development" ||
      localStorage.getItem("enablePerformanceMonitoring") === "true";

    if (this.isEnabled) {
      this.initializeObservers();
    }
  }

  /**
   * Initialize performance observers
   */
  initializeObservers() {
    // Performance Observer for navigation timing
    if ("PerformanceObserver" in window) {
      try {
        const navObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordMetric("navigation", {
              type: entry.entryType,
              name: entry.name,
              duration: entry.duration,
              startTime: entry.startTime,
              ...entry,
            });
          }
        });
        navObserver.observe({ entryTypes: ["navigation"] });
        this.observers.set("navigation", navObserver);

        // Resource timing observer
        const resourceObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordMetric("resource", {
              type: entry.entryType,
              name: entry.name,
              duration: entry.duration,
              transferSize: entry.transferSize,
              encodedBodySize: entry.encodedBodySize,
              decodedBodySize: entry.decodedBodySize,
            });
          }
        });
        resourceObserver.observe({ entryTypes: ["resource"] });
        this.observers.set("resource", resourceObserver);

        // Measure observer for custom metrics
        const measureObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordMetric("measure", {
              name: entry.name,
              duration: entry.duration,
              startTime: entry.startTime,
            });
          }
        });
        measureObserver.observe({ entryTypes: ["measure"] });
        this.observers.set("measure", measureObserver);

        // Long task observer
        if ("longtask" in PerformanceObserver.supportedEntryTypes) {
          const longTaskObserver = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              this.recordMetric("longtask", {
                duration: entry.duration,
                startTime: entry.startTime,
                attribution: entry.attribution,
              });

              // Warn about long tasks
              console.warn(`Long task detected: ${entry.duration}ms`, entry);
            }
          });
          longTaskObserver.observe({ entryTypes: ["longtask"] });
          this.observers.set("longtask", longTaskObserver);
        }
      } catch (error) {
        console.warn("Failed to initialize performance observers:", error);
      }
    }

    // Memory monitoring
    if ("memory" in performance) {
      setInterval(() => {
        this.recordMetric("memory", {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
          timestamp: Date.now(),
        });
      }, 5000); // Every 5 seconds
    }
  }

  /**
   * Record a performance metric
   */
  recordMetric(category, data) {
    if (!this.isEnabled) return;

    if (!this.metrics.has(category)) {
      this.metrics.set(category, []);
    }

    const metrics = this.metrics.get(category);
    metrics.push({
      ...data,
      timestamp: Date.now(),
    });

    // Keep only last 100 entries per category
    if (metrics.length > 100) {
      metrics.splice(0, metrics.length - 100);
    }

    // Check performance budgets
    this.checkBudgets(category, data);
  }

  /**
   * Start timing a custom operation
   */
  startTiming(name) {
    if (!this.isEnabled) return;
    performance.mark(`${name}-start`);
  }

  /**
   * End timing a custom operation
   */
  endTiming(name) {
    if (!this.isEnabled) return;

    try {
      performance.mark(`${name}-end`);
      performance.measure(name, `${name}-start`, `${name}-end`);
    } catch (error) {
      console.warn(`Failed to measure ${name}:`, error);
    }
  }

  /**
   * Time a function execution
   */
  timeFunction(name, fn) {
    if (!this.isEnabled) return fn();

    this.startTiming(name);
    const result = fn();

    if (result instanceof Promise) {
      return result.finally(() => this.endTiming(name));
    } else {
      this.endTiming(name);
      return result;
    }
  }

  /**
   * Set performance budgets
   */
  setBudget(category, budget) {
    this.budgets.set(category, budget);
  }

  /**
   * Check if metrics exceed budgets
   */
  checkBudgets(category, data) {
    const budget = this.budgets.get(category);
    if (!budget) return;

    for (const [key, limit] of Object.entries(budget)) {
      if (data[key] && data[key] > limit) {
        console.warn(
          `Performance budget exceeded for ${category}.${key}: ${data[key]} > ${limit}`,
        );

        // Emit custom event for budget violations
        window.dispatchEvent(
          new CustomEvent("performance-budget-exceeded", {
            detail: { category, key, value: data[key], limit },
          }),
        );
      }
    }
  }

  /**
   * Get metrics for a category
   */
  getMetrics(category) {
    return this.metrics.get(category) || [];
  }

  /**
   * Get all metrics
   */
  getAllMetrics() {
    const result = {};
    for (const [category, metrics] of this.metrics.entries()) {
      result[category] = metrics;
    }
    return result;
  }

  /**
   * Get performance summary
   */
  getSummary() {
    const summary = {};

    for (const [category, metrics] of this.metrics.entries()) {
      if (metrics.length === 0) continue;

      const durations = metrics
        .filter((m) => typeof m.duration === "number")
        .map((m) => m.duration);

      if (durations.length > 0) {
        summary[category] = {
          count: metrics.length,
          avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
          minDuration: Math.min(...durations),
          maxDuration: Math.max(...durations),
          totalDuration: durations.reduce((a, b) => a + b, 0),
        };
      }
    }

    return summary;
  }

  /**
   * Clear all metrics
   */
  clear() {
    this.metrics.clear();
  }

  /**
   * Export metrics as JSON
   */
  export() {
    return JSON.stringify(
      {
        metrics: this.getAllMetrics(),
        summary: this.getSummary(),
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      },
      null,
      2,
    );
  }

  /**
   * Cleanup observers
   */
  destroy() {
    for (const observer of this.observers.values()) {
      observer.disconnect();
    }
    this.observers.clear();
  }
}

// Create singleton instance
const performanceMonitor = new PerformanceMonitor();

// Set default budgets
performanceMonitor.setBudget("navigation", {
  duration: 3000, // 3 seconds for navigation
  domContentLoadedEventEnd: 2000, // 2 seconds for DOM ready
  loadEventEnd: 5000, // 5 seconds for full load
});

performanceMonitor.setBudget("resource", {
  duration: 1000, // 1 second for resource loading
});

performanceMonitor.setBudget("measure", {
  duration: 100, // 100ms for custom operations
});

performanceMonitor.setBudget("longtask", {
  duration: 50, // 50ms for long tasks
});

// Utility functions
export const perf = {
  /**
   * Start timing an operation
   */
  start: (name) => performanceMonitor.startTiming(name),

  /**
   * End timing an operation
   */
  end: (name) => performanceMonitor.endTiming(name),

  /**
   * Time a function
   */
  time: (name, fn) => performanceMonitor.timeFunction(name, fn),

  /**
   * Record a custom metric
   */
  record: (category, data) => performanceMonitor.recordMetric(category, data),

  /**
   * Get metrics
   */
  getMetrics: (category) => performanceMonitor.getMetrics(category),

  /**
   * Get summary
   */
  getSummary: () => performanceMonitor.getSummary(),

  /**
   * Export all data
   */
  export: () => performanceMonitor.export(),

  /**
   * Clear metrics
   */
  clear: () => performanceMonitor.clear(),
};

// Memory management utilities
export const memory = {
  /**
   * Get current memory usage
   */
  getUsage() {
    if ("memory" in performance) {
      return {
        used: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        limit: performance.memory.jsHeapSizeLimit,
        percentage:
          (performance.memory.usedJSHeapSize /
            performance.memory.jsHeapSizeLimit) *
          100,
      };
    }
    return null;
  },

  /**
   * Force garbage collection (if available)
   */
  gc() {
    if (window.gc) {
      window.gc();
    }
  },

  /**
   * Monitor memory usage
   */
  monitor(callback, interval = 5000) {
    return setInterval(() => {
      const usage = this.getUsage();
      if (usage) {
        callback(usage);
      }
    }, interval);
  },
};

// Image optimization utilities
export const imageOptimizer = {
  /**
   * Get optimized image URL with quality and size parameters
   */
  getOptimizedUrl(url, options = {}) {
    if (!url) return url;

    try {
      const urlObj = new URL(url, window.location.origin);

      if (options.quality) {
        urlObj.searchParams.set("quality", options.quality);
      }

      if (options.width) {
        urlObj.searchParams.set("w", options.width);
      }

      if (options.height) {
        urlObj.searchParams.set("h", options.height);
      }

      if (options.format) {
        urlObj.searchParams.set("format", options.format);
      }

      return urlObj.toString();
    } catch (error) {
      console.warn("Failed to optimize image URL:", error);
      return url;
    }
  },

  /**
   * Preload images with priority
   */
  preload(urls, priority = "low") {
    const promises = urls.map((url) => {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;

        // Set loading priority if supported
        if ("loading" in img) {
          img.loading = priority === "high" ? "eager" : "lazy";
        }

        img.src = url;
      });
    });

    return Promise.allSettled(promises);
  },
};

export default performanceMonitor;
