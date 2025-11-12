import { defineStore } from "pinia";
import axios from "axios";
import router from "../router";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    token:
      localStorage.getItem("token") || sessionStorage.getItem("token") || null,
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    getUser: (state) => state.user,
  },

  actions: {
    async login(username, password, rememberMe = false) {
      console.log("Auth store login called with:", { username, rememberMe });
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.post("/v1/auth/login", {
          username,
          password,
        });

        const { access_token, user } = response.data;

        this.token = access_token;
        this.user = user;

        // Always store token in localStorage for cross-tab compatibility
        // The "Remember Me" option can control session duration instead
        localStorage.setItem("token", access_token);
        sessionStorage.removeItem("token"); // Clear session storage

        // Set the Authorization header for all future requests
        axios.defaults.headers.common["Authorization"] =
          `Bearer ${access_token}`;

        router.push("/library");
      } catch (error) {
        // Extract detailed error message from API response
        if (error.response?.data?.detail) {
          // Handle validation errors (array format)
          if (Array.isArray(error.response.data.detail)) {
            const validationErrors = error.response.data.detail
              .map((err) => {
                const field = err.loc?.[err.loc.length - 1] || "field";
                return `${field}: ${err.msg}`;
              })
              .join(", ");
            this.error = `Login failed: ${validationErrors}`;
          } else {
            // Handle custom error messages (string format)
            this.error = error.response.data.detail;
          }
        } else if (error.response?.status === 500) {
          this.error = "Login failed: Server error. Please try again later.";
        } else if (error.response?.status === 401) {
          this.error = "Login failed: Invalid username or password.";
        } else if (error.code === "NETWORK_ERROR" || !error.response) {
          this.error =
            "Login failed: Unable to connect to server. Please check your internet connection and try again.";
        } else {
          this.error = `Login failed: ${error.message || "An unexpected error occurred. Please try again."}`;
        }

        console.error("Login error:", {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message,
          code: error.code,
        });
      } finally {
        this.loading = false;
      }
    },

    async register(email, username, password) {
      this.loading = true;
      this.error = null;

      try {
        await axios.post("/v1/auth/register", {
          email,
          username,
          password,
        });

        router.push("/login");
      } catch (error) {
        // Extract detailed error message from API response
        if (error.response?.data?.detail) {
          // Handle validation errors (array format)
          if (Array.isArray(error.response.data.detail)) {
            const validationErrors = error.response.data.detail
              .map((err) => {
                const field = err.loc?.[err.loc.length - 1] || "field";
                return `${field}: ${err.msg}`;
              })
              .join(", ");
            this.error = `Registration failed: ${validationErrors}`;
          } else {
            // Handle custom error messages (string format)
            this.error = error.response.data.detail;
          }
        } else if (error.response?.status === 500) {
          this.error =
            "Registration failed: Server error. Please try again later.";
        } else if (error.response?.status === 400) {
          this.error =
            "Registration failed: Invalid input data. Please check your information and try again.";
        } else if (error.code === "NETWORK_ERROR" || !error.response) {
          this.error =
            "Registration failed: Unable to connect to server. Please check your internet connection and try again.";
        } else {
          this.error = `Registration failed: ${error.message || "An unexpected error occurred. Please try again."}`;
        }

        console.error("Registration error:", {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message,
          code: error.code,
        });
      } finally {
        this.loading = false;
      }
    },

    async fetchUser() {
      if (!this.token) return;

      this.loading = true;

      try {
        const response = await axios.get("/v1/users/me");
        this.user = response.data;
      } catch (error) {
        console.error("Error fetching user:", error);
        if (error.response?.status === 401) {
          this.logout();
        }
      } finally {
        this.loading = false;
      }
    },

    async logout() {
      // Call backend logout endpoint to blacklist token
      try {
        if (this.token) {
          await axios.post("/v1/auth/logout");
        }
      } catch (error) {
        console.error("Logout error:", error);
        // Continue with logout even if backend call fails
      }

      this.user = null;
      this.token = null;

      localStorage.removeItem("token");
      sessionStorage.removeItem("token");
      delete axios.defaults.headers.common["Authorization"];

      // Clear auth service cache
      try {
        const { authService } = await import("../services/authService.js");
        authService.invalidateCache();
      } catch (error) {
        console.error("Error clearing auth cache:", error);
      }

      router.push("/login");
    },

    initAuth() {
      // Re-read token from storage in case it was set in another tab
      const storedToken =
        localStorage.getItem("token") || sessionStorage.getItem("token");

      // Update token if it's different from what's in storage
      if (storedToken && storedToken !== this.token) {
        this.token = storedToken;
      } else if (!storedToken && this.token) {
        this.token = null;
        this.user = null;
      }

      if (this.token) {
        axios.defaults.headers.common["Authorization"] = `Bearer ${this.token}`;
        this.fetchUser();
      }
    },
  },
});
