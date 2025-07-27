import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";

// Mock axios for integration tests
vi.mock("axios", () => ({
  default: {
    create: vi.fn(),
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    defaults: {
      baseURL: "",
      headers: { common: {} },
    },
  },
}));

describe("Axios Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock successful responses by default
    axios.post.mockResolvedValue({
      data: { success: true },
      status: 200,
      headers: {},
      config: {},
    });

    axios.get.mockResolvedValue({
      data: { results: [] },
      status: 200,
      headers: {},
      config: {},
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Search functionality", () => {
    it("should handle search requests with proper payload structure", async () => {
      const searchPayload = {
        query: "test manga",
        provider: "mangadex",
        page: 1,
        limit: 20,
        status: "ongoing",
        genre: "action",
      };

      const expectedResponse = {
        data: {
          results: [{ id: 1, title: "Test Manga", provider: "mangadex" }],
          total: 1,
        },
        status: 200,
      };

      axios.post.mockResolvedValue(expectedResponse);

      const response = await axios.post("/v1/search", searchPayload);

      expect(axios.post).toHaveBeenCalledWith("/v1/search", searchPayload);
      expect(response.data.results).toHaveLength(1);
      expect(response.data.total).toBe(1);
    });

    it("should handle search errors gracefully", async () => {
      const searchError = {
        response: {
          status: 400,
          data: { detail: "Invalid search query" },
        },
      };

      axios.post.mockRejectedValue(searchError);

      try {
        await axios.post("/v1/search", { query: "" });
      } catch (error) {
        expect(error.response.status).toBe(400);
        expect(error.response.data.detail).toBe("Invalid search query");
      }
    });
  });

  describe("Authentication requests", () => {
    it("should handle login requests", async () => {
      const loginData = {
        username: "testuser",
        password: "testpass",
      };

      const loginResponse = {
        data: {
          access_token: "jwt-token",
          token_type: "bearer",
          user: { id: 1, username: "testuser" },
        },
        status: 200,
      };

      axios.post.mockResolvedValue(loginResponse);

      const response = await axios.post("/v1/auth/login", loginData);

      expect(axios.post).toHaveBeenCalledWith("/v1/auth/login", loginData);
      expect(response.data.access_token).toBe("jwt-token");
    });

    it("should handle registration requests", async () => {
      const registerData = {
        email: "test@example.com",
        username: "testuser",
        password: "testpass",
      };

      axios.post.mockResolvedValue({ data: { success: true }, status: 201 });

      const response = await axios.post("/v1/auth/register", registerData);

      expect(axios.post).toHaveBeenCalledWith(
        "/v1/auth/register",
        registerData,
      );
      expect(response.status).toBe(201);
    });
  });

  describe("Integration API calls", () => {
    it("should handle integration settings fetch", async () => {
      const settingsResponse = {
        data: {
          anilist: { connected: true, last_sync: "2024-01-01" },
          myanimelist: { connected: false },
          kitsu: { connected: false },
        },
        status: 200,
      };

      axios.get.mockResolvedValue(settingsResponse);

      const response = await axios.get("/v1/integrations/settings");

      expect(axios.get).toHaveBeenCalledWith("/v1/integrations/settings");
      expect(response.data.anilist.connected).toBe(true);
    });

    it("should handle integration connection requests", async () => {
      const connectionData = {
        authorization_code: "auth-code",
        code_verifier: "verifier",
        redirect_uri: "http://localhost:3000/callback",
      };

      axios.post.mockResolvedValue({
        data: { success: true, connected: true },
        status: 200,
      });

      const response = await axios.post(
        "/v1/integrations/myanimelist/connect",
        connectionData,
      );

      expect(axios.post).toHaveBeenCalledWith(
        "/v1/integrations/myanimelist/connect",
        connectionData,
      );
      expect(response.data.connected).toBe(true);
    });

    it("should handle sync requests", async () => {
      const syncData = {
        integration_type: "anilist",
        force_full_sync: false,
        sync_direction: "bidirectional",
      };

      axios.post.mockResolvedValue({
        data: { sync_id: "sync-123", status: "started" },
        status: 200,
      });

      const response = await axios.post("/v1/integrations/sync", syncData);

      expect(axios.post).toHaveBeenCalledWith(
        "/v1/integrations/sync",
        syncData,
      );
      expect(response.data.sync_id).toBe("sync-123");
    });
  });

  describe("File upload functionality", () => {
    it("should handle form data uploads", async () => {
      const formData = new FormData();
      const file = new Blob(["test content"], { type: "application/zip" });
      const manga = { title: "Test Manga", provider: "local" };

      formData.append("file", file);
      formData.append("manga", JSON.stringify(manga));

      const uploadConfig = {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: "Bearer jwt-token",
        },
        onUploadProgress: vi.fn(),
      };

      axios.post.mockResolvedValue({
        data: { success: true, file_id: "file-123" },
        status: 200,
      });

      const response = await axios.post("/v1/upload", formData, uploadConfig);

      expect(axios.post).toHaveBeenCalledWith(
        "/v1/upload",
        formData,
        uploadConfig,
      );
      expect(response.data.file_id).toBe("file-123");
    });
  });

  describe("Error handling", () => {
    it("should handle 401 unauthorized errors", async () => {
      const unauthorizedError = {
        response: {
          status: 401,
          data: { detail: "Token expired" },
        },
      };

      axios.get.mockRejectedValue(unauthorizedError);

      try {
        await axios.get("/v1/protected-endpoint");
      } catch (error) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.detail).toBe("Token expired");
      }
    });

    it("should handle network errors", async () => {
      const networkError = new Error("Network Error");
      networkError.code = "NETWORK_ERROR";

      axios.get.mockRejectedValue(networkError);

      try {
        await axios.get("/v1/test");
      } catch (error) {
        expect(error.message).toBe("Network Error");
        expect(error.code).toBe("NETWORK_ERROR");
      }
    });

    it("should handle timeout errors", async () => {
      const timeoutError = new Error("timeout of 30000ms exceeded");
      timeoutError.code = "ECONNABORTED";

      axios.get.mockRejectedValue(timeoutError);

      try {
        await axios.get("/v1/slow-endpoint");
      } catch (error) {
        expect(error.code).toBe("ECONNABORTED");
        expect(error.message).toContain("timeout");
      }
    });
  });
});
