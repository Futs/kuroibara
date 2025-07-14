/**
 * Enhanced security store with RBAC, audit logging, and privacy controls
 */

import { defineStore } from 'pinia';
import api from '../services/api';
import { useAuthStore } from './auth';

// Role definitions with hierarchical permissions
export const ROLES = {
  SUPER_ADMIN: {
    id: 'super_admin',
    name: 'Super Administrator',
    level: 100,
    permissions: ['*'], // All permissions
    description: 'Full system access with all administrative privileges',
    color: 'red'
  },
  ADMIN: {
    id: 'admin',
    name: 'Administrator',
    level: 80,
    permissions: [
      'users.manage',
      'content.manage',
      'system.configure',
      'security.monitor',
      'audit.view',
      'providers.manage',
      'library.admin',
      'roles.assign'
    ],
    description: 'Administrative access with user and content management',
    color: 'purple'
  },
  MODERATOR: {
    id: 'moderator',
    name: 'Moderator',
    level: 60,
    permissions: [
      'content.moderate',
      'users.view',
      'reports.handle',
      'comments.moderate',
      'library.moderate',
      'content.flag'
    ],
    description: 'Content moderation and user management',
    color: 'blue'
  },
  USER: {
    id: 'user',
    name: 'User',
    level: 40,
    permissions: [
      'library.read',
      'library.write',
      'profile.manage',
      'reading.track',
      'comments.create',
      'bookmarks.manage',
      'collections.manage',
      'downloads.manage'
    ],
    description: 'Standard user with full reading and personal library access',
    color: 'green'
  },
  LIMITED_USER: {
    id: 'limited_user',
    name: 'Limited User',
    level: 20,
    permissions: [
      'library.read',
      'profile.view',
      'reading.track',
      'comments.view'
    ],
    description: 'Limited user with read-only access',
    color: 'yellow'
  },
  GUEST: {
    id: 'guest',
    name: 'Guest',
    level: 10,
    permissions: [
      'content.browse',
      'content.preview'
    ],
    description: 'Guest access with limited browsing capabilities',
    color: 'gray'
  }
};

// Content rating system
export const CONTENT_RATINGS = {
  G: { level: 0, name: 'General', description: 'Suitable for all ages' },
  PG: { level: 1, name: 'Parental Guidance', description: 'Parental guidance suggested' },
  'PG-13': { level: 2, name: 'PG-13', description: 'Parents strongly cautioned' },
  R: { level: 3, name: 'Restricted', description: 'Restricted content' },
  'NC-17': { level: 4, name: 'Adults Only', description: 'No one 17 and under admitted' },
  NSFW: { level: 5, name: 'Not Safe for Work', description: 'Adult content' }
};

