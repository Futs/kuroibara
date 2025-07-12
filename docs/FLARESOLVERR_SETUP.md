# FlareSolverr Integration Guide

## Overview

Kuroibara supports optional integration with [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) to bypass Cloudflare protection on manga provider websites. When FlareSolverr is configured, additional Cloudflare-protected providers become available.

## What is FlareSolverr?

FlareSolverr is a proxy server that acts as a middleman between your application and Cloudflare-protected websites. It uses a real browser (Chrome/Chromium) to automatically solve Cloudflare challenges, DDoS protection, and CAPTCHAs.

## Provider Categories

### Default Providers (Always Available - Priority 1-8)
These providers work without FlareSolverr and are prioritized first:
1. **MangaDex** - Official API, excellent functionality
2. **MangaPlus** - Official Shonen Jump content
3. **MangaSee** - Large manga collection
4. **Toonily** - Webtoon provider
5. **MangaBuddy** - General manga provider
6. **MangaDNA** - Manga provider
7. **Manga18FX** - Adult content provider
8. **WebComicsApp** - Comic provider

### Cloudflare-Protected Providers (Requires FlareSolverr - Priority 100+)
These providers are only available when FlareSolverr is configured and appear after default providers:
- **ReaperScans** - Popular scanlation group
- **Manhuaga** - Manhua/Manhwa provider
- **MangaFire** - Large manga aggregator
- **MangaReaderTo** - Popular manga reader

## Setup Instructions

### Option 1: Docker (Recommended)

1. **Run FlareSolverr container:**
   ```bash
   docker run -d \
     --name flaresolverr \
     -p 8191:8191 \
     -e LOG_LEVEL=info \
     -e LOG_HTML=false \
     -e CAPTCHA_SOLVER=none \
     --restart unless-stopped \
     ghcr.io/flaresolverr/flaresolverr:latest
   ```

2. **Configure Kuroibara:**
   Add the FlareSolverr URL to your environment:
   ```bash
   # In your .env file
   FLARESOLVERR_URL=http://localhost:8191
   ```

3. **Restart Kuroibara:**
   ```bash
   docker compose restart backend
   ```

### Option 2: Docker Compose

1. **Add FlareSolverr to your docker-compose.yml:**
   ```yaml
   services:
     flaresolverr:
       image: ghcr.io/flaresolverr/flaresolverr:latest
       container_name: flaresolverr
       restart: unless-stopped
       environment:
         - LOG_LEVEL=info
         - LOG_HTML=false
         - CAPTCHA_SOLVER=none
         - TZ=UTC
       ports:
         - "8191:8191"
       networks:
         - kuroibara-network
   ```

2. **Configure environment:**
   ```bash
   # In your .env file
   FLARESOLVERR_URL=http://flaresolverr:8191
   ```

3. **Start services:**
   ```bash
   docker compose up -d
   ```

### Option 3: External FlareSolverr Instance

If you already have FlareSolverr running elsewhere:

1. **Configure Kuroibara:**
   ```bash
   # In your .env file
   FLARESOLVERR_URL=http://your-flaresolverr-host:8191
   ```

2. **Restart Kuroibara:**
   ```bash
   docker compose restart backend
   ```

## Verification

### Check FlareSolverr Status
Visit `http://localhost:8191` in your browser. You should see the FlareSolverr web interface.

### Test Provider Loading
1. **Without FlareSolverr:** Remove or comment out `FLARESOLVERR_URL` and restart
2. **With FlareSolverr:** Set `FLARESOLVERR_URL` and restart

You should see additional providers available in the Kuroibara interface when FlareSolverr is configured.

### Test Provider Functionality
Use the Kuroibara search interface to test Cloudflare-protected providers like ReaperScans or MangaFire.

## Configuration Options

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLARESOLVERR_URL` | FlareSolverr instance URL | `http://localhost:8191` |

### FlareSolverr Settings

| Setting | Description | Recommended |
|---------|-------------|-------------|
| `LOG_LEVEL` | Logging verbosity | `info` |
| `LOG_HTML` | Log HTML responses | `false` |
| `CAPTCHA_SOLVER` | CAPTCHA solving method | `none` |
| `TZ` | Timezone | `UTC` |

## Troubleshooting

### FlareSolverr Not Working

1. **Check FlareSolverr is running:**
   ```bash
   curl http://localhost:8191/
   ```

2. **Check logs:**
   ```bash
   docker logs flaresolverr
   ```

3. **Verify network connectivity:**
   - Ensure Kuroibara can reach FlareSolverr
   - Check firewall settings
   - Verify port 8191 is accessible

### Providers Still Not Working

1. **Check Kuroibara logs:**
   ```bash
   docker logs kuroibara-backend-1
   ```

2. **Verify environment variable:**
   ```bash
   docker exec kuroibara-backend-1 env | grep FLARESOLVERR
   ```

3. **Test FlareSolverr manually:**
   ```bash
   curl -X POST http://localhost:8191/v1 \
     -H "Content-Type: application/json" \
     -d '{"cmd": "request.get", "url": "https://reaperscans.com", "maxTimeout": 60000}'
   ```

### Performance Issues

- **Increase timeout:** FlareSolverr requests take longer (5-30 seconds)
- **Resource usage:** FlareSolverr uses more CPU/memory due to browser automation
- **Rate limiting:** Some sites may still rate limit even with FlareSolverr

## Security Considerations

1. **Network exposure:** Don't expose FlareSolverr port (8191) to the internet
2. **Resource limits:** Set appropriate CPU/memory limits for FlareSolverr container
3. **Updates:** Keep FlareSolverr updated for security patches

## Performance Impact

| Aspect | Without FlareSolverr | With FlareSolverr |
|--------|---------------------|-------------------|
| Response Time | 1-3 seconds | 5-30 seconds |
| CPU Usage | Low | Medium-High |
| Memory Usage | Low | Medium-High |
| Success Rate | ~11% providers | ~50%+ providers |

## Advanced Configuration

### Custom Headers
FlareSolverr automatically handles most headers, but you can customize them in provider configurations.

### Session Management
FlareSolverr automatically manages browser sessions for optimal performance.

### Proxy Chaining
You can chain FlareSolverr with other proxies if needed for additional anonymity.

## Support

- **FlareSolverr Issues:** [GitHub Issues](https://github.com/FlareSolverr/FlareSolverr/issues)
- **Kuroibara Integration:** Check application logs and verify configuration
- **Provider-Specific Issues:** May require CSS selector updates as sites change

## Conclusion

FlareSolverr integration significantly increases the number of working manga providers by bypassing Cloudflare protection. While it adds complexity and resource usage, it provides access to many popular manga sites that would otherwise be inaccessible.

The integration is designed to be optional - Kuroibara works perfectly fine without FlareSolverr, but provides enhanced functionality when it's available.
