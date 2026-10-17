package android.webkit;
public class CookieManager {
  private static final CookieManager INSTANCE = new CookieManager();
  public static CookieManager getInstance() { return INSTANCE; }
  public String getCookie(String url) { return null; }
  public void setCookie(String url, String cookie) { }
  public void removeAllCookies(android.webkit.ValueCallback<Boolean> cb) { }
  public void flush() { }
}
