/**
 * Image proxy utility for handling external provider images
 * Solves CORS issues by routing external images through backend proxy
 */

/**
 * Check if a URL is from an external provider that needs proxying
 * @param {string} url - Image URL to check
 * @returns {boolean} - True if URL needs proxying
 */
export function needsProxy(url) {
  if (!url || typeof url !== "string") return false;

  // List of external domains that need proxying
  const externalDomains = [
    "toonily.com",
    "mangadna.com",
    "manga18fx.com",
    "mangabuddy.com",
    "weebcentral.com",
    // Add more external provider domains as needed
  ];

  try {
    const urlObj = new URL(url);
    return externalDomains.some((domain) => urlObj.hostname.includes(domain));
  } catch {
    return false;
  }
}

/**
 * Get proxied image URL for external providers
 * @param {string} originalUrl - Original image URL
 * @returns {string} - Proxied URL or original URL if no proxy needed
 */
export function getProxiedImageUrl(originalUrl) {
  if (!originalUrl || !needsProxy(originalUrl)) {
    return originalUrl;
  }

  // Use the backend image proxy endpoint
  const encodedUrl = encodeURIComponent(originalUrl);
  return `/api/v1/providers/image-proxy?url=${encodedUrl}`;
}

/**
 * Get cover URL with proper handling for internal vs external manga
 * @param {Object} manga - Manga object
 * @param {string} mangaId - Manga ID (optional, for internal manga)
 * @returns {string} - Appropriate cover URL
 */
export function getCoverUrl(manga, mangaId = null) {
  // Priority 1: For external manga with cover_image that needs proxy
  if (manga.cover_image && needsProxy(manga.cover_image)) {
    console.log("Using proxy for external image:", manga.cover_image);
    return getProxiedImageUrl(manga.cover_image);
  }

  // Priority 2: For internal manga, use the cover endpoint
  if (mangaId && !manga.provider) {
    console.log("Using internal cover endpoint for manga:", mangaId);
    return `/api/v1/manga/${mangaId}/cover`;
  }

  // Priority 3: For internal manga with cover_image (no proxy needed)
  if (manga.cover_image && !needsProxy(manga.cover_image)) {
    console.log("Using direct internal image:", manga.cover_image);
    return manga.cover_image;
  }

  // Priority 4: Try cover_url with proxy if needed
  if (manga.cover_url) {
    if (needsProxy(manga.cover_url)) {
      console.log("Using proxy for cover_url:", manga.cover_url);
      return getProxiedImageUrl(manga.cover_url);
    } else {
      console.log("Using direct cover_url:", manga.cover_url);
      return manga.cover_url;
    }
  }

  // Fallback to placeholder
  console.log("Using placeholder image for manga:", manga.title || "unknown");
  return "/placeholder-cover.jpg";
}

/**
 * Enhanced image error handler with retry logic
 * @param {Event} event - Image error event
 * @param {string} originalUrl - Original image URL
 * @param {Function} onRetry - Callback for retry attempts
 */
export function handleImageError(event, originalUrl, onRetry = null) {
  const img = event.target;

  // If this was a proxied URL that failed, try the original
  if (img.src.includes("/api/v1/providers/image-proxy")) {
    console.warn(`Proxied image failed, trying original: ${originalUrl}`);
    if (originalUrl && originalUrl !== img.src) {
      img.src = originalUrl;
      return;
    }
  }

  // If original also failed, try proxy (for external URLs)
  if (
    needsProxy(originalUrl) &&
    !img.src.includes("/api/v1/providers/image-proxy")
  ) {
    console.warn(
      `Original external image failed, trying proxy: ${originalUrl}`,
    );
    img.src = getProxiedImageUrl(originalUrl);
    return;
  }

  // Final fallback to placeholder
  console.warn(`All image sources failed for: ${originalUrl}`);
  img.src = "/placeholder-cover.jpg";

  // Call retry callback if provided
  if (onRetry && typeof onRetry === "function") {
    onRetry(originalUrl);
  }
}

/**
 * Preload image with proxy fallback
 * @param {string} url - Image URL to preload
 * @returns {Promise} - Promise that resolves when image loads
 */
export function preloadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();

    img.onload = () => resolve(img);
    img.onerror = () => {
      // Try proxy if original fails and it's an external URL
      if (
        needsProxy(url) &&
        !img.src.includes("/api/v1/providers/image-proxy")
      ) {
        img.src = getProxiedImageUrl(url);
      } else {
        reject(new Error(`Failed to load image: ${url}`));
      }
    };

    img.src = getCoverUrl({ cover_image: url });
  });
}

export default {
  needsProxy,
  getProxiedImageUrl,
  getCoverUrl,
  handleImageError,
  preloadImage,
};
