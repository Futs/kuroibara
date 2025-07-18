import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { rateLimiter, proxyManager } from "../rateLimiter";

describe("Rate Limiter", () => {
  beforeEach(() => {
    // Clear all limits before each test
    rateLimiter.limits.clear();
    rateLimiter.queues.clear();
    rateLimiter.stats.clear();
  });

  describe("Rate Limit Configuration", () => {
    it("should set rate limit for provider", () => {
      const providerId = "test-provider";
      const config = {
        limit: 30,
        windowMs: 60000,
        burstLimit: 5,
      };

      rateLimiter.setLimit(providerId, config);

      const limit = rateLimiter.limits.get(providerId);
      expect(limit).toBeDefined();
      expect(limit.limit).toBe(30);
      expect(limit.windowMs).toBe(60000);
      expect(limit.burstLimit).toBe(5);
    });

    it("should use default values when not specified", () => {
      const providerId = "test-provider";
      rateLimiter.setLimit(providerId, {});

      const limit = rateLimiter.limits.get(providerId);
      expect(limit.limit).toBe(rateLimiter.globalConfig.defaultLimit);
      expect(limit.windowMs).toBe(rateLimiter.globalConfig.windowMs);
    });
  });

  describe("Rate Limit Checking", () => {
    it("should allow requests under limit", async () => {
      const providerId = "test-provider";
      rateLimiter.setLimit(providerId, { limit: 10, windowMs: 60000 });

      const result = await rateLimiter.checkLimit(providerId);
      expect(result.allowed).toBe(true);
      expect(result.waitTime).toBe(0);
    });

    it("should block requests over limit", async () => {
      const providerId = "test-provider";
      rateLimiter.setLimit(providerId, { limit: 2, windowMs: 60000 });

      // Make requests up to limit
      await rateLimiter.checkLimit(providerId);
      rateLimiter.recordRequest(providerId);
      await rateLimiter.checkLimit(providerId);
      rateLimiter.recordRequest(providerId);

      // Next request should be blocked
      const result = await rateLimiter.checkLimit(providerId);
      expect(result.allowed).toBe(false);
      expect(result.waitTime).toBeGreaterThan(0);
      expect(result.reason).toBe("rate_limit");
    });

    it("should enforce burst limit", async () => {
      const providerId = "test-provider";
      rateLimiter.setLimit(providerId, {
        limit: 100,
        windowMs: 60000,
        burstLimit: 2,
      });

      // Make burst requests
      await rateLimiter.checkLimit(providerId);
      rateLimiter.recordRequest(providerId);
      await rateLimiter.checkLimit(providerId);
      rateLimiter.recordRequest(providerId);

      // Next request should be blocked by burst limit
      const result = await rateLimiter.checkLimit(providerId);
      expect(result.allowed).toBe(false);
      expect(result.reason).toBe("burst_limit");
    });

    it("should allow requests for provider without limits", async () => {
      const providerId = "unlimited-provider";

      const result = await rateLimiter.checkLimit(providerId);
      expect(result.allowed).toBe(true);
    });
  });

  describe("Request Recording", () => {
    it("should record requests correctly", () => {
      const providerId = "test-provider";
      rateLimiter.setLimit(providerId, { limit: 10 });

      rateLimiter.recordRequest(providerId);

      const limit = rateLimiter.limits.get(providerId);
      const stats = rateLimiter.stats.get(providerId);

      expect(limit.requests).toHaveLength(1);
      expect(limit.burstRequests).toHaveLength(1);
      expect(stats.totalRequests).toBe(1);
      expect(stats.lastRequest).toBeInstanceOf(Date);
    });

    it("should clean old requests from window", async () => {
      const providerId = "test-provider";
      rateLimiter.setLimit(providerId, { limit: 10, windowMs: 100 });

      // Record a request
      rateLimiter.recordRequest(providerId);

      // Wait for window to expire
      await new Promise((resolve) => setTimeout(resolve, 150));

      // Check limit should clean old requests
      await rateLimiter.checkLimit(providerId);

      const limit = rateLimiter.limits.get(providerId);
      expect(limit.requests).toHaveLength(0);
    });
  });

  describe("Request Queue", () => {
    it("should queue requests when rate limited", async () => {
      const providerId = "test-provider";
      rateLimiter.setLimit(providerId, { limit: 1, windowMs: 60000 });

      // Fill the limit
      rateLimiter.recordRequest(providerId);

      const mockRequestFn = vi.fn().mockResolvedValue("result");

      // This should be queued
      const promise = rateLimiter.queueRequest(providerId, mockRequestFn);

      const queue = rateLimiter.queues.get(providerId);
      expect(queue).toHaveLength(1);

      // Don't wait for the promise to resolve in this test
      // as it would require time manipulation
    });

    it("should respect priority in queue", async () => {
      const providerId = "test-provider";
      rateLimiter.setLimit(providerId, { limit: 0 }); // Block all requests

      const lowPriorityFn = vi.fn().mockResolvedValue("low");
      const highPriorityFn = vi.fn().mockResolvedValue("high");

      // Queue low priority first
      rateLimiter.queueRequest(providerId, lowPriorityFn, 1);
      // Queue high priority second
      rateLimiter.queueRequest(providerId, highPriorityFn, 10);

      const queue = rateLimiter.queues.get(providerId);
      expect(queue).toHaveLength(2);
      expect(queue[0].priority).toBe(10); // High priority should be first
      expect(queue[1].priority).toBe(1);
    });

    it("should reject when queue is full", async () => {
      const providerId = "test-provider";
      rateLimiter.setLimit(providerId, { limit: 0 });

      // Fill the queue
      const promises = [];
      for (let i = 0; i < rateLimiter.globalConfig.maxQueueSize; i++) {
        promises.push(
          rateLimiter.queueRequest(providerId, () => Promise.resolve()),
        );
      }

      // Next request should be rejected
      await expect(
        rateLimiter.queueRequest(providerId, () => Promise.resolve()),
      ).rejects.toThrow("Request queue is full");
    });
  });

  describe("Rate Limit Status", () => {
    it("should return correct status", () => {
      const providerId = "test-provider";
      rateLimiter.setLimit(providerId, { limit: 10, windowMs: 60000 });

      // Make some requests
      rateLimiter.recordRequest(providerId);
      rateLimiter.recordRequest(providerId);

      const status = rateLimiter.getStatus(providerId);

      expect(status.configured).toBe(true);
      expect(status.limit).toBe(10);
      expect(status.currentRequests).toBe(2);
      expect(status.remainingRequests).toBe(8);
      expect(status.queueLength).toBe(0);
    });

    it("should return unconfigured status for unknown provider", () => {
      const status = rateLimiter.getStatus("unknown-provider");
      expect(status.configured).toBe(false);
    });
  });

  describe("Global Configuration", () => {
    it("should update global configuration", () => {
      const newConfig = {
        defaultLimit: 120,
        maxQueueSize: 200,
      };

      rateLimiter.updateGlobalConfig(newConfig);

      expect(rateLimiter.globalConfig.defaultLimit).toBe(120);
      expect(rateLimiter.globalConfig.maxQueueSize).toBe(200);
    });
  });
});