export const useSecurityStore = defineStore('security', {
  state: () => ({
    // Role and permission management
    currentRole: null,
    permissions: new Set(),
    roleHierarchy: ROLES,
    
    // Content filtering
    contentFilter: {
      maxRating: 'PG-13',
      allowNSFW: false,
      blockedTags: [],
      allowedLanguages: ['en'],
      hideExplicit: true
    },
    
    // Session management
    sessions: [],
    currentSession: null,
    deviceInfo: null,
    securitySettings: {
      sessionTimeout: 3600000, // 1 hour
      maxConcurrentSessions: 5,
      requireTwoFactor: false,
      autoLogoutInactive: true,
      passwordPolicy: {
        minLength: 8,
        requireUppercase: true,
        requireLowercase: true,
        requireNumbers: true,
        requireSpecialChars: true,
        preventReuse: 5
      }
    },
    
    // Two-factor authentication
    twoFactorEnabled: false,
    twoFactorMethods: ['totp', 'email', 'sms'],
    backupCodes: [],
    
    // Audit logging
    auditLog: [],
    securityEvents: [],
    
    // Privacy settings
    privacySettings: {
      dataCollection: true,
      analytics: true,
      personalizedContent: true,
      shareReadingData: false,
      publicProfile: false,
      allowCookies: true,
      trackingConsent: null
    },
    
    // API security
    rateLimits: new Map(),
    blockedIPs: new Set(),
    suspiciousActivity: [],
    
    // UI state
    loading: false,
    error: null,
  }),

  getters: {
    // Role and permission getters
    getCurrentRole: (state) => state.currentRole,
    getUserPermissions: (state) => Array.from(state.permissions),
    
    // Role level checking
    isAdmin: (state) => state.currentRole?.level >= ROLES.ADMIN.level,
    isModerator: (state) => state.currentRole?.level >= ROLES.MODERATOR.level,
    isUser: (state) => state.currentRole?.level >= ROLES.USER.level,
    
    // Permission checking
    hasPermission: (state) => (permission) => {
      if (!state.permissions.size) return false;
      if (state.permissions.has('*')) return true;
      return state.permissions.has(permission);
    },
    
    hasAnyPermission: (state) => (permissions) => {
      if (!state.permissions.size) return false;
      if (state.permissions.has('*')) return true;
      return permissions.some(permission => state.permissions.has(permission));
    },
    
    hasAllPermissions: (state) => (permissions) => {
      if (!state.permissions.size) return false;
      if (state.permissions.has('*')) return true;
      return permissions.every(permission => state.permissions.has(permission));
    },
    
    // Content filtering
    canViewContent: (state) => (content) => {
      const filter = state.contentFilter;
      const contentRating = CONTENT_RATINGS[content.rating] || CONTENT_RATINGS.G;
      const maxRating = CONTENT_RATINGS[filter.maxRating] || CONTENT_RATINGS.G;
      
      // Check rating level
      if (contentRating.level > maxRating.level) return false;
      
      // Check NSFW content
      if (content.isNSFW && !filter.allowNSFW) return false;
      
      // Check blocked tags
      if (content.tags && content.tags.some(tag => filter.blockedTags.includes(tag))) {
        return false;
      }
      
      // Check language
      if (content.language && !filter.allowedLanguages.includes(content.language)) {
        return false;
      }
      
      return true;
    },
    
    getContentFilter: (state) => {
      const role = state.currentRole;
      if (!role) return { allowAll: false, maxRating: 'G' };
      
      switch (role.id) {
        case 'super_admin':
        case 'admin':
          return { allowAll: true };
        case 'moderator':
          return { allowAll: true, canModerate: true };
        case 'user':
          return state.contentFilter;
        case 'limited_user':
          return { 
            maxRating: 'PG', 
            allowNSFW: false,
            allowedLanguages: state.contentFilter.allowedLanguages
          };
        case 'guest':
          return { 
            maxRating: 'G', 
            allowNSFW: false, 
            previewOnly: true,
            allowedLanguages: ['en']
          };
        default:
          return { allowAll: false, maxRating: 'G' };
      }
    },
    
    // Security status
    getSecurityScore: (state) => {
      let score = 0;
      
      // Two-factor authentication
      if (state.twoFactorEnabled) score += 30;
      
      // Strong password policy
      if (state.securitySettings.passwordPolicy.minLength >= 12) score += 20;
      
      // Session security
      if (state.securitySettings.sessionTimeout <= 1800000) score += 15; // 30 minutes
      
      // Privacy settings
      if (!state.privacySettings.dataCollection) score += 10;
      if (!state.privacySettings.analytics) score += 10;
      
      // Recent security events
      const recentEvents = state.securityEvents.filter(
        event => Date.now() - new Date(event.timestamp).getTime() < 86400000 // 24 hours
      );
      if (recentEvents.length === 0) score += 15;
      
      return Math.min(score, 100);
    },
    
    getActiveSessions: (state) => state.sessions.filter(s => s.isActive),
    
    getRecentAuditEvents: (state) => (limit = 50) => {
      return state.auditLog.slice(0, limit);
    },
    
    getSecurityAlerts: (state) => {
      return state.securityEvents.filter(event => 
        event.severity === 'high' || event.severity === 'critical'
      );
    },
  },

  actions: {
    // Role and permission management
    async setUserRole(roleId, userId = null) {
      const authStore = useAuthStore();
      
      // Check permission to assign roles
      if (userId && userId !== authStore.user?.id) {
        this.requirePermission('roles.assign');
      }
      
      const role = ROLES[roleId.toUpperCase()];
      if (!role) {
        throw new Error(`Invalid role: ${roleId}`);
      }
      
      this.currentRole = role;
      this.permissions = new Set(role.permissions);
      
      // Update content filter based on role
      this.updateContentFilterForRole(role);
      
      // Log role change
      this.logAuditEvent('role_assigned', {
        userId: userId || authStore.user?.id,
        roleId: role.id,
        permissions: role.permissions,
        assignedBy: authStore.user?.id
      });
      
      // Save to server if for current user
      if (!userId || userId === authStore.user?.id) {
        try {
          await api.put('/user/role', { roleId: role.id });
        } catch (error) {
          console.error('Failed to save role to server:', error);
        }
      }
    },

    updateContentFilterForRole(role) {
      switch (role.id) {
        case 'super_admin':
        case 'admin':
        case 'moderator':
          this.contentFilter = {
            maxRating: 'NSFW',
            allowNSFW: true,
            blockedTags: [],
            allowedLanguages: ['*'],
            hideExplicit: false
          };
          break;
        case 'user':
          // Keep user's custom settings
          break;
        case 'limited_user':
          this.contentFilter = {
            maxRating: 'PG',
            allowNSFW: false,
            blockedTags: ['explicit', 'adult'],
            allowedLanguages: this.contentFilter.allowedLanguages,
            hideExplicit: true
          };
          break;
        case 'guest':
          this.contentFilter = {
            maxRating: 'G',
            allowNSFW: false,
            blockedTags: ['explicit', 'adult', 'mature'],
            allowedLanguages: ['en'],
            hideExplicit: true
          };
          break;
      }
    },

    // Permission checking methods
    checkPermission(permission) {
      return this.hasPermission(permission);
    },

    requirePermission(permission) {
      if (!this.hasPermission(permission)) {
        this.logSecurityEvent('unauthorized_access_attempt', {
          permission,
          userId: useAuthStore().user?.id
        });
        throw new Error(`Access denied: Missing permission '${permission}'`);
      }
    },

    // Content filtering
    async updateContentFilter(newFilter) {
      const authStore = useAuthStore();
      
      // Validate filter based on role
      if (this.currentRole?.level < ROLES.USER.level) {
        throw new Error('Insufficient permissions to modify content filter');
      }
      
      this.contentFilter = { ...this.contentFilter, ...newFilter };
      
      this.logAuditEvent('content_filter_updated', {
        userId: authStore.user?.id,
        changes: newFilter
      });
      
      try {
        await api.put('/user/content-filter', this.contentFilter);
      } catch (error) {
        console.error('Failed to save content filter:', error);
      }
    },

    filterContent(contentList) {
      return contentList.filter(content => this.canViewContent(content));
    },

    // Session management
    async fetchUserSessions() {
      try {
        const response = await api.get('/auth/sessions');
        this.sessions = response.data;
        return this.sessions;
      } catch (error) {
        console.error('Error fetching sessions:', error);
        throw error;
      }
    },

    async terminateSession(sessionId) {
      try {
        await api.delete(`/auth/sessions/${sessionId}`);
        this.sessions = this.sessions.filter(s => s.id !== sessionId);
        
        this.logSecurityEvent('session_terminated', {
          sessionId,
          terminatedBy: useAuthStore().user?.id
        });
      } catch (error) {
        console.error('Error terminating session:', error);
        throw error;
      }
    },

    async terminateAllOtherSessions() {
      try {
        await api.post('/auth/sessions/terminate-others');
        this.sessions = this.sessions.filter(s => s.id === this.currentSession?.id);
        
        this.logSecurityEvent('all_sessions_terminated', {
          userId: useAuthStore().user?.id,
          keepSessionId: this.currentSession?.id
        });
      } catch (error) {
        console.error('Error terminating sessions:', error);
        throw error;
      }
    },

    // Two-factor authentication
    async enableTwoFactor(method = 'totp') {
      try {
        const response = await api.post('/auth/2fa/enable', { method });
        const { secret, qrCode, backupCodes } = response.data;
        
        this.twoFactorEnabled = true;
        this.backupCodes = backupCodes;
        
        this.logSecurityEvent('2fa_enabled', {
          userId: useAuthStore().user?.id,
          method
        });
        
        return { secret, qrCode, backupCodes };
      } catch (error) {
        console.error('Error enabling 2FA:', error);
        throw error;
      }
    },

    async disableTwoFactor(code) {
      try {
        await api.post('/auth/2fa/disable', { code });
        this.twoFactorEnabled = false;
        this.backupCodes = [];
        
        this.logSecurityEvent('2fa_disabled', {
          userId: useAuthStore().user?.id
        });
      } catch (error) {
        console.error('Error disabling 2FA:', error);
        throw error;
      }
    },

    async verifyTwoFactor(code) {
      try {
        const response = await api.post('/auth/2fa/verify', { code });
        return response.data.valid;
      } catch (error) {
        console.error('Error verifying 2FA:', error);
        throw error;
      }
    },

    // Privacy and data management
    async updatePrivacySettings(settings) {
      try {
        await api.put('/user/privacy', settings);
        this.privacySettings = { ...this.privacySettings, ...settings };
        
        this.logAuditEvent('privacy_settings_updated', {
          userId: useAuthStore().user?.id,
          changes: settings
        });
      } catch (error) {
        console.error('Error updating privacy settings:', error);
        throw error;
      }
    },

    async exportUserData() {
      try {
        const response = await api.post('/user/export-data');
        
        this.logAuditEvent('data_export_requested', {
          userId: useAuthStore().user?.id
        });
        
        return response.data;
      } catch (error) {
        console.error('Error exporting user data:', error);
        throw error;
      }
    },

    async deleteUserData() {
      try {
        await api.post('/user/delete-data');
        
        this.logAuditEvent('data_deletion_requested', {
          userId: useAuthStore().user?.id
        });
        
        // Clear local state
        this.clearSecurityState();
      } catch (error) {
        console.error('Error deleting user data:', error);
        throw error;
      }
    },

    // Audit logging
    logAuditEvent(action, details = {}) {
      const authStore = useAuthStore();
      const event = {
        id: Date.now() + Math.random(),
        timestamp: new Date(),
        action,
        userId: authStore.user?.id,
        sessionId: this.currentSession?.id,
        details,
        userAgent: navigator.userAgent,
        ipAddress: 'client-side', // Would be set by server
      };
      
      this.auditLog.unshift(event);
      
      // Keep only last 1000 events in memory
      if (this.auditLog.length > 1000) {
        this.auditLog = this.auditLog.slice(0, 1000);
      }
      
      // Send to server for persistent storage
      this.sendAuditEvent(event);
    },

    logSecurityEvent(type, details = {}) {
      const authStore = useAuthStore();
      const event = {
        id: Date.now() + Math.random(),
        timestamp: new Date(),
        type,
        severity: this.getSecurityEventSeverity(type),
        userId: authStore.user?.id,
        sessionId: this.currentSession?.id,
        details,
        userAgent: navigator.userAgent,
      };
      
      this.securityEvents.unshift(event);
      
      // Keep only last 500 security events in memory
      if (this.securityEvents.length > 500) {
        this.securityEvents = this.securityEvents.slice(0, 500);
      }
      
      // Send to server for monitoring
      this.sendSecurityEvent(event);
    },

    async sendAuditEvent(event) {
      try {
        await api.post('/audit/log', event);
      } catch (error) {
        console.warn('Failed to send audit event:', error);
      }
    },

    async sendSecurityEvent(event) {
      try {
        await api.post('/security/event', event);
      } catch (error) {
        console.warn('Failed to send security event:', error);
      }
    },

    getSecurityEventSeverity(type) {
      const severityMap = {
        'login_success': 'info',
        'login_failure': 'warning',
        'logout': 'info',
        'session_terminated': 'info',
        'all_sessions_terminated': 'warning',
        '2fa_enabled': 'info',
        '2fa_disabled': 'warning',
        'password_changed': 'info',
        'role_assigned': 'info',
        'unauthorized_access_attempt': 'high',
        'suspicious_activity': 'high',
        'account_locked': 'high',
        'data_breach_attempt': 'critical'
      };
      
      return severityMap[type] || 'info';
    },

    // API security
    checkRateLimit(endpoint) {
      const limit = this.rateLimits.get(endpoint);
      if (!limit) return true;
      
      const now = Date.now();
      const windowStart = now - limit.windowMs;
      
      // Clean old requests
      limit.requests = limit.requests.filter(time => time > windowStart);
      
      return limit.requests.length < limit.maxRequests;
    },

    recordAPIRequest(endpoint) {
      if (!this.rateLimits.has(endpoint)) {
        this.rateLimits.set(endpoint, {
          maxRequests: 100,
          windowMs: 60000, // 1 minute
          requests: []
        });
      }
      
      const limit = this.rateLimits.get(endpoint);
      limit.requests.push(Date.now());
    },

    // Utility methods
    clearSecurityState() {
      this.currentRole = null;
      this.permissions.clear();
      this.sessions = [];
      this.currentSession = null;
      this.twoFactorEnabled = false;
      this.backupCodes = [];
      this.auditLog = [];
      this.securityEvents = [];
    },

    // Initialize security state
    async initializeSecurity(user) {
      if (user) {
        await this.setUserRole(user.role);
        
        // Load user's privacy settings
        try {
          const response = await api.get('/user/privacy');
          this.privacySettings = { ...this.privacySettings, ...response.data };
        } catch (error) {
          console.warn('Failed to load privacy settings:', error);
        }
        
        // Load user's content filter
        try {
          const response = await api.get('/user/content-filter');
          this.contentFilter = { ...this.contentFilter, ...response.data };
        } catch (error) {
          console.warn('Failed to load content filter:', error);
        }
        
        // Check 2FA status
        try {
          const response = await api.get('/auth/2fa/status');
          this.twoFactorEnabled = response.data.enabled;
        } catch (error) {
          console.warn('Failed to check 2FA status:', error);
        }
      }
    },
  },
});
