/**
 * Background processor for heavy operations
 * Handles metadata updates, image processing, duplicate detection, etc.
 */

class BackgroundProcessor {
  constructor() {
    this.workers = new Map();
    this.taskQueue = [];
    this.activeJobs = new Map();
    this.maxWorkers = navigator.hardwareConcurrency || 4;
    this.jobId = 0;
  }

  /**
   * Initialize worker pool
   */
  async initializeWorkers() {
    const workerTypes = ['metadata', 'image', 'duplicate', 'statistics'];
    
    for (const type of workerTypes) {
      try {
        const worker = new Worker(
          new URL(`./workers/${type}Worker.js`, import.meta.url),
          { type: 'module' }
        );
        
        worker.onmessage = (event) => this.handleWorkerMessage(type, event);
        worker.onerror = (error) => this.handleWorkerError(type, error);
        
        this.workers.set(type, worker);
      } catch (error) {
        console.warn(`Failed to initialize ${type} worker:`, error);
      }
    }
  }

  /**
   * Handle worker messages
   */
  handleWorkerMessage(workerType, event) {
    const { jobId, type, data, error } = event.data;
    const job = this.activeJobs.get(jobId);
    
    if (!job) return;
    
    switch (type) {
      case 'progress':
        job.onProgress?.(data);
        break;
      case 'complete':
        job.resolve(data);
        this.activeJobs.delete(jobId);
        break;
      case 'error':
        job.reject(new Error(error));
        this.activeJobs.delete(jobId);
        break;
    }
  }

  /**
   * Handle worker errors
   */
  handleWorkerError(workerType, error) {
    console.error(`Worker ${workerType} error:`, error);
    
    // Find and reject all jobs for this worker
    for (const [jobId, job] of this.activeJobs.entries()) {
      if (job.workerType === workerType) {
        job.reject(error);
        this.activeJobs.delete(jobId);
      }
    }
  }

  /**
   * Submit a job to be processed in background
   */
  async submitJob(workerType, task, data, options = {}) {
    return new Promise((resolve, reject) => {
      const jobId = ++this.jobId;
      const worker = this.workers.get(workerType);
      
      if (!worker) {
        reject(new Error(`Worker ${workerType} not available`));
        return;
      }
      
      const job = {
        jobId,
        workerType,
        task,
        data,
        options,
        resolve,
        reject,
        onProgress: options.onProgress,
        createdAt: Date.now()
      };
      
      this.activeJobs.set(jobId, job);
      
      // Send job to worker
      worker.postMessage({
        jobId,
        task,
        data,
        options
      });
      
      // Set timeout if specified
      if (options.timeout) {
        setTimeout(() => {
          if (this.activeJobs.has(jobId)) {
            this.activeJobs.delete(jobId);
            reject(new Error('Job timeout'));
          }
        }, options.timeout);
      }
    });
  }

  /**
   * Process metadata updates in background
   */
  async processMetadataUpdates(mangaList, options = {}) {
    return this.submitJob('metadata', 'updateMetadata', mangaList, {
      ...options,
      batchSize: options.batchSize || 10
    });
  }

  /**
   * Process image optimization in background
   */
  async processImageOptimization(imageUrls, options = {}) {
    return this.submitJob('image', 'optimizeImages', imageUrls, {
      ...options,
      quality: options.quality || 'medium',
      format: options.format || 'webp'
    });
  }

  /**
   * Detect duplicates in background
   */
  async detectDuplicates(mangaList, options = {}) {
    return this.submitJob('duplicate', 'detectDuplicates', mangaList, {
      ...options,
      threshold: options.threshold || 0.8,
      algorithm: options.algorithm || 'similarity'
    });
  }

  /**
   * Calculate statistics in background
   */
  async calculateStatistics(mangaList, options = {}) {
    return this.submitJob('statistics', 'calculateStats', mangaList, {
      ...options,
      includeGenres: options.includeGenres !== false,
      includeAuthors: options.includeAuthors !== false,
      includeReadingTime: options.includeReadingTime !== false
    });
  }

  /**
   * Get active jobs status
   */
  getActiveJobs() {
    const jobs = [];
    for (const [jobId, job] of this.activeJobs.entries()) {
      jobs.push({
        jobId,
        workerType: job.workerType,
        task: job.task,
        createdAt: job.createdAt,
        duration: Date.now() - job.createdAt
      });
    }
    return jobs;
  }

  /**
   * Cancel a job
   */
  cancelJob(jobId) {
    const job = this.activeJobs.get(jobId);
    if (job) {
      job.reject(new Error('Job cancelled'));
      this.activeJobs.delete(jobId);
      
      // Send cancel message to worker
      const worker = this.workers.get(job.workerType);
      if (worker) {
        worker.postMessage({
          jobId,
          task: 'cancel'
        });
      }
    }
  }

  /**
   * Cancel all jobs
   */
  cancelAllJobs() {
    for (const jobId of this.activeJobs.keys()) {
      this.cancelJob(jobId);
    }
  }

  /**
   * Terminate all workers
   */
  terminate() {
    this.cancelAllJobs();
    
    for (const worker of this.workers.values()) {
      worker.terminate();
    }
    
    this.workers.clear();
  }
}

// Create singleton instance
const backgroundProcessor = new BackgroundProcessor();

// Initialize workers when module loads
backgroundProcessor.initializeWorkers().catch(error => {
  console.warn('Failed to initialize background workers:', error);
});

export default backgroundProcessor;

// Utility functions for common operations
export const background = {
  /**
   * Process metadata updates
   */
  updateMetadata: (mangaList, options) => 
    backgroundProcessor.processMetadataUpdates(mangaList, options),

  /**
   * Optimize images
   */
  optimizeImages: (imageUrls, options) => 
    backgroundProcessor.processImageOptimization(imageUrls, options),

  /**
   * Detect duplicates
   */
  detectDuplicates: (mangaList, options) => 
    backgroundProcessor.detectDuplicates(mangaList, options),

  /**
   * Calculate statistics
   */
  calculateStats: (mangaList, options) => 
    backgroundProcessor.calculateStatistics(mangaList, options),

  /**
   * Get job status
   */
  getJobs: () => backgroundProcessor.getActiveJobs(),

  /**
   * Cancel job
   */
  cancel: (jobId) => backgroundProcessor.cancelJob(jobId),

  /**
   * Cancel all jobs
   */
  cancelAll: () => backgroundProcessor.cancelAllJobs()
};

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  backgroundProcessor.terminate();
});