describe("Proxy Manager", () => {
  beforeEach(() => {
    proxyManager.proxies.clear();
    proxyManager.proxyHealth.clear();
    proxyManager.proxyRotation.clear();
  });

  describe("Proxy Configuration", () => {
    it("should add proxy for provider", () => {
      const providerId = "test-provider";
      const proxyConfig = {
        host: "127.0.0.1",
        port: 8080,
        type: "http",
        username: "user",
        password: "pass",
      };

      const proxyId = proxyManager.addProxy(providerId, proxyConfig);

      expect(proxyId).toBeDefined();
      const proxies = proxyManager.proxies.get(providerId);
      expect(proxies).toHaveLength(1);
      expect(proxies[0].host).toBe("127.0.0.1");
      expect(proxies[0].port).toBe(8080);
    });

    it("should remove proxy", () => {
      const providerId = "test-provider";
      const proxyConfig = { host: "127.0.0.1", port: 8080 };

      const proxyId = proxyManager.addProxy(providerId, proxyConfig);
      proxyManager.removeProxy(providerId, proxyId);

      const proxies = proxyManager.proxies.get(providerId);
      expect(proxies).toHaveLength(0);
    });
  });

  describe("Proxy Selection", () => {
    it("should return null when no proxies available", () => {
      const proxy = proxyManager.getProxy("no-proxies-provider");
      expect(proxy).toBeNull();
    });

    it("should return proxy when available", () => {
      const providerId = "test-provider";
      const proxyConfig = { host: "127.0.0.1", port: 8080 };

      proxyManager.addProxy(providerId, proxyConfig);
      const proxy = proxyManager.getProxy(providerId);

      expect(proxy).toBeDefined();
      expect(proxy.host).toBe("127.0.0.1");
    });

    it("should rotate proxies in round robin", () => {
      const providerId = "test-provider";

      proxyManager.addProxy(providerId, { host: "127.0.0.1", port: 8080 });
      proxyManager.addProxy(providerId, { host: "127.0.0.2", port: 8080 });

      proxyManager.globalConfig.rotationStrategy = "round_robin";

      const proxy1 = proxyManager.getProxy(providerId);
      const proxy2 = proxyManager.getProxy(providerId);
      const proxy3 = proxyManager.getProxy(providerId);

      expect(proxy1.host).toBe("127.0.0.1");
      expect(proxy2.host).toBe("127.0.0.2");
      expect(proxy3.host).toBe("127.0.0.1"); // Should wrap around
    });

    it("should select random proxy", () => {
      const providerId = "test-provider";

      proxyManager.addProxy(providerId, { host: "127.0.0.1", port: 8080 });
      proxyManager.addProxy(providerId, { host: "127.0.0.2", port: 8080 });

      proxyManager.globalConfig.rotationStrategy = "random";

      const proxy = proxyManager.getProxy(providerId);
      expect(["127.0.0.1", "127.0.0.2"]).toContain(proxy.host);
    });
  });

  describe("Proxy Health", () => {
    it("should initialize proxy health", () => {
      const providerId = "test-provider";
      const proxyConfig = { host: "127.0.0.1", port: 8080 };

      const proxyId = proxyManager.addProxy(providerId, proxyConfig);
      const health = proxyManager.proxyHealth.get(`${providerId}-${proxyId}`);

      expect(health).toBeDefined();
      expect(health.isHealthy).toBe(true);
      expect(health.consecutiveFailures).toBe(0);
      expect(health.successRate).toBe(100);
    });

    it("should record proxy usage", () => {
      const providerId = "test-provider-usage";
      const proxyConfig = { host: "127.0.0.1", port: 8080 };

      const proxyId = proxyManager.addProxy(providerId, proxyConfig);

      // Record successful usage
      proxyManager.recordProxyUsage(providerId, proxyId, true, 500);

      const health = proxyManager.proxyHealth.get(`${providerId}-${proxyId}`);
      expect(health.totalRequests).toBe(1);
      expect(health.successfulRequests).toBe(1);
      expect(health.averageResponseTime).toBe(500);
      expect(health.consecutiveFailures).toBe(0);
    });

    it("should handle proxy failures", () => {
      const providerId = "test-provider";
      const proxyConfig = { host: "127.0.0.1", port: 8080 };

      const proxyId = proxyManager.addProxy(providerId, proxyConfig);

      // Record multiple failures
      for (let i = 0; i < 3; i++) {
        proxyManager.recordProxyUsage(providerId, proxyId, false, 0);
      }

      const health = proxyManager.proxyHealth.get(`${providerId}-${proxyId}`);
      const proxies = proxyManager.proxies.get(providerId);

      expect(health.consecutiveFailures).toBe(3);
      expect(health.isHealthy).toBe(false);
      expect(proxies[0].isActive).toBe(false); // Should be disabled
    });

    it("should calculate health score correctly", () => {
      const providerId = "test-provider";
      const proxyConfig = { host: "127.0.0.1", port: 8080 };

      const proxyId = proxyManager.addProxy(providerId, proxyConfig);

      // Record some usage
      proxyManager.recordProxyUsage(providerId, proxyId, true, 200);
      proxyManager.recordProxyUsage(providerId, proxyId, true, 300);

      const score = proxyManager.getProxyHealthScore(providerId, proxyId);
      expect(score).toBeGreaterThan(90); // Should be high for good performance
    });
  });

  describe("Proxy Status", () => {
    it("should return proxy status", () => {
      const providerId = "test-provider";
      const proxyConfig = { host: "127.0.0.1", port: 8080 };

      proxyManager.addProxy(providerId, proxyConfig);
      const status = proxyManager.getProxyStatus(providerId);

      expect(status).toHaveLength(1);
      expect(status[0].host).toBe("127.0.0.1");
      expect(status[0].health).toBeDefined();
    });
  });
});

