package android.net;
public class Uri {
  private final java.net.URI uri;
  private Uri(java.net.URI u) { uri = u; }
  public static Uri parse(String s) { return new Uri(java.net.URI.create(s)); }
  public String getHost() { return uri.getHost(); }
  public String getPath() { return uri.getPath(); }
  public String getScheme() { return uri.getScheme(); }
  public String getQuery() { return uri.getQuery(); }
  public String toString() { return uri.toString(); }
}
