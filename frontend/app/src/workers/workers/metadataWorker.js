/**
 * Metadata processing worker
 * Handles metadata updates, enrichment, and validation in background
 */

class MetadataWorker {
  constructor() {
    this.activeJobs = new Map();
  }

  /**
   * Process metadata updates
   */
  async updateMetadata(jobId, mangaList, options = {}) {
    try {
      const batchSize = options.batchSize || 10;
      const total = mangaList.length;
      let processed = 0;
      const results = [];

      // Process in batches to avoid blocking
      for (let i = 0; i < mangaList.length; i += batchSize) {
        const batch = mangaList.slice(i, i + batchSize);

        for (const manga of batch) {
          if (this.isJobCancelled(jobId)) {
            throw new Error("Job cancelled");
          }

          try {
            const updatedMetadata = await this.processMetadataItem(
              manga,
              options,
            );
            results.push(updatedMetadata);
            processed++;

            // Report progress
            this.postMessage({
              jobId,
              type: "progress",
              data: {
                processed,
                total,
                percentage: Math.round((processed / total) * 100),
                current: manga.title,
              },
            });
          } catch (error) {
            console.warn(
              `Failed to process metadata for ${manga.title}:`,
              error,
            );
            results.push({ ...manga, error: error.message });
            processed++;
          }
        }

        // Small delay to prevent blocking
        await this.sleep(10);
      }

      this.postMessage({
        jobId,
        type: "complete",
        data: results,
      });
    } catch (error) {
      this.postMessage({
        jobId,
        type: "error",
        error: error.message,
      });
    }
  }

  /**
   * Process individual metadata item
   */
  async processMetadataItem(manga, options) {
    const metadata = { ...manga };

    // Normalize title
    if (metadata.title) {
      metadata.normalizedTitle = this.normalizeTitle(metadata.title);
    }

    // Extract and normalize genres
    if (metadata.genres) {
      metadata.normalizedGenres = this.normalizeGenres(metadata.genres);
    }

    // Normalize authors
    if (metadata.authors) {
      metadata.normalizedAuthors = this.normalizeAuthors(metadata.authors);
    }

    // Calculate content rating
    metadata.contentRating = this.calculateContentRating(metadata);

    // Extract keywords from description
    if (metadata.description) {
      metadata.keywords = this.extractKeywords(metadata.description);
    }

    // Calculate similarity hash for duplicate detection
    metadata.similarityHash = this.calculateSimilarityHash(metadata);

    // Validate metadata completeness
    metadata.completeness = this.calculateCompleteness(metadata);

    // Add processing timestamp
    metadata.lastProcessed = new Date().toISOString();

    return metadata;
  }

  /**
   * Normalize title for better matching
   */
  normalizeTitle(title) {
    return title
      .toLowerCase()
      .replace(/[^\w\s]/g, "") // Remove special characters
      .replace(/\s+/g, " ") // Normalize whitespace
      .trim();
  }

  /**
   * Normalize genres
   */
  normalizeGenres(genres) {
    const genreMap = {
      action: ["action", "fighting", "battle"],
      adventure: ["adventure", "journey"],
      comedy: ["comedy", "humor", "funny"],
      drama: ["drama", "dramatic"],
      fantasy: ["fantasy", "magic", "magical"],
      horror: ["horror", "scary", "terror"],
      mystery: ["mystery", "detective", "investigation"],
      romance: ["romance", "love", "romantic"],
      "sci-fi": ["sci-fi", "science fiction", "scifi", "futuristic"],
      "slice of life": ["slice of life", "daily life", "everyday"],
      sports: ["sports", "athletic", "competition"],
      supernatural: ["supernatural", "paranormal", "occult"],
      thriller: ["thriller", "suspense", "tension"],
    };

    const normalized = [];

    for (const genre of genres) {
      const lowerGenre = genre.toLowerCase();
      let found = false;

      for (const [canonical, variants] of Object.entries(genreMap)) {
        if (variants.includes(lowerGenre)) {
          if (!normalized.includes(canonical)) {
            normalized.push(canonical);
          }
          found = true;
          break;
        }
      }

      if (!found) {
        normalized.push(lowerGenre);
      }
    }

    return normalized;
  }

