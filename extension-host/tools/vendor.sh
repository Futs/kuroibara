#!/usr/bin/env bash
# Builds the two host dependencies that come from outside this repo:
#   vendor/keiyoushi-core.jar           compiled Keiyoushi core (from extensions-source, Gradle output)
#   vendor/androidx-preference-stubs.jar androidx.preference classes (from the Tachiyomi lib runtime jar)
# Usage: tools/vendor.sh [path/to/extensions-source]
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-$HOME/Apps/extensions-source}"
VENDOR="$HERE/vendor"
mkdir -p "$VENDOR"
export JAVA_HOME="${JAVA_HOME:-$(ls -d ~/.local/jdk/jdk-21* | head -1)}"

(cd "$SRC" && ./gradlew --no-daemon -q :core:compileReleaseKotlin)
CORE_CLASSES="$SRC/core/build/intermediates/built_in_kotlinc/release/compileReleaseKotlin/classes"
rm -f "$VENDOR/keiyoushi-core.jar"
(cd "$CORE_CLASSES" && "$JAVA_HOME/bin/jar" cf "$VENDOR/keiyoushi-core.jar" .)

# The Tachiyomi lib runtime jar sits in the Gradle cache after any extension build.
LIB_RT=$(find "$HOME/.gradle/caches" -name "extensions-lib-*-runtime.jar" | head -1)
TMP=$(mktemp -d)
(cd "$TMP" && "$JAVA_HOME/bin/jar" xf "$LIB_RT" androidx)
rm -f "$VENDOR/androidx-preference-stubs.jar"
(cd "$TMP" && "$JAVA_HOME/bin/jar" cf "$VENDOR/androidx-preference-stubs.jar" androidx)
rm -rf "$TMP"
echo "vendor: $(ls -la "$VENDOR" | tail -n +2 | awk '{print $5, $9}' | paste -sd' ' -)"
