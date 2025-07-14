import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";

// Mock API - must be defined before importing the store
vi.mock("../../services/api", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

import { useSecurityStore, ROLES, CONTENT_RATINGS } from "../security";
import api from "../../services/api";

describe("Security Store", () => {
  let securityStore;

  beforeEach(() => {
    setActivePinia(createPinia());
    securityStore = useSecurityStore();
    vi.clearAllMocks();
  });

  describe("Role Management", () => {
    it("should set user role correctly", async () => {
      await securityStore.setUserRole("admin");

      expect(securityStore.currentRole).toEqual(ROLES.ADMIN);
      expect(securityStore.permissions.has("users.manage")).toBe(true);
      expect(securityStore.permissions.has("content.manage")).toBe(true);
    });

    it("should throw error for invalid role", async () => {
      await expect(securityStore.setUserRole("invalid_role")).rejects.toThrow(
        "Invalid role: invalid_role",
      );
    });

    it("should check permissions correctly", () => {
      securityStore.currentRole = ROLES.USER;
      securityStore.permissions = new Set(["library.read", "library.write"]);

      expect(securityStore.hasPermission("library.read")).toBe(true);
      expect(securityStore.hasPermission("users.manage")).toBe(false);
    });

    it("should allow all permissions for super admin", () => {
      securityStore.currentRole = ROLES.SUPER_ADMIN;
      securityStore.permissions = new Set(["*"]);

      expect(securityStore.hasPermission("any.permission")).toBe(true);
      expect(securityStore.hasPermission("users.manage")).toBe(true);
    });

    it("should require permission correctly", () => {
      securityStore.currentRole = ROLES.USER;
      securityStore.permissions = new Set(["library.read"]);

      expect(() =>
        securityStore.requirePermission("library.read"),
      ).not.toThrow();
      expect(() => securityStore.requirePermission("users.manage")).toThrow(
        "Access denied: Missing permission 'users.manage'",
      );
    });
  });

  describe("Content Filtering", () => {
    it("should filter content based on rating", () => {
      securityStore.contentFilter = {
        maxRating: "PG-13",
        allowNSFW: false,
        blockedTags: [],
        allowedLanguages: ["en"],
      };

      const content1 = { rating: "G", isNSFW: false, tags: [], language: "en" };
      const content2 = { rating: "R", isNSFW: false, tags: [], language: "en" };
      const content3 = { rating: "PG", isNSFW: true, tags: [], language: "en" };

      expect(securityStore.canViewContent(content1)).toBe(true);
      expect(securityStore.canViewContent(content2)).toBe(false);
      expect(securityStore.canViewContent(content3)).toBe(false);
    });

    it("should filter content based on blocked tags", () => {
      securityStore.contentFilter = {
        maxRating: "NSFW",
        allowNSFW: true,
        blockedTags: ["violence", "explicit"],
        allowedLanguages: ["en"],
      };

      const content1 = {
        rating: "PG",
        isNSFW: false,
        tags: ["comedy"],
        language: "en",
      };
      const content2 = {
        rating: "PG",
        isNSFW: false,
        tags: ["violence"],
        language: "en",
      };

      expect(securityStore.canViewContent(content1)).toBe(true);
      expect(securityStore.canViewContent(content2)).toBe(false);
    });

    it("should filter content based on language", () => {
      securityStore.contentFilter = {
        maxRating: "NSFW",
        allowNSFW: true,
        blockedTags: [],
        allowedLanguages: ["en", "ja"],
      };

      const content1 = {
        rating: "PG",
        isNSFW: false,
        tags: [],
        language: "en",
      };
      const content2 = {
        rating: "PG",
        isNSFW: false,
        tags: [],
        language: "fr",
      };

      expect(securityStore.canViewContent(content1)).toBe(true);
      expect(securityStore.canViewContent(content2)).toBe(false);
    });

    it("should update content filter correctly", async () => {
      mockApi.put.mockResolvedValue({ data: {} });

      const newFilter = {
        maxRating: "R",
        allowNSFW: true,
      };

      await securityStore.updateContentFilter(newFilter);

      expect(securityStore.contentFilter.maxRating).toBe("R");
      expect(securityStore.contentFilter.allowNSFW).toBe(true);
      expect(mockApi.put).toHaveBeenCalledWith(
        "/user/content-filter",
        expect.objectContaining(newFilter),
      );
    });
  });

  describe("Session Management", () => {
    it("should fetch user sessions", async () => {
      const mockSessions = [
        { id: "1", isActive: true, deviceType: "desktop" },
        { id: "2", isActive: true, deviceType: "mobile" },
      ];

      mockApi.get.mockResolvedValue({ data: mockSessions });

      const sessions = await securityStore.fetchUserSessions();

      expect(sessions).toEqual(mockSessions);
      expect(securityStore.sessions).toEqual(mockSessions);
      expect(mockApi.get).toHaveBeenCalledWith("/auth/sessions");
    });

    it("should terminate session", async () => {
      securityStore.sessions = [
        { id: "1", isActive: true },
        { id: "2", isActive: true },
      ];

      mockApi.delete.mockResolvedValue({ data: {} });

      await securityStore.terminateSession("1");

      expect(securityStore.sessions).toHaveLength(1);
      expect(securityStore.sessions[0].id).toBe("2");
      expect(mockApi.delete).toHaveBeenCalledWith("/auth/sessions/1");
    });

    it("should terminate all other sessions", async () => {
      securityStore.currentSession = { id: "1" };
      securityStore.sessions = [
        { id: "1", isActive: true },
        { id: "2", isActive: true },
        { id: "3", isActive: true },
      ];

      mockApi.post.mockResolvedValue({ data: {} });

      await securityStore.terminateAllOtherSessions();

      expect(securityStore.sessions).toHaveLength(1);
      expect(securityStore.sessions[0].id).toBe("1");
      expect(mockApi.post).toHaveBeenCalledWith(
        "/auth/sessions/terminate-others",
      );
    });
  });

  describe("Two-Factor Authentication", () => {
    it("should enable two-factor authentication", async () => {
      const mockResponse = {
        secret: "ABCD1234",
        qrCode: "data:image/png;base64,abc123",
        backupCodes: ["code1", "code2"],
      };

      mockApi.post.mockResolvedValue({ data: mockResponse });

      const result = await securityStore.enableTwoFactor("totp");

      expect(result).toEqual(mockResponse);
      expect(securityStore.twoFactorEnabled).toBe(true);
      expect(securityStore.backupCodes).toEqual(mockResponse.backupCodes);
      expect(mockApi.post).toHaveBeenCalledWith("/auth/2fa/enable", {
        method: "totp",
      });
    });

    it("should disable two-factor authentication", async () => {
      securityStore.twoFactorEnabled = true;
      securityStore.backupCodes = ["code1", "code2"];

      mockApi.post.mockResolvedValue({ data: {} });

      await securityStore.disableTwoFactor("123456");

      expect(securityStore.twoFactorEnabled).toBe(false);
      expect(securityStore.backupCodes).toEqual([]);
      expect(mockApi.post).toHaveBeenCalledWith("/auth/2fa/disable", {
        code: "123456",
      });
    });

    it("should verify two-factor code", async () => {
      mockApi.post.mockResolvedValue({ data: { valid: true } });

      const result = await securityStore.verifyTwoFactor("123456");

      expect(result).toBe(true);
      expect(mockApi.post).toHaveBeenCalledWith("/auth/2fa/verify", {
        code: "123456",
      });
    });
  });

  describe("Privacy Settings", () => {
    it("should update privacy settings", async () => {
      mockApi.put.mockResolvedValue({ data: {} });

      const newSettings = {
        dataCollection: false,
        analytics: false,
      };

      await securityStore.updatePrivacySettings(newSettings);

      expect(securityStore.privacySettings.dataCollection).toBe(false);
      expect(securityStore.privacySettings.analytics).toBe(false);
      expect(mockApi.put).toHaveBeenCalledWith("/user/privacy", newSettings);
    });

    it("should export user data", async () => {
      const mockData = { userData: "exported data" };
      mockApi.post.mockResolvedValue({ data: mockData });

      const result = await securityStore.exportUserData();

      expect(result).toEqual(mockData);
      expect(mockApi.post).toHaveBeenCalledWith("/user/export-data");
    });

    it("should delete user data", async () => {
      mockApi.post.mockResolvedValue({ data: {} });

      await securityStore.deleteUserData();

      expect(mockApi.post).toHaveBeenCalledWith("/user/delete-data");
      // Should clear security state
      expect(securityStore.currentRole).toBeNull();
      expect(securityStore.permissions.size).toBe(0);
    });
  });

  describe("Audit Logging", () => {
    it("should log audit events", () => {
      const action = "test_action";
      const details = { key: "value" };

      securityStore.logAuditEvent(action, details);

      expect(securityStore.auditLog).toHaveLength(1);
      expect(securityStore.auditLog[0].action).toBe(action);
      expect(securityStore.auditLog[0].details).toEqual(details);
    });

    it("should log security events", () => {
      const type = "login_failure";
      const details = { attempts: 3 };

      securityStore.logSecurityEvent(type, details);

      expect(securityStore.securityEvents).toHaveLength(1);
      expect(securityStore.securityEvents[0].type).toBe(type);
      expect(securityStore.securityEvents[0].severity).toBe("warning");
      expect(securityStore.securityEvents[0].details).toEqual(details);
    });

    it("should limit audit log size", () => {
      // Fill audit log beyond limit
      for (let i = 0; i < 1100; i++) {
        securityStore.logAuditEvent(`action_${i}`);
      }

      expect(securityStore.auditLog).toHaveLength(1000);
    });

    it("should limit security events size", () => {
      // Fill security events beyond limit
      for (let i = 0; i < 600; i++) {
        securityStore.logSecurityEvent(`event_${i}`);
      }

      expect(securityStore.securityEvents).toHaveLength(500);
    });
  });

  describe("API Security", () => {
    it("should check rate limits", () => {
      const endpoint = "/api/test";

      // Should allow first request
      expect(securityStore.checkRateLimit(endpoint)).toBe(true);

      // Record requests up to limit
      securityStore.rateLimits.set(endpoint, {
        maxRequests: 2,
        windowMs: 60000,
        requests: [Date.now(), Date.now()],
      });

      // Should block when limit reached
      expect(securityStore.checkRateLimit(endpoint)).toBe(false);
    });

    it("should record API requests", () => {
      const endpoint = "/api/test";

      securityStore.recordAPIRequest(endpoint);

      const limit = securityStore.rateLimits.get(endpoint);
      expect(limit).toBeDefined();
      expect(limit.requests).toHaveLength(1);
    });

    it("should clean old rate limit requests", () => {
      const endpoint = "/api/test";
      const now = Date.now();
      const oldTime = now - 120000; // 2 minutes ago

      securityStore.rateLimits.set(endpoint, {
        maxRequests: 100,
        windowMs: 60000, // 1 minute window
        requests: [oldTime, now],
      });

      // Check rate limit should clean old requests
      securityStore.checkRateLimit(endpoint);

      const limit = securityStore.rateLimits.get(endpoint);
      expect(limit.requests).toHaveLength(1);
      expect(limit.requests[0]).toBe(now);
    });
  });

  describe("Security Score", () => {
    it("should calculate security score correctly", () => {
      // Reset to default state
      securityStore.twoFactorEnabled = false;
      securityStore.securitySettings.passwordPolicy.minLength = 8;
      securityStore.securitySettings.sessionTimeout = 3600000;
      securityStore.privacySettings.dataCollection = true;
      securityStore.privacySettings.analytics = true;
      securityStore.securityEvents = [];

      let score = securityStore.getSecurityScore;
      expect(score).toBe(25); // Base score with no security features

      // Enable 2FA
      securityStore.twoFactorEnabled = true;
      score = securityStore.getSecurityScore;
      expect(score).toBe(55); // +30 for 2FA

      // Strong password policy
      securityStore.securitySettings.passwordPolicy.minLength = 12;
      score = securityStore.getSecurityScore;
      expect(score).toBe(75); // +20 for strong password

      // Short session timeout
      securityStore.securitySettings.sessionTimeout = 1800000; // 30 minutes
      score = securityStore.getSecurityScore;
      expect(score).toBe(90); // +15 for short timeout

      // Privacy settings
      securityStore.privacySettings.dataCollection = false;
      securityStore.privacySettings.analytics = false;
      score = securityStore.getSecurityScore;
      expect(score).toBe(100); // +10 for privacy
    });
  });

  describe("Getters", () => {
    it("should identify admin users correctly", () => {
      securityStore.currentRole = ROLES.ADMIN;
      expect(securityStore.isAdmin).toBe(true);

      securityStore.currentRole = ROLES.USER;
      expect(securityStore.isAdmin).toBe(false);
    });

    it("should identify moderator users correctly", () => {
      securityStore.currentRole = ROLES.MODERATOR;
      expect(securityStore.isModerator).toBe(true);

      securityStore.currentRole = ROLES.USER;
      expect(securityStore.isModerator).toBe(true); // Users have moderator level

      securityStore.currentRole = ROLES.GUEST;
      expect(securityStore.isModerator).toBe(false);
    });

    it("should get active sessions correctly", () => {
      securityStore.sessions = [
        { id: "1", isActive: true },
        { id: "2", isActive: false },
        { id: "3", isActive: true },
      ];

      const activeSessions = securityStore.getActiveSessions;
      expect(activeSessions).toHaveLength(2);
      expect(activeSessions.map((s) => s.id)).toEqual(["1", "3"]);
    });

    it("should get security alerts correctly", () => {
      securityStore.securityEvents = [
        { id: "1", severity: "info" },
        { id: "2", severity: "high" },
        { id: "3", severity: "critical" },
        { id: "4", severity: "warning" },
      ];

      const alerts = securityStore.getSecurityAlerts;
      expect(alerts).toHaveLength(2);
      expect(alerts.map((a) => a.id)).toEqual(["2", "3"]);
    });
  });

  describe("Initialization", () => {
    it("should initialize security state correctly", async () => {
      const mockUser = { role: "user" };

      mockApi.get.mockImplementation((url) => {
        switch (url) {
          case "/user/privacy":
            return Promise.resolve({ data: { dataCollection: false } });
          case "/user/content-filter":
            return Promise.resolve({ data: { maxRating: "R" } });
          case "/auth/2fa/status":
            return Promise.resolve({ data: { enabled: true } });
          default:
            return Promise.reject(new Error("Unknown endpoint"));
        }
      });

      await securityStore.initializeSecurity(mockUser);

      expect(securityStore.currentRole).toEqual(ROLES.USER);
      expect(securityStore.privacySettings.dataCollection).toBe(false);
      expect(securityStore.contentFilter.maxRating).toBe("R");
      expect(securityStore.twoFactorEnabled).toBe(true);
    });
  });
});

afterEach(() => {
  vi.clearAllTimers();
});
