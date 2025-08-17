/**
 * Provider-specific rate limiting configurations
 * Based on HakuNeko's throttle settings and provider requirements
 */

export const PROVIDER_RATE_LIMITS = {
  // MangaDex - Popular, well-maintained API (requires conservative rate limiting)
  mangadex: {
    limit: 12, // 12 requests per minute (5 second intervals)
    windowMs: 60000,
    burstLimit: 2, // 2 requests per second burst
    retryAfter: 5000, // 5 second retry delay
    description:
      "MangaDex requires 5 second intervals between API requests to avoid rate limiting",
  },

  // MangaHub - GraphQL API with rate limiting
  mangahub: {
    limit: 30, // 30 requests per minute
    windowMs: 60000,
    burstLimit: 3,
    retryAfter: 1000,
    description: "MangaHub has strict API rate limits",
  },

  // E-Hentai - Strict rate limiting
  ehentai: {
    limit: 20, // 20 requests per minute
    windowMs: 60000,
    burstLimit: 2,
    retryAfter: 500,
    description: "E-Hentai blocks IPs for too many consecutive requests",
  },

  // Viz Shonen Jump - Very strict
  vizshonenjump: {
    limit: 12, // 12 requests per minute
    windowMs: 60000,
    burstLimit: 1,
    retryAfter: 500,
    description: "Viz has very strict rate limits and image link expiration",
  },

  // Line Webtoon - Moderate throttling
  linewebtoon: {
    limit: 40, // 40 requests per minute
    windowMs: 60000,
    burstLimit: 4,
    retryAfter: 750,
    description: "Line Webtoon rejects too many consecutive requests",
  },

  // PornComix - Moderate throttling
  porncomix: {
    limit: 24, // 24 requests per minute
    windowMs: 60000,
    burstLimit: 2,
    retryAfter: 500,
    description: "PornComix may ban IPs for too many consecutive requests",
  },

  // ReadManga - Conservative settings
  readmanga: {
    limit: 30,
    windowMs: 60000,
    burstLimit: 3,
    retryAfter: 1000,
    description: "ReadManga requires conservative rate limiting",
  },

  // Generic fallback for unknown providers
  default: {
    limit: 30, // Conservative default
    windowMs: 60000,
    burstLimit: 3,
    retryAfter: 1000,
    description: "Default conservative rate limiting for unknown providers",
  },
};

/**
 * Provider-specific download settings
 */
export const PROVIDER_DOWNLOAD_SETTINGS = {
  mangadex: {
    maxConcurrentDownloads: 2,
    chapterDelay: 5000, // 5 seconds between chapter downloads (user reports)
    pageDelay: 500, // 500ms between page downloads (HakuNeko default)
    retryAttempts: 3,
    timeout: 30000,
  },

  mangahub: {
    maxConcurrentDownloads: 2,
    chapterDelay: 1000,
    pageDelay: 200,
    retryAttempts: 3,
    timeout: 45000,
  },

  ehentai: {
    maxConcurrentDownloads: 1,
    chapterDelay: 2000,
    pageDelay: 500,
    retryAttempts: 2,
    timeout: 60000,
  },

  vizshonenjump: {
    maxConcurrentDownloads: 1,
    chapterDelay: 5000,
    pageDelay: 1000,
    retryAttempts: 2,
    timeout: 30000,
  },

  linewebtoon: {
    maxConcurrentDownloads: 2,
    chapterDelay: 750,
    pageDelay: 250,
    retryAttempts: 3,
    timeout: 45000,
  },

  porncomix: {
    maxConcurrentDownloads: 2,
    chapterDelay: 1000,
    pageDelay: 500,
    retryAttempts: 3,
    timeout: 45000,
  },

  readmanga: {
    maxConcurrentDownloads: 2,
    chapterDelay: 1000,
    pageDelay: 300,
    retryAttempts: 3,
    timeout: 45000,
  },

  default: {
    maxConcurrentDownloads: 2,
    chapterDelay: 1000,
    pageDelay: 300,
    retryAttempts: 3,
    timeout: 45000,
  },
};

/**
 * Initialize rate limits for all providers
 */
export function initializeProviderRateLimits(rateLimiter) {
  Object.entries(PROVIDER_RATE_LIMITS).forEach(([providerId, config]) => {
    if (providerId !== "default") {
      rateLimiter.setLimit(providerId, config);
    }
  });
}

/**
 * Get rate limit configuration for a provider
 */
export function getProviderRateLimit(providerId) {
  return PROVIDER_RATE_LIMITS[providerId] || PROVIDER_RATE_LIMITS.default;
}

/**
 * Get download settings for a provider
 */
export function getProviderDownloadSettings(providerId) {
  return (
    PROVIDER_DOWNLOAD_SETTINGS[providerId] || PROVIDER_DOWNLOAD_SETTINGS.default
  );
}

/**
 * Apply rate limiting to a provider request
 */
export async function makeRateLimitedRequest(
  rateLimiter,
  providerId,
  requestFn,
  options = {},
) {
  // Ensure rate limit is configured
  if (!rateLimiter.limits.has(providerId)) {
    const config = getProviderRateLimit(providerId);
    rateLimiter.setLimit(providerId, config);
  }

  // Make rate-limited request
  return await rateLimiter.makeRequest(providerId, requestFn, options);
}
