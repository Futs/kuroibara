package android.util;
public final class Log {
  public static int v(String t, String m) { return 0; }
  public static int d(String t, String m) { return 0; }
  public static int i(String t, String m) { return 0; }
  public static int w(String t, String m) { return 0; }
  public static int w(String t, Throwable e) { return 0; }
  public static int e(String t, String m) { System.err.println("E/" + t + ": " + m); return 0; }
  public static int e(String t, String m, Throwable e) { System.err.println("E/" + t + ": " + m + " " + e); return 0; }
  public static int d(String t, String m, Throwable e) { return 0; }
  public static int i(String t, String m, Throwable e) { return 0; }
  public static int w(String t, String m, Throwable e) { return 0; }
}