  /**
   * Normalize authors
   */
  normalizeAuthors(authors) {
    return authors.map((author) => ({
      ...author,
      normalizedName: author.name
        .toLowerCase()
        .replace(/[^\w\s]/g, "")
        .replace(/\s+/g, " ")
        .trim(),
    }));
  }

  /**
   * Calculate content rating based on genres and keywords
   */
  calculateContentRating(metadata) {
    const matureGenres = ["horror", "mature", "adult", "ecchi", "hentai"];
    const matureKeywords = ["violence", "blood", "gore", "sexual", "adult"];

    let score = 0;

    // Check genres
    if (metadata.genres) {
      for (const genre of metadata.genres) {
        if (matureGenres.some((mg) => genre.toLowerCase().includes(mg))) {
          score += 2;
        }
      }
    }

    // Check description for mature keywords
    if (metadata.description) {
      const description = metadata.description.toLowerCase();
      for (const keyword of matureKeywords) {
        if (description.includes(keyword)) {
          score += 1;
        }
      }
    }

    if (score >= 4) return "mature";
    if (score >= 2) return "teen";
    return "everyone";
  }

  /**
   * Extract keywords from description
   */
  extractKeywords(description) {
    const stopWords = new Set([
      "the",
      "a",
      "an",
      "and",
      "or",
      "but",
      "in",
      "on",
      "at",
      "to",
      "for",
      "of",
      "with",
      "by",
      "is",
      "are",
      "was",
      "were",
      "be",
      "been",
      "have",
      "has",
      "had",
      "do",
      "does",
      "did",
      "will",
      "would",
      "could",
      "should",
    ]);

    const words = description
      .toLowerCase()
      .replace(/[^\w\s]/g, " ")
      .split(/\s+/)
      .filter((word) => word.length > 3 && !stopWords.has(word));

    // Count word frequency
    const frequency = {};
    for (const word of words) {
      frequency[word] = (frequency[word] || 0) + 1;
    }

    // Return top keywords
    return Object.entries(frequency)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([word]) => word);
  }

  /**
   * Calculate similarity hash for duplicate detection
   */
  calculateSimilarityHash(metadata) {
    const components = [
      metadata.normalizedTitle || "",
      (metadata.normalizedAuthors || []).map((a) => a.normalizedName).join(""),
      (metadata.normalizedGenres || []).join(""),
      (metadata.keywords || []).slice(0, 5).join(""),
    ];

    return this.simpleHash(components.join(""));
  }

  /**
   * Simple hash function
   */
  simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(36);
  }

  /**
   * Calculate metadata completeness score
   */
  calculateCompleteness(metadata) {
    const fields = [
      "title",
      "description",
      "authors",
      "genres",
      "status",
      "rating",
      "language",
      "cover_url",
    ];

    let score = 0;
    let total = fields.length;

    for (const field of fields) {
      if (metadata[field]) {
        if (Array.isArray(metadata[field])) {
          score += metadata[field].length > 0 ? 1 : 0;
        } else if (typeof metadata[field] === "string") {
          score += metadata[field].trim().length > 0 ? 1 : 0;
        } else {
          score += 1;
        }
      }
    }

    return Math.round((score / total) * 100);
  }

  /**
   * Check if job is cancelled
   */
  isJobCancelled(jobId) {
    return this.activeJobs.has(jobId) && this.activeJobs.get(jobId).cancelled;
  }

  /**
   * Cancel a job
   */
  cancelJob(jobId) {
    if (this.activeJobs.has(jobId)) {
      this.activeJobs.get(jobId).cancelled = true;
    }
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Post message to main thread
   */
  postMessage(data) {
    self.postMessage(data);
  }
}

// Create worker instance
const worker = new MetadataWorker();

// Handle messages from main thread
self.onmessage = async function (event) {
  const { jobId, task, data, options } = event.data;

  switch (task) {
    case "updateMetadata":
      worker.activeJobs.set(jobId, { cancelled: false });
      await worker.updateMetadata(jobId, data, options);
      worker.activeJobs.delete(jobId);
      break;

    case "cancel":
      worker.cancelJob(jobId);
      break;

    default:
      worker.postMessage({
        jobId,
        type: "error",
        error: `Unknown task: ${task}`,
      });
  }
};
