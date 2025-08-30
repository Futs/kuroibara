/**
 * Torrent search and download service
 */

import api from './api';

class TorrentService {
  /**
   * Search for torrents across indexers
   * @param {string} query - Search query
   * @param {Object} options - Search options
   * @returns {Promise<Object>} Search results
   */
  async searchTorrents(query, options = {}) {
    try {
      const params = new URLSearchParams({
        query: query,
        limit: options.limit || 50
      });

      if (options.category) {
        params.append('category', options.category);
      }

      if (options.indexer) {
        params.append('indexer', options.indexer);
      }

      const response = await api.get(`/api/v1/torrents/search?${params}`);
      return response.data;
    } catch (error) {
      console.error('Error searching torrents:', error);
      throw error;
    }
  }

  /**
   * Download a torrent
   * @param {Object} torrentData - Torrent download data
   * @returns {Promise<Object>} Download response
   */
  async downloadTorrent(torrentData) {
    try {
      const response = await api.post('/api/v1/torrents/download', torrentData);
      return response.data;
    } catch (error) {
      console.error('Error downloading torrent:', error);
      throw error;
    }
  }

  /**
   * Get list of available indexers
   * @returns {Promise<Array>} List of indexer names
   */
  async getIndexers() {
    try {
      const response = await api.get('/api/v1/torrents/indexers');
      return response.data;
    } catch (error) {
      console.error('Error getting indexers:', error);
      throw error;
    }
  }

  /**
   * Check health of torrent indexers
   * @returns {Promise<Object>} Health status
   */
  async checkIndexerHealth() {
    try {
      const response = await api.get('/api/v1/torrents/indexers/health');
      return response.data;
    } catch (error) {
      console.error('Error checking indexer health:', error);
      throw error;
    }
  }

  /**
   * Test specific indexer
   * @param {string} indexerName - Name of indexer to test
   * @returns {Promise<Object>} Test result
   */
  async testIndexer(indexerName) {
    try {
      const response = await api.post(`/api/v1/torrents/indexers/${indexerName}/test`);
      return response.data;
    } catch (error) {
      console.error(`Error testing indexer ${indexerName}:`, error);
      throw error;
    }
  }

  /**
   * Format file size for display
   * @param {number} bytes - Size in bytes
   * @returns {string} Formatted size
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Format upload date for display
   * @param {string} dateString - ISO date string
   * @returns {string} Formatted date
   */
  formatUploadDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7);
      return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
    } else if (diffDays < 365) {
      const months = Math.floor(diffDays / 30);
      return `${months} month${months > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  /**
   * Get health color for seeders/leechers
   * @param {number} seeders - Number of seeders
   * @param {number} leechers - Number of leechers
   * @returns {string} CSS color class
   */
  getHealthColor(seeders, leechers) {
    const ratio = leechers > 0 ? seeders / leechers : seeders;
    
    if (seeders === 0) {
      return 'text-red-600 dark:text-red-400'; // Dead
    } else if (ratio >= 2) {
      return 'text-green-600 dark:text-green-400'; // Excellent
    } else if (ratio >= 1) {
      return 'text-yellow-600 dark:text-yellow-400'; // Good
    } else {
      return 'text-orange-600 dark:text-orange-400'; // Fair
    }
  }

  /**
   * Get health status text
   * @param {number} seeders - Number of seeders
   * @param {number} leechers - Number of leechers
   * @returns {string} Health status
   */
  getHealthStatus(seeders, leechers) {
    const ratio = leechers > 0 ? seeders / leechers : seeders;
    
    if (seeders === 0) {
      return 'Dead';
    } else if (ratio >= 2) {
      return 'Excellent';
    } else if (ratio >= 1) {
      return 'Good';
    } else {
      return 'Fair';
    }
  }

  /**
   * Filter torrents by quality criteria
   * @param {Array} torrents - Array of torrent results
   * @param {Object} filters - Filter criteria
   * @returns {Array} Filtered torrents
   */
  filterTorrents(torrents, filters = {}) {
    return torrents.filter(torrent => {
      // Minimum seeders filter
      if (filters.minSeeders && torrent.seeders < filters.minSeeders) {
        return false;
      }

      // Size filters
      if (filters.maxSizeGB) {
        const sizeGB = torrent.size_bytes / (1024 ** 3);
        if (sizeGB > filters.maxSizeGB) {
          return false;
        }
      }

      if (filters.minSizeMB) {
        const sizeMB = torrent.size_bytes / (1024 ** 2);
        if (sizeMB < filters.minSizeMB) {
          return false;
        }
      }

      // Exclude keywords
      if (filters.excludeKeywords && filters.excludeKeywords.length > 0) {
        const title = torrent.title.toLowerCase();
        for (const keyword of filters.excludeKeywords) {
          if (title.includes(keyword.toLowerCase())) {
            return false;
          }
        }
      }

      // Include keywords (all must be present)
      if (filters.includeKeywords && filters.includeKeywords.length > 0) {
        const title = torrent.title.toLowerCase();
        for (const keyword of filters.includeKeywords) {
          if (!title.includes(keyword.toLowerCase())) {
            return false;
          }
        }
      }

      return true;
    });
  }

  /**
   * Sort torrents by specified criteria
   * @param {Array} torrents - Array of torrent results
   * @param {string} sortBy - Sort field (seeders, size, date)
   * @param {string} order - Sort order (asc, desc)
   * @returns {Array} Sorted torrents
   */
  sortTorrents(torrents, sortBy = 'seeders', order = 'desc') {
    const sorted = [...torrents].sort((a, b) => {
      let aValue, bValue;

      switch (sortBy) {
        case 'seeders':
          aValue = a.seeders;
          bValue = b.seeders;
          break;
        case 'size':
          aValue = a.size_bytes;
          bValue = b.size_bytes;
          break;
        case 'date':
          aValue = new Date(a.upload_date);
          bValue = new Date(b.upload_date);
          break;
        case 'title':
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        default:
          return 0;
      }

      if (order === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return sorted;
  }

  /**
   * Get recommended torrent from results
   * @param {Array} torrents - Array of torrent results
   * @returns {Object|null} Best torrent or null
   */
  getBestTorrent(torrents) {
    if (!torrents || torrents.length === 0) {
      return null;
    }

    // Score torrents based on multiple factors
    const scoredTorrents = torrents.map(torrent => {
      let score = 0;

      // Seeders score (0-40 points)
      score += Math.min(torrent.seeders * 2, 40);

      // Size score (prefer reasonable sizes, 0-20 points)
      const sizeGB = torrent.size_bytes / (1024 ** 3);
      if (sizeGB >= 0.1 && sizeGB <= 5) {
        score += 20;
      } else if (sizeGB <= 10) {
        score += 10;
      }

      // Recency score (0-20 points)
      const daysSinceUpload = (Date.now() - new Date(torrent.upload_date)) / (1000 * 60 * 60 * 24);
      if (daysSinceUpload <= 30) {
        score += 20;
      } else if (daysSinceUpload <= 90) {
        score += 10;
      }

      // Health ratio score (0-20 points)
      const ratio = torrent.leechers > 0 ? torrent.seeders / torrent.leechers : torrent.seeders;
      if (ratio >= 2) {
        score += 20;
      } else if (ratio >= 1) {
        score += 10;
      }

      return { ...torrent, score };
    });

    // Return highest scoring torrent
    return scoredTorrents.reduce((best, current) => 
      current.score > best.score ? current : best
    );
  }
}

export default new TorrentService();
