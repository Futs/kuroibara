# Authentication Security

This document explains the authentication security features in Kuroibara and how they protect user sessions.

## Token Validation on New Tabs

### Overview

By default, Kuroibara now validates authentication tokens when opening new browser tabs or windows. This ensures that expired or invalid sessions cannot be used to access protected content.

### How It Works

1. **Route Guard Validation**: When navigating to a protected route in a new tab, the system checks if token validation is enabled
2. **Server Verification**: If enabled, the token is validated with the server using a quick API call (`/api/v1/users/me`)
3. **Caching**: Valid tokens are cached for 5 minutes to avoid excessive server requests
4. **Automatic Cleanup**: Invalid or expired tokens are automatically removed from storage

### Security Benefits

- **Session Expiry Enforcement**: Prevents access with expired tokens
- **Token Blacklist Respect**: Honors server-side token blacklisting (e.g., after logout)
- **Concurrent Session Control**: Ensures proper session management across multiple tabs
- **Reduced Attack Surface**: Limits the window for token-based attacks

### User Experience

- **Fast Access**: Cached validations provide quick access for recently validated tokens
- **Seamless UX**: Valid sessions continue working normally
- **Clear Feedback**: Invalid sessions redirect to login with clear messaging

## Configuration

### Settings Location

Navigate to **Settings > Security > Authentication Security** to configure token validation.

### Options

- **Validate Token on New Tab**: 
  - **Enabled (Recommended)**: New tabs validate tokens with the server
  - **Disabled (Legacy)**: New tabs trust existing tokens without validation

### Default Behavior

- New installations: **Enabled** (secure by default)
- Existing installations: **Enabled** (upgraded for security)
- Users can disable if needed for convenience

## Technical Implementation

### Frontend Components

1. **Auth Service** (`/src/services/authService.js`):
   - Token validation with caching
   - Storage management
   - Cache invalidation

2. **Route Guard** (`/src/router/index.js`):
   - Pre-route authentication checks
   - Configurable validation behavior
   - Error handling and redirects

3. **Settings Store** (`/src/stores/settings.js`):
   - Configuration persistence
   - User preference management

### Backend Security

1. **JWT Validation** (`/backend/app/core/deps.py`):
   - Token expiry checking
   - Signature verification
   - Blacklist validation

2. **Token Blacklisting** (`/backend/app/api/api_v1/endpoints/auth.py`):
   - Logout token invalidation
   - Redis-based blacklist storage
   - TTL-based cleanup

## Migration Guide

### For Existing Users

If you prefer the previous behavior (no validation on new tabs):

1. Go to **Settings > Security**
2. Toggle off **"Validate Token on New Tab"**
3. Save settings

### For Developers

The authentication service provides these methods:

```javascript
import { authService } from '@/services/authService.js';

// Check if token exists (quick)
const hasToken = authService.hasToken();

// Validate with server (cached)
const isValid = await authService.validateToken();

// Get cached validation status
const cached = authService.getCachedValidation();

// Clear validation cache
authService.invalidateCache();
```

## Security Recommendations

1. **Keep Validation Enabled**: For maximum security, keep token validation enabled
2. **Regular Logout**: Log out when finished, especially on shared computers
3. **Monitor Sessions**: Check active sessions in the security dashboard
4. **Strong Passwords**: Use strong, unique passwords for your account

## Troubleshooting

### Frequent Re-authentication

If you're being asked to log in frequently:

1. Check if your session timeout is too short
2. Verify your internet connection is stable
3. Consider disabling token validation if convenience is preferred over security

### Performance Impact

Token validation adds a small delay when opening new tabs:

- **First validation**: ~100-500ms (server request)
- **Cached validation**: <10ms (local cache)
- **Cache duration**: 5 minutes

### Browser Compatibility

This feature works with all modern browsers that support:
- localStorage/sessionStorage
- Async/await
- Fetch API

## Future Enhancements

Planned security improvements:

1. **Device Fingerprinting**: Track and validate device characteristics
2. **Geolocation Checks**: Alert on logins from unusual locations
3. **Session Analytics**: Detailed session usage statistics
4. **Two-Factor Authentication**: Additional security layer
5. **Biometric Authentication**: Browser-based biometric support
