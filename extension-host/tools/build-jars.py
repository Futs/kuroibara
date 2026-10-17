#!/usr/bin/env python3
"""Build host-loadable extension JARs from extensions-source, plus an index.

For each extension module:
  1. Gradle compiles it (and its theme/lib deps) to classes, unobfuscated.
  2. Its own classes, theme classes and lib classes go into <module>.jar.
     Host-provided packages (Mihon source API, network, core utils, androidx) are left out.
  3. Assets (theme i18n bundles) are copied under assets/.
  4. Sources (name, lang, id, baseUrl) are read from the KSP-generated Generated.kt.

Incremental: a module is rebuilt only when its source tree (own + theme + lib deps) hash changes,
or with --all. The index pins the extensions-source commit it was built from.

Usage:
  build-jars.py [--all] [--out DIR] [--src EXT_SOURCE] [module ...]
  module = path under src/, e.g. en/mangakatana. Default list: tools/day1.txt.
"""
import argparse, hashlib, json, os, re, subprocess, sys, zipfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
JAVA_HOME = os.path.expanduser(os.environ.get("JAVA_HOME", ""))

# Host-provided: never bundled. Keiyoushi core and the Mihon source API live in the host runtime.
HOST_PREFIXES = ("eu/kanade/tachiyomi/source/", "eu/kanade/tachiyomi/network/", "eu/kanade/tachiyomi/AppInfo",
                 "androidx/", "android/", "keiyoushi/network/", "keiyoushi/utils/", "keiyoushi/annotation/",
                 "keiyoushi/zip/", "keiyoushi/webview/", "keiyoushi/source/KeiSource", "keiyoushi/source/Mirror",
                 "keiyoushi/source/Custom", "keiyoushi/source/UrlActivity")
KEEP_OVERRIDE = ("keiyoushi/source/Generated",)  # bundled even though keiyoushi/source/ is partly host-provided


def module_dir(src, mod):
    return os.path.join(src, "src", mod)


def read_build(path):
    text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    return {
        "version_code": (re.search(r"versionCode\s*=\s*(\d+)", text) or [None, None])[1],
        "theme": (re.search(r'theme\s*=\s*"([^"]+)"', text) or [None, None])[1],
        "lib_deps": re.findall(r'project\(":lib:([^"]+)"\)', text),
    }


def class_dirs(src, project_dir_rel):
    """Kotlin and Java compile outputs for a Gradle project under src/."""
    base = os.path.join(src, project_dir_rel, "build", "intermediates")
    out = []
    for p in (os.path.join(base, "built_in_kotlinc", "release", "compileReleaseKotlin", "classes"),
              os.path.join(base, "javac", "release", "compileReleaseJavaWithJavac", "classes")):
        if os.path.isdir(p):
            out.append(p)
    assets = os.path.join(src, project_dir_rel, "assets")
    return out, (assets if os.path.isdir(assets) else None)


def collect_deps(src, mod):
    """Own classes plus theme and lib deps, transitively. Returns (class_dirs, asset_dirs, input_dirs)."""
    classes, assets, inputs = [], [], []
    seen = set()
    own_rel = os.path.join("src", mod)
    queue = [own_rel]
    while queue:
        rel = queue.pop(0)
        if rel in seen:
            continue
        seen.add(rel)
        c, a = class_dirs(src, rel)
        classes += c
        if a: assets.append(a)
        inputs.append(os.path.join(src, rel))
        info = read_build(os.path.join(src, rel, "build.gradle.kts"))
        if rel == own_rel and info["theme"]:
            queue.append(os.path.join("lib-multisrc", info["theme"]))
        for lib in info["lib_deps"]:
            queue.append(os.path.join("lib", lib))
        if rel.startswith("lib-multisrc"):
            for lib in info["lib_deps"]:
                queue.append(os.path.join("lib", lib))
    return classes, assets, inputs


def tree_hash(paths):
    h = hashlib.sha256()
    for root_path in sorted(paths):
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in ("build", ".gradle")]
            for f in sorted(files):
                fp = os.path.join(root, f)
                h.update(os.path.relpath(fp, root_path).encode())
                with open(fp, "rb") as fh:
                    h.update(fh.read())
    return h.hexdigest()


def parse_sources(generated_path):
    """Read name/lang/id/baseUrl for each source in a KSP Generated.kt, in declaration order.

    Two shapes occur: named arguments inside listOf(...) (multi-source), and one
    `override val` block per source. A baseUrl computed at runtime (mirror prefs) is recorded as "dynamic".
    """
    if not os.path.exists(generated_path):
        return []
    t = open(generated_path, encoding="utf-8").read()
    named = re.findall(r'name = "([^"]*)",\s*lang = "([^"]*)",\s*id = ([0-9_]+)L,\s*baseUrl = "([^"]*)"', t)
    if named:
        return [{"name": n, "lang": l, "id": int(i.replace("_", "")), "baseUrl": u} for n, l, i, u in named]
    names = re.findall(r'override val name(?:: \w+)?\s*\n?\s*get\(\) = "([^"]*)"', t)
    langs = re.findall(r'override val lang(?:: \w+)?\s*\n?\s*get\(\) = "([^"]*)"', t)
    ids = re.findall(r"override val id(?:: \w+)?\s*\n?\s*get\(\) = ([0-9_]+)L", t)
    urls = re.findall(r'override val baseUrl(?:: \w+)?\s*\n?\s*get\(\) = "([^"]*)"', t)
    out = []
    for i, (n, l, d) in enumerate(zip(names, langs, ids)):
        out.append({"name": n, "lang": l, "id": int(d.replace("_", "")),
                    "baseUrl": urls[i] if i < len(urls) else "dynamic"})
    return out


