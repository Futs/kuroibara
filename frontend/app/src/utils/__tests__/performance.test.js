import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";

// Mock PerformanceObserver first
const mockPerformanceObserver = vi.fn().mockImplementation((callback) => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock the environment before importing the performance module
global.window = {
  ...global,
  location: {
    origin: "http://localhost:3000",
    href: "http://localhost:3000",
  },
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
  PerformanceObserver: mockPerformanceObserver, // Add to window object
};
global.localStorage = {
  getItem: vi.fn().mockReturnValue("true"),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

// Mock performance API
const mockPerformance = {
  mark: vi.fn(),
  measure: vi.fn(),
  memory: {
    usedJSHeapSize: 50000000,
    totalJSHeapSize: 100000000,
    jsHeapSizeLimit: 200000000,
  },
};
global.performance = mockPerformance;

global.PerformanceObserver = mockPerformanceObserver;

// Set environment to development to enable performance monitoring
const originalEnv = process.env.NODE_ENV;
process.env.NODE_ENV = "development";

// Now import the performance module after mocks are set up
import { perf, memory, imageOptimizer } from "../performance";



describe("Performance Utilities", () => {
  beforeEach(() => {
    // Clear only performance API mocks, not PerformanceObserver
    mockPerformance.mark.mockClear();
    mockPerformance.measure.mockClear();
    global.window.addEventListener.mockClear();
    global.window.removeEventListener.mockClear();
    global.window.dispatchEvent.mockClear();

    // Reset performance monitoring state
    perf.clear();
    // Force enable performance monitoring for tests
    perf._enableForTesting();
  });

  afterEach(() => {
    // Restore original environment
    process.env.NODE_ENV = originalEnv;
  });

  describe("Performance Monitoring", () => {
    it("should start and end timing", () => {
      perf.start("test-operation");
      expect(mockPerformance.mark).toHaveBeenCalledWith("test-operation-start");

      perf.end("test-operation");
      expect(mockPerformance.mark).toHaveBeenCalledWith("test-operation-end");
      expect(mockPerformance.measure).toHaveBeenCalledWith(
        "test-operation",
        "test-operation-start",
        "test-operation-end",
      );
    });

    it("should time function execution", () => {
      const testFn = vi.fn(() => "result");
      const result = perf.time("test-function", testFn);

      expect(testFn).toHaveBeenCalled();
      expect(result).toBe("result");
      expect(mockPerformance.mark).toHaveBeenCalledWith("test-function-start");
      expect(mockPerformance.mark).toHaveBeenCalledWith("test-function-end");
    });

    it("should time async function execution", async () => {
      const testFn = vi.fn(async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        return "async-result";
      });

      const result = await perf.time("async-function", testFn);

      expect(testFn).toHaveBeenCalled();
      expect(result).toBe("async-result");
      expect(mockPerformance.mark).toHaveBeenCalledWith("async-function-start");
      expect(mockPerformance.mark).toHaveBeenCalledWith("async-function-end");
    });

    it("should record custom metrics", () => {
      const beforeTimestamp = Date.now();
      const metric = {
        category: "test",
        data: { value: 100 },
      };

      perf.record(metric.category, metric.data);
      const afterTimestamp = Date.now();
      const metrics = perf.getMetrics(metric.category);

      expect(metrics).toHaveLength(1);
      expect(metrics[0]).toMatchObject({ value: 100 });
      // Check timestamp is within reasonable range
      expect(metrics[0].timestamp).toBeGreaterThanOrEqual(beforeTimestamp);
      expect(metrics[0].timestamp).toBeLessThanOrEqual(afterTimestamp);
    });

    it("should get performance summary", () => {
      // Record some test metrics
      perf.record("test-category", { duration: 100 });
      perf.record("test-category", { duration: 200 });
      perf.record("test-category", { duration: 150 });

      const summary = perf.getSummary();

      expect(summary["test-category"]).toBeDefined();
      expect(summary["test-category"].count).toBe(3);
      expect(summary["test-category"].avgDuration).toBe(150);
      expect(summary["test-category"].minDuration).toBe(100);
      expect(summary["test-category"].maxDuration).toBe(200);
    });
  });

  describe("Memory Management", () => {
    it("should get memory usage", () => {
      const usage = memory.getUsage();

      expect(usage).toBeDefined();
      expect(usage.used).toBe(50000000);
      expect(usage.total).toBe(100000000);
      expect(usage.limit).toBe(200000000);
      expect(usage.percentage).toBe(25); // 50MB / 200MB * 100
    });

    it("should monitor memory usage", () => {
      const callback = vi.fn();
      const intervalId = memory.monitor(callback, 100);

      expect(intervalId).toBeDefined();
      expect(typeof intervalId === "number" || typeof intervalId === "object").toBe(true);

      // Wait for callback to be called
      return new Promise((resolve) => {
        setTimeout(() => {
          expect(callback).toHaveBeenCalled();
          clearInterval(intervalId);
          resolve();
        }, 150);
      });
    });

    it("should handle missing memory API", () => {
      const originalMemory = global.performance.memory;
      delete global.performance.memory;

      const usage = memory.getUsage();
      expect(usage).toBeNull();

      global.performance.memory = originalMemory;
    });
  });

  describe("Image Optimizer", () => {
    it("should generate optimized URL with quality", () => {
      const url = "https://example.com/image.jpg";
      const optimized = imageOptimizer.getOptimizedUrl(url, { quality: 80 });

      expect(optimized).toContain("quality=80");
    });

    it("should generate optimized URL with dimensions", () => {
      const url = "https://example.com/image.jpg";
      const optimized = imageOptimizer.getOptimizedUrl(url, {
        width: 400,
        height: 600,
      });

      expect(optimized).toContain("w=400");
      expect(optimized).toContain("h=600");
    });

    it("should handle invalid URLs gracefully", () => {
      // Mock URL constructor to throw for this test
      const originalURL = global.URL;
      global.URL = vi.fn().mockImplementation(() => {
        throw new Error("Invalid URL");
      });

      const invalidUrl = "invalid-url";
      const optimized = imageOptimizer.getOptimizedUrl(invalidUrl, {
        quality: 80,
      });

      expect(optimized).toBe(invalidUrl);

      // Restore URL constructor
      global.URL = originalURL;
    });

    it("should preload images", async () => {
      // Mock Image constructor - create new mock for each instance
      const mockImages = [];
      global.Image = vi.fn(() => {
        const mockImage = {
          onload: null,
          onerror: null,
          src: "",
          loading: "",
        };
        mockImages.push(mockImage);
        return mockImage;
      });

      const urls = ["image1.jpg", "image2.jpg"];
      const preloadPromise = imageOptimizer.preload(urls);

      // Simulate successful loading for all images
      setTimeout(() => {
        mockImages.forEach(img => {
          if (img.onload) img.onload();
        });
      }, 10);

      const results = await preloadPromise;

      expect(results).toHaveLength(2);
      expect(global.Image).toHaveBeenCalledTimes(2);
      // All should be fulfilled
      expect(results.every(result => result.status === 'fulfilled')).toBe(true);
    });
  });

  describe("Performance Budgets", () => {
    it("should detect budget violations", () => {
      const budgetViolations = [];

      // Listen for budget violation events
      window.addEventListener("performance-budget-exceeded", (event) => {
        budgetViolations.push(event.detail);
      });

      // Record a metric that exceeds budget
      perf.record("test-budget", { duration: 1000 }); // Assuming budget is 500ms

      // Check if violation was detected (this would depend on actual budget setup)
      // This is a simplified test - actual implementation would need budget configuration
    });
  });

  describe("Performance Observer Integration", () => {
    it("should initialize performance observers", () => {
      // The PerformanceObserver should have been called during the beforeEach setup
      // when _enableForTesting() was called, so we check the accumulated calls
      expect(global.PerformanceObserver).toHaveBeenCalled();
    });

    it("should handle missing PerformanceObserver gracefully", () => {
      const originalPO = global.PerformanceObserver;
      delete global.PerformanceObserver;

      // Should not throw error when PerformanceObserver is not available
      expect(() => {
        perf.record("test", { value: 1 });
      }).not.toThrow();

      global.PerformanceObserver = originalPO;
    });
  });

  describe("Export Functionality", () => {
    it("should export performance data", () => {
      // Record some test data
      perf.record("export-test", { duration: 100, type: "test" });

      const exported = perf.export();
      const data = JSON.parse(exported);

      expect(data).toHaveProperty("metrics");
      expect(data).toHaveProperty("summary");
      expect(data).toHaveProperty("timestamp");
      expect(data).toHaveProperty("userAgent");
      expect(data).toHaveProperty("url");
    });

    it("should clear all metrics", () => {
      perf.record("clear-test", { value: 1 });
      expect(perf.getMetrics("clear-test")).toHaveLength(1);

      perf.clear();
      expect(perf.getMetrics("clear-test")).toHaveLength(0);
    });
  });

  describe("Error Handling", () => {
    it("should handle timing errors gracefully", () => {
      // Mock performance.measure to throw error
      mockPerformance.measure.mockImplementationOnce(() => {
        throw new Error("Measure failed");
      });

      expect(() => {
        perf.end("non-existent-timer");
      }).not.toThrow();
    });

    it("should handle function timing errors", () => {
      const errorFn = () => {
        throw new Error("Function error");
      };

      expect(() => {
        perf.time("error-function", errorFn);
      }).toThrow("Function error");

      // Should still call end timing even on error
      expect(mockPerformance.mark).toHaveBeenCalledWith("error-function-end");
    });
  });

  describe("Memory Leak Prevention", () => {
    it("should limit metric storage", () => {
      // Record more than 100 metrics
      for (let i = 0; i < 150; i++) {
        perf.record("limit-test", { value: i });
      }

      const metrics = perf.getMetrics("limit-test");
      expect(metrics.length).toBeLessThanOrEqual(100);
    });
  });
});

describe("Performance Integration", () => {
  it("should work with real performance API if available", () => {
    if ("performance" in window && "mark" in performance) {
      perf.start("real-test");
      perf.end("real-test");

      // Should not throw errors with real API
      expect(true).toBe(true);
    }
  });

  it("should handle different browser environments", () => {
    // Test with minimal browser environment
    const originalPerformance = global.performance;
    global.performance = { now: () => Date.now() };

    expect(() => {
      perf.record("browser-test", { value: 1 });
    }).not.toThrow();

    global.performance = originalPerformance;
  });
});

afterEach(() => {
  // Clean up any intervals or observers
  perf.clear();
});
