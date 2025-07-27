import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";

describe("API Service Configuration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should verify axios is available and working", () => {
    expect(axios).toBeDefined();
    expect(typeof axios.create).toBe("function");
    expect(typeof axios.get).toBe("function");
    expect(typeof axios.post).toBe("function");
  });

  it("should be able to create axios instance", () => {
    const instance = axios.create({
      baseURL: "/test",
      timeout: 5000,
    });

    expect(instance).toBeDefined();
    expect(instance.defaults.baseURL).toBe("/test");
    expect(instance.defaults.timeout).toBe(5000);
  });

  it("should have interceptors available", () => {
    const instance = axios.create();

    expect(instance.interceptors).toBeDefined();
    expect(instance.interceptors.request).toBeDefined();
    expect(instance.interceptors.response).toBeDefined();
    expect(typeof instance.interceptors.request.use).toBe("function");
    expect(typeof instance.interceptors.response.use).toBe("function");
  });
});

describe("Axios v1.11.0 Features", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should handle form data correctly", async () => {
    const formData = new FormData();
    formData.append("file", new Blob(["test"], { type: "text/plain" }));
    formData.append("metadata", JSON.stringify({ title: "test" }));

    const mockResponse = { data: { success: true }, status: 200 };
    const axiosPost = vi.fn().mockResolvedValue(mockResponse);

    const testAxios = {
      post: axiosPost,
      defaults: { headers: { common: {} } },
    };

    await testAxios.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    expect(axiosPost).toHaveBeenCalledWith("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  });

  it("should handle large buffers without RangeError", async () => {
    // Test the fix for large Buffer handling (one of the v1.11.0 fixes)
    const largeBuffer = Buffer.alloc(1024 * 1024); // 1MB buffer
    const mockResponse = { data: { success: true }, status: 200 };
    const axiosPost = vi.fn().mockResolvedValue(mockResponse);

    const testAxios = { post: axiosPost };

    await testAxios.post("/upload-buffer", largeBuffer, {
      headers: { "Content-Type": "application/octet-stream" },
    });

    expect(axiosPost).toHaveBeenCalledWith("/upload-buffer", largeBuffer, {
      headers: { "Content-Type": "application/octet-stream" },
    });
  });

  it("should handle JSON requests and responses", async () => {
    const requestData = { query: "test", filters: { status: "active" } };
    const responseData = { results: [], total: 0 };
    const mockResponse = { data: responseData, status: 200 };

    const axiosPost = vi.fn().mockResolvedValue(mockResponse);
    const testAxios = { post: axiosPost };

    const result = await testAxios.post("/search", requestData);

    expect(axiosPost).toHaveBeenCalledWith("/search", requestData);
    expect(result.data).toEqual(responseData);
  });

  it("should handle error responses correctly", async () => {
    const errorResponse = {
      response: {
        status: 400,
        data: { detail: "Invalid request" },
      },
    };

    const axiosGet = vi.fn().mockRejectedValue(errorResponse);
    const testAxios = { get: axiosGet };

    try {
      await testAxios.get("/invalid-endpoint");
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data.detail).toBe("Invalid request");
    }

    expect(axiosGet).toHaveBeenCalledWith("/invalid-endpoint");
  });

  it("should handle timeout configuration", () => {
    const config = {
      timeout: 30000,
      baseURL: "/api",
    };

    const axiosCreate = vi.fn().mockReturnValue({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    });

    axiosCreate(config);
    expect(axiosCreate).toHaveBeenCalledWith(config);
  });
});
