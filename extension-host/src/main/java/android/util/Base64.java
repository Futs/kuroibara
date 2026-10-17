package android.util;
public final class Base64 {
  public static final int DEFAULT = 0, NO_PADDING = 1, NO_WRAP = 2, CRLF = 4, URL_SAFE = 8;
  private static java.util.Base64.Encoder enc(int f) {
    java.util.Base64.Encoder e = (f & URL_SAFE) != 0 ? java.util.Base64.getUrlEncoder() : java.util.Base64.getEncoder();
    if ((f & NO_PADDING) != 0) e = e.withoutPadding();
    return e;
  }
  public static byte[] encode(byte[] in, int f) { return enc(f).encode(in); }
  public static String encodeToString(byte[] in, int f) { return new String(encode(in, f), java.nio.charset.StandardCharsets.US_ASCII); }
  public static byte[] decode(String s, int f) {
    return (f & URL_SAFE) != 0 ? java.util.Base64.getUrlDecoder().decode(s) : java.util.Base64.getMimeDecoder().decode(s);
  }
  public static byte[] decode(byte[] s, int f) { return decode(new String(s, java.nio.charset.StandardCharsets.US_ASCII), f); }
}
