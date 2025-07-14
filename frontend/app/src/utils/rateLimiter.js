/**
 * Advanced rate limiting and request throttling system
 */

class RateLimiter {
  constructor() {
    this.limits = new Map();
    this.queues = new Map();
    this.stats = new Map();
    this.globalConfig = {
      defaultLimit: 60, // requests per minute
      burstLimit: 10, // burst requests allowed
      windowMs: 60000, // 1 minute window
      retryAfter: 1000, // retry delay in ms
      maxQueueSize: 100,
    };
  }

  /**
   * Set rate limit for a provider
   */
  setLimit(providerId, config) {
    this.limits.set(providerId, {
      limit: config.limit || this.globalConfig.defaultLimit,
      windowMs: config.windowMs || this.globalConfig.windowMs,
      burstLimit: config.burstLimit || this.globalConfig.burstLimit,
      retryAfter: config.retryAfter || this.globalConfig.retryAfter,
      requests: [],
      burstRequests: [],
    });

    if (!this.queues.has(providerId)) {
      this.queues.set(providerId, []);
    }

    if (!this.stats.has(providerId)) {
      this.stats.set(providerId, {
        totalRequests: 0,
        throttledRequests: 0,
        queuedRequests: 0,
        averageWaitTime: 0,
        lastRequest: null,
      });
    }
  }

  /**
   * Check if request is allowed
   */
  async checkLimit(providerId) {
    const limit = this.limits.get(providerId);
    if (!limit) {
      // No limit set, allow request
      return { allowed: true, waitTime: 0 };
    }

    const now = Date.now();
    const windowStart = now - limit.windowMs;
    const burstWindowStart = now - 1000; // 1 second burst window

    // Clean old requests
    limit.requests = limit.requests.filter(time => time > windowStart);
    limit.burstRequests = limit.burstRequests.filter(time => time > burstWindowStart);

    // Check burst limit first
    if (limit.burstRequests.length >= limit.burstLimit) {
      const oldestBurst = Math.min(...limit.burstRequests);
      const waitTime = 1000 - (now - oldestBurst);
      return { allowed: false, waitTime, reason: 'burst_limit' };
    }

    // Check regular limit
    if (limit.requests.length >= limit.limit) {
      const oldestRequest = Math.min(...limit.requests);
      const waitTime = limit.windowMs - (now - oldestRequest);
      return { allowed: false, waitTime, reason: 'rate_limit' };
    }

    return { allowed: true, waitTime: 0 };
  }

  /**
   * Record a request
   */
  recordRequest(providerId) {
    const limit = this.limits.get(providerId);
    const stats = this.stats.get(providerId);
    
    if (limit) {
      const now = Date.now();
      limit.requests.push(now);
      limit.burstRequests.push(now);
    }

    if (stats) {
      stats.totalRequests++;
      stats.lastRequest = new Date();
    }
  }

  /**
   * Add request to queue
   */
  async queueRequest(providerId, requestFn, priority = 0) {
    const queue = this.queues.get(providerId) || [];
    const stats = this.stats.get(providerId);

    if (queue.length >= this.globalConfig.maxQueueSize) {
      throw new Error('Request queue is full');
    }

    return new Promise((resolve, reject) => {
      const queueItem = {
        id: Date.now() + Math.random(),
        requestFn,
        priority,
        resolve,
        reject,
        queuedAt: Date.now(),
      };

      // Insert based on priority
      const insertIndex = queue.findIndex(item => item.priority < priority);
      if (insertIndex === -1) {
        queue.push(queueItem);
      } else {
        queue.splice(insertIndex, 0, queueItem);
      }

      this.queues.set(providerId, queue);

      if (stats) {
        stats.queuedRequests++;
      }

      // Start processing queue
      this.processQueue(providerId);
    });
  }

  /**
   * Process request queue
   */
  async processQueue(providerId) {
    const queue = this.queues.get(providerId);
    if (!queue || queue.length === 0) return;

    const checkResult = await this.checkLimit(providerId);
    
    if (checkResult.allowed) {
      const queueItem = queue.shift();
      if (queueItem) {
        try {
          this.recordRequest(providerId);
          const result = await queueItem.requestFn();
          
          // Update wait time stats
          const stats = this.stats.get(providerId);
          if (stats) {
            const waitTime = Date.now() - queueItem.queuedAt;
            stats.averageWaitTime = (stats.averageWaitTime + waitTime) / 2;
          }
          
          queueItem.resolve(result);
        } catch (error) {
          queueItem.reject(error);
        }

        // Continue processing queue
        setTimeout(() => this.processQueue(providerId), 100);
      }
    } else {
      // Wait and try again
      setTimeout(() => this.processQueue(providerId), checkResult.waitTime);
      
      // Update throttled stats
      const stats = this.stats.get(providerId);
      if (stats) {
        stats.throttledRequests++;
      }
    }
  }

