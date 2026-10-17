package android.webkit;

import java.net.URI;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

// Process-wide cookie store, keyed by host. Extensions read and write it through the Android API;
// the Cloudflare interceptor writes the clearance cookies a solver returns. Not persisted: a restart clears it.
public class CookieManager {
    private static final CookieManager INSTANCE = new CookieManager();

    private final Map<String, Map<String, String>> byHost = new ConcurrentHashMap<>();
    private volatile boolean acceptCookies = true;

    public static CookieManager getInstance() {
        return INSTANCE;
    }

    public void setAcceptCookie(boolean accept) {
        this.acceptCookies = accept;
    }

    public boolean acceptCookie() {
        return acceptCookies;
    }

    // "name=value; Path=/; Secure" -> stores name=value for the URL's host.
    public void setCookie(String url, String cookie) {
        if (!acceptCookies || cookie == null) return;
        String host = hostOf(url);
        if (host == null) return;
        String pair = cookie.split(";", 2)[0].trim();
        int eq = pair.indexOf('=');
        if (eq <= 0) return;
        byHost.computeIfAbsent(host, h -> new ConcurrentHashMap<>())
                .put(pair.substring(0, eq).trim(), pair.substring(eq + 1).trim());
    }

    // Cookies for the URL's host and its parent domains, as a Cookie header value. Null if there are none.
    public String getCookie(String url) {
        String host = hostOf(url);
        if (host == null) return null;
        StringBuilder out = new StringBuilder();
        for (Map.Entry<String, Map<String, String>> e : byHost.entrySet()) {
            if (!host.equals(e.getKey()) && !host.endsWith("." + e.getKey())) continue;
            for (Map.Entry<String, String> c : e.getValue().entrySet()) {
                if (out.length() > 0) out.append("; ");
                out.append(c.getKey()).append('=').append(c.getValue());
            }
        }
        return out.length() == 0 ? null : out.toString();
    }

    public boolean hasCookies(String url) {
        return getCookie(url) != null;
    }

    public void removeAllCookies(ValueCallback<Boolean> callback) {
        byHost.clear();
        if (callback != null) callback.onReceiveValue(true);
    }

    public void removeSessionCookies(ValueCallback<Boolean> callback) {
        removeAllCookies(callback);
    }

    public void flush() {
    }

    private static String hostOf(String url) {
        try {
            return url == null ? null : URI.create(url).getHost();
        } catch (IllegalArgumentException e) {
            return null;
        }
    }
}
