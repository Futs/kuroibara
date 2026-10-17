package android.app;
import android.content.SharedPreferences;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map; import java.util.Set; import java.util.HashMap;
public class Application extends android.content.Context {
  private final Map<String, SharedPreferences> prefs = new ConcurrentHashMap<>();
  public java.io.File getCacheDir() { return dir("cache"); }
  public java.io.File getFilesDir() { return dir("files"); }
  private static java.io.File dir(String n) { java.io.File f = new java.io.File(System.getProperty("java.io.tmpdir"), "phase0-" + n); f.mkdirs(); return f; }
  @Override public SharedPreferences getSharedPreferences(String name, int mode) {
    return prefs.computeIfAbsent(name, n -> new MemPrefs());
  }
  static final class MemPrefs implements SharedPreferences {
    private final Map<String, Object> m = new ConcurrentHashMap<>();
    public Map<String, ?> getAll() { return new HashMap<>(m); }
    public String getString(String k, String d) { Object v = m.get(k); return v == null ? d : (String) v; }
    @SuppressWarnings("unchecked")
    public Set<String> getStringSet(String k, Set<String> d) { Object v = m.get(k); return v == null ? d : (Set<String>) v; }
    public int getInt(String k, int d) { Object v = m.get(k); return v == null ? d : (Integer) v; }
    public long getLong(String k, long d) { Object v = m.get(k); return v == null ? d : (Long) v; }
    public float getFloat(String k, float d) { Object v = m.get(k); return v == null ? d : (Float) v; }
    public boolean getBoolean(String k, boolean d) { Object v = m.get(k); return v == null ? d : (Boolean) v; }
    public boolean contains(String k) { return m.containsKey(k); }
    public Editor edit() { return new Ed(m); }
    static final class Ed implements Editor {
      private final Map<String, Object> m; private final Map<String, Object> pending = new HashMap<>(); private boolean clear;
      Ed(Map<String, Object> m) { this.m = m; }
      public Editor putString(String k, String v) { pending.put(k, v); return this; }
      public Editor putStringSet(String k, Set<String> v) { pending.put(k, v); return this; }
      public Editor putInt(String k, int v) { pending.put(k, v); return this; }
      public Editor putLong(String k, long v) { pending.put(k, v); return this; }
      public Editor putFloat(String k, float v) { pending.put(k, v); return this; }
      public Editor putBoolean(String k, boolean v) { pending.put(k, v); return this; }
      public Editor remove(String k) { pending.put(k, null); return this; }
      public Editor clear() { clear = true; return this; }
      public boolean commit() { if (clear) m.clear(); pending.forEach((k, v) -> { if (v == null) m.remove(k); else m.put(k, v); }); return true; }
      public void apply() { commit(); }
    }
  }
}