  /**
   * Make rate-limited request
   */
  async makeRequest(providerId, requestFn, options = {}) {
    const { priority = 0, timeout = 30000 } = options;
    
    const checkResult = await this.checkLimit(providerId);
    
    if (checkResult.allowed) {
      this.recordRequest(providerId);
      return await requestFn();
    } else {
      // Queue the request
      return await this.queueRequest(providerId, requestFn, priority);
    }
  }

  /**
   * Get rate limit status
   */
  getStatus(providerId) {
    const limit = this.limits.get(providerId);
    const queue = this.queues.get(providerId) || [];
    const stats = this.stats.get(providerId);

    if (!limit) {
      return { configured: false };
    }

    const now = Date.now();
    const windowStart = now - limit.windowMs;
    const currentRequests = limit.requests.filter(time => time > windowStart).length;

    return {
      configured: true,
      limit: limit.limit,
      windowMs: limit.windowMs,
      currentRequests,
      remainingRequests: Math.max(0, limit.limit - currentRequests),
      queueLength: queue.length,
      resetTime: Math.min(...limit.requests) + limit.windowMs,
      stats: stats || {},
    };
  }

  /**
   * Get all provider statuses
   */
  getAllStatuses() {
    const statuses = {};
    for (const providerId of this.limits.keys()) {
      statuses[providerId] = this.getStatus(providerId);
    }
    return statuses;
  }

  /**
   * Clear rate limit for provider
   */
  clearLimit(providerId) {
    this.limits.delete(providerId);
    this.queues.delete(providerId);
    this.stats.delete(providerId);
  }

  /**
   * Update global configuration
   */
  updateGlobalConfig(config) {
    this.globalConfig = { ...this.globalConfig, ...config };
  }
}

/**
 * Proxy management system
 */
class ProxyManager {
  constructor() {
    this.proxies = new Map();
    this.proxyHealth = new Map();
    this.proxyRotation = new Map();
    this.globalConfig = {
      healthCheckInterval: 300000, // 5 minutes
      maxFailures: 3,
      rotationStrategy: 'round_robin', // round_robin, random, health_based
    };
  }

  /**
   * Add proxy configuration for provider
   */
  addProxy(providerId, proxyConfig) {
    if (!this.proxies.has(providerId)) {
      this.proxies.set(providerId, []);
    }

    const proxies = this.proxies.get(providerId);
    const proxy = {
      id: Date.now() + Math.random(),
      ...proxyConfig,
      addedAt: new Date(),
      isActive: true,
    };

    proxies.push(proxy);
    this.initializeProxyHealth(providerId, proxy.id);
    
    return proxy.id;
  }

  /**
   * Remove proxy
   */
  removeProxy(providerId, proxyId) {
    const proxies = this.proxies.get(providerId) || [];
    const index = proxies.findIndex(p => p.id === proxyId);
    
    if (index !== -1) {
      proxies.splice(index, 1);
      this.proxyHealth.delete(`${providerId}-${proxyId}`);
    }
  }

  /**
   * Get proxy for request
   */
  getProxy(providerId) {
    const proxies = this.proxies.get(providerId) || [];
    const activeProxies = proxies.filter(p => p.isActive);
    
    if (activeProxies.length === 0) {
      return null;
    }

    const strategy = this.globalConfig.rotationStrategy;
    let selectedProxy;

    switch (strategy) {
      case 'round_robin':
        selectedProxy = this.getRoundRobinProxy(providerId, activeProxies);
        break;
      case 'random':
        selectedProxy = activeProxies[Math.floor(Math.random() * activeProxies.length)];
        break;
      case 'health_based':
        selectedProxy = this.getHealthBasedProxy(providerId, activeProxies);
        break;
      default:
        selectedProxy = activeProxies[0];
    }

    return selectedProxy;
  }

  /**
   * Round robin proxy selection
   */
  getRoundRobinProxy(providerId, proxies) {
    if (!this.proxyRotation.has(providerId)) {
      this.proxyRotation.set(providerId, { index: 0 });
    }

    const rotation = this.proxyRotation.get(providerId);
    const proxy = proxies[rotation.index % proxies.length];
    rotation.index++;

    return proxy;
  }

