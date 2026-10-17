#!/usr/bin/env python3
"""Fetch the upstream Keiyoushi catalog and write data/upstream/index.json for display.

Source: repo.json -> index_v2 (index.pb, gzip protobuf). The protobuf schema comes from
extensions-source/.github/scripts/index_pb2.py, so this needs the `protobuf` Python package.

What it records per extension: package, our module key (lang/name), version code and name,
content warning, JAR and APK URLs, and sources. repo.json's signingKeyFingerprint is kept as
information only: it is the APK signing key, not a signature on the index, and our installs
come from our own build (D2/(b)), so nothing is verified against it here.

Usage: fetch-upstream.py [--src EXT_SOURCE] [--out DIR]
"""
import argparse, gzip, io, json, os, sys, urllib.request
from datetime import datetime, timezone

REPO_JSON = "https://raw.githubusercontent.com/keiyoushi/extensions/repo/repo.json"
HERE = os.path.dirname(os.path.abspath(__file__))


def get(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def module_key(package):
    # eu.kanade.tachiyomi.extension.<lang>.<name> -> <lang>/<name>; matches our build's module dirs.
    parts = package.split(".")
    if len(parts) >= 6 and parts[:4] == ["eu", "kanade", "tachiyomi", "extension"]:
        return f"{parts[4]}/{parts[5]}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.expanduser("~/Apps/extensions-source"))
    ap.add_argument("--out", default=os.path.join(HERE, "..", "data", "upstream"))
    args = ap.parse_args()

    sys.path.insert(0, os.path.join(args.src, ".github", "scripts"))
    import index_pb2  # noqa: E402  (generated schema from upstream)

    repo = json.loads(get(REPO_JSON))
    index_url = repo["index_v2"]
    if not index_url.startswith("http"):
        index_url = "https://raw.githubusercontent.com/keiyoushi/extensions/repo/" + index_url
    raw = get(index_url)
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    idx = index_pb2.Index()
    idx.ParseFromString(raw)

    exts = []
    for e in idx.extensionList.extensions:
        exts.append({
            "package": e.packageName,
            "module": module_key(e.packageName),
            "name": e.name,
            "version_code": e.versionCode,
            "version_name": e.versionName,
            "content_warning": index_pb2.ContentWarning.Name(e.contentWarning),
            "jar_url": e.resources.jarUrl or None,
            "apk_url": e.resources.apkUrl or None,
            "sources": [{"id": s.id, "name": s.name, "language": s.language, "home_url": s.homeUrl} for s in e.sources],
        })

    os.makedirs(args.out, exist_ok=True)
    out = {
        "name": idx.name,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "index_url": index_url,
        "signing_key_fingerprint": repo.get("meta", {}).get("signingKeyFingerprint"),
        "extensions": exts,
    }
    path = os.path.join(args.out, "index.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"upstream: {len(exts)} extensions -> {path}")


if __name__ == "__main__":
    main()
