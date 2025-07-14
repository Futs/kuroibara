/**
 * CDN integration for faster image delivery and optimization
 */

class CDNManager {
  constructor() {
    this.providers = new Map();
    this.fallbackChain = [];
    this.config = {
      enableOptimization: true,
      enableWebP: this.supportsWebP(),
      enableAVIF: this.supportsAVIF(),
      defaultQuality: 80,
      enableLazyLoading: true,
      enableProgressiveJPEG: true,
      maxRetries: 3,
      retryDelay: 1000
    };
    
    this.initializeProviders();
  }

  /**
   * Initialize CDN providers
   */
  initializeProviders() {
    // Cloudinary provider
    this.providers.set('cloudinary', {
      name: 'Cloudinary',
      baseUrl: process.env.VITE_CLOUDINARY_URL || '',
      transform: (url, options) => this.cloudinaryTransform(url, options),
      priority: 1
    });

    // ImageKit provider
    this.providers.set('imagekit', {
      name: 'ImageKit',
      baseUrl: process.env.VITE_IMAGEKIT_URL || '',
      transform: (url, options) => this.imagekitTransform(url, options),
      priority: 2
    });

    // Custom CDN provider
    this.providers.set('custom', {
      name: 'Custom CDN',
      baseUrl: process.env.VITE_CDN_URL || '',
      transform: (url, options) => this.customTransform(url, options),
      priority: 3
    });

    // Original source (fallback)
    this.providers.set('original', {
      name: 'Original',
      baseUrl: '',
      transform: (url, options) => this.originalTransform(url, options),
      priority: 999
    });

    // Set fallback chain based on priority
    this.fallbackChain = Array.from(this.providers.values())
      .sort((a, b) => a.priority - b.priority)
      .filter(provider => provider.baseUrl || provider.name === 'Original');
  }

  /**
   * Get optimized image URL with CDN and fallbacks
   */
  getOptimizedUrl(originalUrl, options = {}) {
    if (!originalUrl) return originalUrl;

    const opts = {
      width: options.width,
      height: options.height,
      quality: options.quality || this.config.defaultQuality,
      format: this.getBestFormat(options.format),
      fit: options.fit || 'cover',
      progressive: options.progressive !== false,
      ...options
    };

    // Try each provider in fallback chain
    for (const provider of this.fallbackChain) {
      try {
        const transformedUrl = provider.transform(originalUrl, opts);
        if (transformedUrl) {
          return transformedUrl;
        }
      } catch (error) {
        console.warn(`CDN provider ${provider.name} failed:`, error);
        continue;
      }
    }

    // Return original URL if all providers fail
    return originalUrl;
  }

  /**
   * Cloudinary URL transformation
   */
  cloudinaryTransform(url, options) {
    if (!this.providers.get('cloudinary').baseUrl) return null;

    const transformations = [];

    if (options.width || options.height) {
      const resize = `c_${options.fit || 'fill'}`;
      if (options.width) transformations.push(`w_${options.width}`);
      if (options.height) transformations.push(`h_${options.height}`);
      transformations.push(resize);
    }

    if (options.quality) {
      transformations.push(`q_${options.quality}`);
    }

    if (options.format) {
      transformations.push(`f_${options.format}`);
    }

    if (options.progressive) {
      transformations.push('fl_progressive');
    }

    const transformString = transformations.join(',');
    const baseUrl = this.providers.get('cloudinary').baseUrl;
    
    // Extract filename from original URL
    const filename = this.extractFilename(url);
    
    return `${baseUrl}/${transformString}/${filename}`;
  }

  /**
   * ImageKit URL transformation
   */
  imagekitTransform(url, options) {
    if (!this.providers.get('imagekit').baseUrl) return null;

    const params = new URLSearchParams();

    if (options.width) params.set('w', options.width);
    if (options.height) params.set('h', options.height);
    if (options.quality) params.set('q', options.quality);
    if (options.format) params.set('f', options.format);
    if (options.fit) params.set('c', options.fit);
    if (options.progressive) params.set('pr', 'true');

    const baseUrl = this.providers.get('imagekit').baseUrl;
    const filename = this.extractFilename(url);
    const queryString = params.toString();
    
    return `${baseUrl}/${filename}${queryString ? `?${queryString}` : ''}`;
  }