  /**
   * Health-based proxy selection
   */
  getHealthBasedProxy(providerId, proxies) {
    // Sort by health score (response time, success rate, etc.)
    const sortedProxies = proxies.sort((a, b) => {
      const healthA = this.getProxyHealthScore(providerId, a.id);
      const healthB = this.getProxyHealthScore(providerId, b.id);
      return healthB - healthA;
    });

    return sortedProxies[0];
  }

  /**
   * Calculate proxy health score
   */
  getProxyHealthScore(providerId, proxyId) {
    const health = this.proxyHealth.get(`${providerId}-${proxyId}`);
    if (!health) return 0;

    let score = 100;
    
    // Penalize for failures
    score -= health.consecutiveFailures * 20;
    
    // Penalize for high response time
    if (health.averageResponseTime > 1000) {
      score -= (health.averageResponseTime - 1000) / 100;
    }
    
    // Penalize for low success rate
    if (health.successRate < 95) {
      score -= (95 - health.successRate) * 2;
    }

    return Math.max(0, score);
  }

  /**
   * Initialize proxy health tracking
   */
  initializeProxyHealth(providerId, proxyId) {
    const key = `${providerId}-${proxyId}`;
    this.proxyHealth.set(key, {
      isHealthy: true,
      consecutiveFailures: 0,
      totalRequests: 0,
      successfulRequests: 0,
      averageResponseTime: 0,
      successRate: 100,
      lastCheck: new Date(),
      lastUsed: null,
    });
  }

  /**
   * Record proxy usage
   */
  recordProxyUsage(providerId, proxyId, success, responseTime) {
    const key = `${providerId}-${proxyId}`;
    const health = this.proxyHealth.get(key);
    
    if (!health) return;

    health.totalRequests++;
    health.lastUsed = new Date();

    if (success) {
      health.successfulRequests++;
      health.consecutiveFailures = 0;
    } else {
      health.consecutiveFailures++;
    }

    if (responseTime) {
      health.averageResponseTime = 
        (health.averageResponseTime + responseTime) / 2;
    }

    health.successRate = health.totalRequests > 0 
      ? (health.successfulRequests / health.totalRequests) * 100 
      : 100;

    health.isHealthy = health.consecutiveFailures < this.globalConfig.maxFailures;

    // Disable proxy if too many failures
    if (health.consecutiveFailures >= this.globalConfig.maxFailures) {
      const proxies = this.proxies.get(providerId) || [];
      const proxy = proxies.find(p => p.id === proxyId);
      if (proxy) {
        proxy.isActive = false;
      }
    }
  }

  /**
   * Test proxy health
   */
  async testProxy(providerId, proxyId, testUrl = 'https://httpbin.org/ip') {
    const proxies = this.proxies.get(providerId) || [];
    const proxy = proxies.find(p => p.id === proxyId);
    
    if (!proxy) {
      throw new Error('Proxy not found');
    }

    const startTime = Date.now();
    
    try {
      const response = await fetch(testUrl, {
        method: 'GET',
        headers: {
          'User-Agent': 'Kuroibara/1.0',
        },
        // Proxy configuration would be applied here
        // This depends on the specific proxy implementation
      });

      const responseTime = Date.now() - startTime;
      const success = response.ok;

      this.recordProxyUsage(providerId, proxyId, success, responseTime);

      return {
        success,
        responseTime,
        status: response.status,
        data: success ? await response.json() : null,
      };
    } catch (error) {
      const responseTime = Date.now() - startTime;
      this.recordProxyUsage(providerId, proxyId, false, responseTime);
      
      throw error;
    }
  }

  /**
   * Get proxy status
   */
  getProxyStatus(providerId) {
    const proxies = this.proxies.get(providerId) || [];
    
    return proxies.map(proxy => ({
      ...proxy,
      health: this.proxyHealth.get(`${providerId}-${proxy.id}`),
    }));
  }

  /**
   * Start health monitoring
   */
  startHealthMonitoring() {
    setInterval(async () => {
      for (const [providerId, proxies] of this.proxies.entries()) {
        for (const proxy of proxies) {
          if (proxy.isActive) {
            try {
              await this.testProxy(providerId, proxy.id);
            } catch (error) {
              console.warn(`Proxy health check failed for ${proxy.host}:${proxy.port}:`, error);
            }
          }
        }
      }
    }, this.globalConfig.healthCheckInterval);
  }
}

// Create singleton instances
const rateLimiter = new RateLimiter();
const proxyManager = new ProxyManager();

// Start proxy health monitoring
proxyManager.startHealthMonitoring();

export { rateLimiter, proxyManager };
export default { rateLimiter, proxyManager };