describe("Integration Tests", () => {
  it("should work together for rate-limited proxy requests", async () => {
    const providerId = "integration-test";

    // Set up rate limiting
    rateLimiter.setLimit(providerId, { limit: 2, windowMs: 1000 });

    // Set up proxy
    proxyManager.addProxy(providerId, { host: "127.0.0.1", port: 8080 });

    // Make requests with longer delay to ensure they stay active during status check
    const mockRequestFn = vi.fn().mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve("success"), 500))
    );

    // Make first two requests - these should be allowed immediately
    const promise1 = rateLimiter.makeRequest(providerId, mockRequestFn);
    const promise2 = rateLimiter.makeRequest(providerId, mockRequestFn);

    // Wait a tiny bit for the first two to be recorded
    await new Promise(resolve => setTimeout(resolve, 10));

    // Now make the third request - this should be queued
    const promise3 = rateLimiter.makeRequest(providerId, mockRequestFn);

    // Check status immediately after third request
    await new Promise(resolve => setTimeout(resolve, 10));
    const status = rateLimiter.getStatus(providerId);

    // Should have 2 requests in the time window (first two were allowed)
    expect(status.currentRequests).toBe(2);
    // The 3rd request should be queued since limit is 2 per window
    expect(status.queueLength).toBe(1);

    // Wait for all requests to complete
    await Promise.all([promise1, promise2, promise3]);

    const proxy = proxyManager.getProxy(providerId);
    expect(proxy).toBeDefined();
  });
});

afterEach(() => {
  vi.clearAllTimers();
});