  /**
   * Custom CDN transformation
   */
  customTransform(url, options) {
    if (!this.providers.get('custom').baseUrl) return null;

    const params = new URLSearchParams();

    if (options.width) params.set('width', options.width);
    if (options.height) params.set('height', options.height);
    if (options.quality) params.set('quality', options.quality);
    if (options.format) params.set('format', options.format);

    const baseUrl = this.providers.get('custom').baseUrl;
    const filename = this.extractFilename(url);
    const queryString = params.toString();
    
    return `${baseUrl}/${filename}${queryString ? `?${queryString}` : ''}`;
  }

  /**
   * Original URL with basic optimization
   */
  originalTransform(url, options) {
    if (!url) return url;

    try {
      const urlObj = new URL(url, window.location.origin);
      
      if (options.quality && options.quality !== this.config.defaultQuality) {
        urlObj.searchParams.set('quality', options.quality);
      }
      
      if (options.width) {
        urlObj.searchParams.set('w', options.width);
      }
      
      if (options.height) {
        urlObj.searchParams.set('h', options.height);
      }
      
      if (options.format) {
        urlObj.searchParams.set('format', options.format);
      }
      
      return urlObj.toString();
    } catch (error) {
      return url;
    }
  }

  /**
   * Extract filename from URL
   */
  extractFilename(url) {
    try {
      const urlObj = new URL(url);
      return urlObj.pathname.split('/').pop() || 'image';
    } catch (error) {
      return url.split('/').pop() || 'image';
    }
  }

  /**
   * Get best image format based on browser support
   */
  getBestFormat(requestedFormat) {
    if (requestedFormat) return requestedFormat;
    
    if (this.config.enableAVIF) return 'avif';
    if (this.config.enableWebP) return 'webp';
    return 'auto';
  }

  /**
   * Check WebP support
   */
  supportsWebP() {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  }

  /**
   * Check AVIF support
   */
  supportsAVIF() {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    return canvas.toDataURL('image/avif').indexOf('data:image/avif') === 0;
  }

  /**
   * Preload images with CDN optimization
   */
  async preloadImages(urls, options = {}) {
    const preloadPromises = urls.map(url => {
      const optimizedUrl = this.getOptimizedUrl(url, {
        ...options,
        quality: options.quality || 60, // Lower quality for preloading
        width: options.width || 400 // Smaller size for preloading
      });

      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve({ url, optimizedUrl, success: true });
        img.onerror = () => resolve({ url, optimizedUrl, success: false });
        
        // Set loading priority
        if ('loading' in img) {
          img.loading = options.priority === 'high' ? 'eager' : 'lazy';
        }
        
        img.src = optimizedUrl;
      });
    });

    return Promise.allSettled(preloadPromises);
  }

  /**
   * Get responsive image URLs for different screen sizes
   */
  getResponsiveUrls(url, options = {}) {
    const breakpoints = options.breakpoints || [320, 640, 768, 1024, 1280, 1920];
    const urls = {};

    for (const width of breakpoints) {
      urls[`${width}w`] = this.getOptimizedUrl(url, {
        ...options,
        width,
        height: options.height ? Math.round((options.height * width) / (options.width || width)) : undefined
      });
    }

    return urls;
  }

  /**
   * Generate srcset string for responsive images
   */
  generateSrcSet(url, options = {}) {
    const responsiveUrls = this.getResponsiveUrls(url, options);
    
    return Object.entries(responsiveUrls)
      .map(([descriptor, url]) => `${url} ${descriptor}`)
      .join(', ');
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get current configuration
   */
  getConfig() {
    return { ...this.config };
  }

  /**
   * Get provider status
   */
  getProviderStatus() {
    const status = {};
    
    for (const [name, provider] of this.providers.entries()) {
      status[name] = {
        name: provider.name,
        available: Boolean(provider.baseUrl || name === 'original'),
        priority: provider.priority
      };
    }
    
    return status;
  }
}

// Create singleton instance
const cdnManager = new CDNManager();

// Export utility functions
export const cdn = {
  /**
   * Get optimized image URL
   */
  optimize: (url, options) => cdnManager.getOptimizedUrl(url, options),

  /**
   * Preload images
   */
  preload: (urls, options) => cdnManager.preloadImages(urls, options),

  /**
   * Get responsive URLs
   */
  responsive: (url, options) => cdnManager.getResponsiveUrls(url, options),

  /**
   * Generate srcset
   */
  srcset: (url, options) => cdnManager.generateSrcSet(url, options),

  /**
   * Update configuration
   */
  config: (newConfig) => cdnManager.updateConfig(newConfig),

  /**
   * Get status
   */
  status: () => cdnManager.getProviderStatus()
};

export default cdnManager;
