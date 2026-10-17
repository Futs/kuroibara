package android.os;
public final class SystemClock {
  public static long elapsedRealtime() { return System.nanoTime() / 1_000_000L; }
  public static long uptimeMillis() { return elapsedRealtime(); }
  public static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }
}
