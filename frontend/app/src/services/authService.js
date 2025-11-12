import axios from "axios";

/**
 * Authentication service for token validation and session management
 */
class AuthService {
  constructor() {
    this.tokenValidationCache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Get token from storage
   */
  getToken() {
    return localStorage.getItem("token") || sessionStorage.getItem("token");
  }

  /**
   * Check if token exists in storage
   */
  hasToken() {
    return !!this.getToken();
  }

  /**
   * Validate token with server (with caching to avoid excessive requests)
   */
  async validateToken(token = null) {
    const tokenToValidate = token || this.getToken();

    if (!tokenToValidate) {
      console.log("AuthService: No token to validate");
      return false;
    }

    // Check cache first
    const cacheKey = tokenToValidate;
    const cached = this.tokenValidationCache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      console.log(
        "AuthService: Using cached validation result:",
        cached.isValid,
      );
      return cached.isValid;
    }

    console.log("AuthService: Validating token with server");
    try {
      // Validate with server
      const response = await axios.get("/api/v1/users/me", {
        headers: {
          Authorization: `Bearer ${tokenToValidate}`,
        },
        timeout: 5000, // 5 second timeout for route guards
      });

      console.log("AuthService: Token validation successful");

      // Cache successful validation
      this.tokenValidationCache.set(cacheKey, {
        isValid: true,
        timestamp: Date.now(),
      });

      return true;
    } catch (error) {
      console.log(
        "AuthService: Token validation failed:",
        error.response?.status,
        error.message,
      );

      // Cache failed validation (shorter cache time for failed validations)
      this.tokenValidationCache.set(cacheKey, {
        isValid: false,
        timestamp: Date.now(),
      });

      // Clear invalid token from storage only on 401 (unauthorized)
      if (error.response?.status === 401) {
        console.log("AuthService: Clearing invalid token from storage");
        this.clearToken();
      }

      return false;
    }
  }

  /**
   * Clear token from storage and cache
   */
  clearToken() {
    localStorage.removeItem("token");
    sessionStorage.removeItem("token");
    delete axios.defaults.headers.common["Authorization"];
    this.tokenValidationCache.clear();
  }

  /**
   * Check if user is authenticated (quick check without server validation)
   */
  isAuthenticated() {
    return this.hasToken();
  }

  /**
   * Check if user is authenticated with server validation
   */
  async isAuthenticatedWithValidation() {
    if (!this.hasToken()) {
      return false;
    }

    return await this.validateToken();
  }

  /**
   * Invalidate token cache (useful after logout or token refresh)
   */
  invalidateCache() {
    this.tokenValidationCache.clear();
  }

  /**
   * Get cached validation status (if available)
   */
  getCachedValidation(token = null) {
    const tokenToCheck = token || this.getToken();

    if (!tokenToCheck) {
      return null;
    }

    const cached = this.tokenValidationCache.get(tokenToCheck);

    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.isValid;
    }

    return null;
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;