def write_jar(out_jar, classes, assets):
    seen = set()
    with zipfile.ZipFile(out_jar, "w", zipfile.ZIP_DEFLATED) as z:
        for d in classes:
            for root, _, files in os.walk(d):
                for f in sorted(files):
                    fp = os.path.join(root, f)
                    name = os.path.relpath(fp, d).replace(os.sep, "/")
                    if name in seen or name.endswith(".kotlin_module"):
                        continue
                    if name.startswith(HOST_PREFIXES) and not name.startswith(KEEP_OVERRIDE):
                        continue
                    seen.add(name)
                    z.write(fp, name)
        for d in assets:
            for root, _, files in os.walk(d):
                for f in sorted(files):
                    fp = os.path.join(root, f)
                    name = "assets/" + os.path.relpath(fp, d).replace(os.sep, "/")
                    if name not in seen:
                        seen.add(name)
                        z.write(fp, name)


def gradle_compile(src, mods):
    tasks = []
    for m in mods:
        path = ":src:" + m.replace("/", ":")
        tasks += [path + ":compileReleaseKotlin", path + ":compileReleaseJavaWithJavac"]
    env = dict(os.environ)
    if JAVA_HOME:
        env["JAVA_HOME"] = JAVA_HOME
    cmd = ["./gradlew", "--no-daemon", "--continue", "-q"] + tasks
    r = subprocess.run(cmd, cwd=src, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        errors = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith("e: ") or "What went wrong" in l]
        print("gradle reported errors:", *errors[:10], sep="\n  ", file=sys.stderr)
    return r.returncode


def migrate_entry(entry):
    """Convert the flat pre-history index shape into the versions list."""
    if "versions" in entry or "jar" not in entry:
        return
    entry["versions"] = [{k: entry[k] for k in ("version_code", "hash", "jar", "sources", "built_at", "built_from") if k in entry}]
    entry["theme"] = entry.get("theme")
    for k in ("version_code", "hash", "jar", "sources", "built_at", "built_from"):
        entry.pop(k, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modules", nargs="*")
    ap.add_argument("--all", action="store_true", help="rebuild even if unchanged")
    ap.add_argument("--src", default=os.path.expanduser("~/Apps/extensions-source"))
    ap.add_argument("--out", default=os.path.join(HERE, "..", "data", "jars"))
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    mods = args.modules or [l.strip() for l in open(os.path.join(HERE, "day1.txt")) if l.strip()]

    index_path = os.path.join(out, "index.json")
    index = json.load(open(index_path)) if os.path.exists(index_path) else {"modules": {}}
    for m, entry in index["modules"].items():
        migrate_entry(entry)
    commit = subprocess.run(["git", "-C", src, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    todo = []
    for m in mods:
        classes, assets, inputs = collect_deps(src, m)
        h = tree_hash(inputs)
        versions = index["modules"].get(m, {}).get("versions", [])
        latest = versions[-1] if versions else None
        jar_ok = latest is not None and os.path.exists(os.path.join(out, latest["jar"]))
        if args.all or not jar_ok or latest["hash"] != h:
            todo.append((m, h))
        else:
            print(f"unchanged: {m} (version_code {latest['version_code']})")

    if todo:
        print(f"building {len(todo)} module(s)...")
        gradle_compile(src, [m for m, _ in todo])

    for m, h in todo:
        classes, assets, _ = collect_deps(src, m)
        if not classes:
            print(f"FAILED (no classes): {m}")
            continue
        build = read_build(os.path.join(src, "src", m, "build.gradle.kts"))
        vc = int(build["version_code"]) if build["version_code"] else None
        jar_name = f"{m.replace('/', '_')}@{vc}-{h[:8]}.jar"
        write_jar(os.path.join(out, jar_name), classes, assets)
        sources = parse_sources(os.path.join(src, "src", m, "build", "generated", "ksp", "release", "kotlin", "keiyoushi", "source", "Generated.kt"))
        record = {
            "version_code": vc,
            "hash": h,
            "jar": jar_name,
            "sources": sources,
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "built_from": commit,
        }
        entry = index["modules"].setdefault(m, {"versions": []})
        entry["theme"] = build["theme"]
        # One record per (version_code, source hash). Rebuilding the same source replaces its record.
        entry["versions"] = [v for v in entry["versions"] if (v["version_code"], v["hash"]) != (vc, h)] + [record]
        print(f"built: {m} version_code={vc} -> {jar_name} ({len(sources)} source(s))")

    index["extensions_source_commit"] = commit
    index["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    json.dump(index, open(index_path, "w"), indent=2)
    print(f"index: {index_path}")


if __name__ == "__main__":
    main()
