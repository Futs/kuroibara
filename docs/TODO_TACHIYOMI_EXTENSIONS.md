# TODO: feat/tachiyomi-extensions

Goal: Mihon-style source handling in Kuroibara.

1. Sources supply search **and** metadata, as in Mihon. Users install extensions from the catalog, and global search shows which installed extensions have a match.
2. Run Tachiyomi/Keiyoushi extensions instead of hand-written Python providers.
3. Metadata comes from the source. MangaUpdates is an optional comparison, field by field, as AudioSilo does with its community metadata.

UI work is on a separate branch: `feat/ui-react-shadcn` (see the UI section below). This branch is backend only.

**Base:** `origin/chore/dependency-updates` (`0796388`), the newest commit on any remote branch. It sits on top of `dev` and adds one dependency bump (`backend/requirements.txt`, `frontend/app/package-lock.json`). Drop that commit if you don't want it here. Local `main` is fast-forwarded to `origin/main` (`cd39318`).

## Decisions

Recommended defaults. Confirm before Phase 2.

- [ ] **D1 Metadata source.** Selecting a title adds it to the library using the provider's metadata. That is the base record. MangaUpdates is applied only when the user asks (see Phase 2b).
- [ ] **D2 Extension runtime.** A JVM process that loads the extension JARs and exposes HTTP to the Python backend. Runs as its own container in the compose stack. Why a separate process is needed: see "Why a JVM process" below.
- [ ] **D3 UI stack.** React + shadcn/ui + Tailwind v4, matching AudioSilo's admin console. Lives on `feat/ui-react-shadcn`, not this branch. Kuroibara's colour palette stays.
- [ ] **D4 Rollout.** Strangler pattern. Additive migrations only. New code paths sit beside the old providers behind a flag. Old providers are removed only after parity.
- [ ] **D6 Network-dependent sources stay in the project.** A source that fails from one network may work from another, and other users in other countries may reach it. Never exclude a source because it failed here. Each install carries a health record instead: last result, error class (blocked, timeout, 401, shim gap, WebView needed) and when it was checked. The user decides what to keep. Enable, disable and uninstall are separate actions. Disabled sources stay installed, skip search, and keep their library links.
- [ ] **D5 No built-in sources.** The new path ships with no extensions installed. The user imports Keiyoushi-compatible extensions from a catalog URL or local JAR files and installs or removes them. Old providers stay in place until cutover (D4).

## Why a JVM process (D2)

Keiyoushi extensions are compiled JVM bytecode. The Kuroibara backend is Python, so something has to run that bytecode. Options:

- In-process via JPype or Py4J. Works, but a bad extension can crash or exhaust memory in the API server, and the JVM and Python GCs compete.
- A separate JVM process. Isolates crashes and memory, and lets the backend stay in Python.
- Rewrite the backend in Kotlin. Large change; not justified by this feature.
- Reimplement extensions in Python. Not viable at roughly 1,400 extensions.

A "container" is only packaging. The required part is a separate process. It can run as a sidecar container or as a second process in the Kuroibara image.

## Constraints (to avoid breaking existing features)

- [ ] Do not edit existing provider classes except where a shared helper must change. Record each such edit here.
- [ ] Existing tables and API routes stay unchanged. New data goes in new tables and new `/api/v2/...` routes.
- [ ] Each phase ends with `pytest` green and the frontend building. Note any test that was already failing before this branch.
- [ ] The local `refactor` branch is not used. Its remote was deleted, and it is an ancestor of `dev` (`dev` has 16 commits it lacks), so nothing in it is missing from `dev`.

## Phase 0: Feasibility spike (go / no-go)

Time-box this. Stop and report if it fails.

**Result (2026-10-17): GO.** Search, details, chapters and pages all return real data for 3 extensions across 2 themes.

| Extension | Theme | Search | Details | Chapters | Pages |
| --- | --- | --- | --- | --- | --- |
| MangaKatana | standalone | 5 | One Piece, Oda Eiichiro | 1202 | 52 |
| Toonily | Madara | 25 | Baby Prisoner of the Winter Castle | 84 | 16 |
| MangaFire (en) | standalone, multi-source | 50 | One Plus One | 3 | 34 |

- Runtime: Mihon `source-api` plus trimmed network code (`NetworkHelper`, `OkHttpExtensions`, `Requests`, interceptors) plus Android shims. Compiled by Gradle with JDK 21. The Madara theme and `lib/i18n` are compiled from this repo.
- Shortcuts that matter: `NetworkHelper` has no Cloudflare WebView (a pass-through placeholder). No Bitmap or image decode. Preferences UI is not rendered. None of these were exercised.
- Harness, runtime and run notes: `/home/futs/Apps/phase0-spike/` (see `RUN.md`). Kept outside `/tmp`.
- Next: Phase 0b, the smoke test across the 27 day-1 extensions. Expect more shim gaps and Cloudflare failures there.

**Status (2026-10-17):** step 1 done. Built with JDK 21 (Temurin 21.0.12, `~/.local/jdk`) and Android SDK platform 37.0 (`~/Android/Sdk`). Kotlin here caps at JVM 26, so JDK 27 fails. Unsigned JARs in `/tmp/phase0/jars/`: `mangakatana.jar`, `toonily.jar`, `mangafire.jar`. JARs bundle library code under obfuscated names (for example `eu/kanade/tachiyomi/a/a/a`, `keiyoushi/b`), so a host can't just swap in its own lib. Check this before the loader work.

**Status, step 2 (2026-10-17): blocked on the host runtime, not on shims.**

- The `extensions-lib` artifact (`com.github.keiyoushi:extensions-lib`) is compile-time stubs. Every method in `HttpSource` throws `Stub!`. Its runtime jar has stubs too. The real `HttpSource`, `NetworkHelper` and models come from the host app at runtime.
- Extensions import about 306 distinct host classes. Most common: source models, `FilterList`, `GET`/`POST`, `HttpException`, `ConfigurableSource`. Multisrc themes (`lib-multisrc/madara`, `mangathemesia`, and others) are source in this repo and need compiling too.
- Closest real runtime in the workspace: Mihon's `source-api` (19 Kotlin files) plus its `core/common` network code. Both are coupled to Android and Mihon core (`Context`, `PreferenceScreen`, Compose `@Stable`, `rx.Observable`, `tachiyomi.core.common`).
- Host harness exists at `/tmp/phase0/host/` (`Host.java`, Android shims, `build.sh`, `classpath.py`). Loads `keiyoushi.source.Generated` (KSP output), registers `Application` in Injekt, calls the suspend functions through reflection. Works up to `HttpSource` init, then stops at the stub.
- Next, one of: (a) compile Mihon `source-api` plus a trimmed `core/common` network subset with `kotlin-compiler-embeddable` as the host runtime; (b) write our own `HttpSource`-compatible runtime in Java/Kotlin covering the ~306-symbol surface. (a) is closer to real behaviour. (b) is cleaner but larger.
- Obfuscation finding from step 1 still applies. Extension JARs from `outputs/jar` bundle renamed library classes. The harness uses the unobfuscated `compileReleaseKotlin/classes` directory instead.

- [x] Get 3 extension JARs. The project already builds them: `gradle/build-logic/.../ExtensionPlugin.kt` creates `outputs/jar/<variant>/*.jar` via `CreateExtensionJarTask` (R8-shrinks the classes, excludes anything the host provides). CI uploads these as artifacts. Pick one per theme family (for example madara, mangareader, and one custom).
- [ ] Shim the Android classes the JARs reference. Inventory below.
- [ ] WebView: stub it, and mark Cloudflare-protected extensions as "needs capture" for now.
- [ ] For each extension call `search`, `details`, `chapterList`, `pageList`. Record which calls work.
- [ ] **Go** if at least 3 extensions across 2 themes return search, details, chapters and pages. **No-go** otherwise. On no-go, stop and report to the user with the failure list.

### Phase 0b: Measure compatibility across all extensions

Run before promising "all extensions on day 1".

- [ ] Build a smoke-test harness that loads each extension JAR and runs `search` (fixed query), `details`, `chapterList` and `pageList` on one known title.
- [ ] Run it across all ~1,434 packages. Record per extension: loads, search, details, chapters, pages, and the first error.
- [ ] Bucket the results: works, broken by shim gap (which class), needs WebView, site down or changed. The "shim gap" bucket shows which shims to build next.
- [ ] Publish the pass rate and the list. That becomes the honest day-1 claim.
- [ ] Results go stale. Re-run on a schedule.

**Result (2026-10-17, query "one", FlareSolverr on):** 27 of 27 load. 21 of 27 pass search, details, chapters and pages with real data.

| Outcome | Extensions |
| --- | --- |
| Full pass | 1Manga.co, Anisa Scans, Asura Scans, Drake Scans, Hive Scans, MangaGeko, MangaKatana, MangaOnline.fun, Vortex Scans, Weeb Central, Lunar Manga, Manga18.me, Manga18fx, MangaDNA, Eris Scans, Grim Scans, MadaraDex, MangaFire, Mangafreak, Toonily, TopManhua.fan |
| Pages need WebView (shim gap, Phase 4) | AllManga, HDoujin (search, details and chapters pass) |
| Unverified from our network | Mangakakalot, Manhuarm (MangaBox theme; 403 without solver, timeout with it). Kept per D6. "Unverified", not "broken". |
| HTTP 401 | Hiperdex (may need login) |
| Inconclusive | MangaDex (en): test title returned 0 chapters, so pages were skipped. Retest with another title. |

Notes:

- No Cloudflare challenge (`cf-mitigated`) was seen during the run, so the solver path was not exercised for these sources. The live FlareSolverr check is still open.
- Fixed in this round: `AppInfo` shim, Main dispatcher for `Dispatchers.Main`, English source picked from multi-source extensions.
- Raw results: `phase0-spike/smoke/results_final.jsonl`. Earlier runs are kept beside it.

### Day-1 target set (from the user's installed extensions)

27 installed on the user's mobile. All 27 resolve to a source directory in `extensions-source`, with two names that need confirming. Source dirs are relative to `/home/futs/Apps/extensions-source`.

| # | Installed name | Source dir | Notes |
| --- | --- | --- | --- |
| 1 | 1manga | `src/en/onemangaco` | Listed as "1Manga.co" in the source |
| 2 | allmanga | `src/en/allanime` | WebView + Cloudflare references |
| 3 | Anisa Scans | `src/en/anisascans` | |
| 4 | Asusra Scans | `src/en/asurascans` | Listed as "Asura Scans" in the source. Confirm this is the same site. |
| 5 | Drake Scans | `src/en/drakescans` | |
| 6 | Hive Scans | `src/en/hivescans` | |
| 7 | MangaGeko | `src/en/mangarawclub` | Source name differs from the installed name |
| 8 | MangaKakalot | `src/en/mangakakalot` | |
| 9 | MangaKatana | `src/en/mangakatana` | |
| 10 | MangaOnline.fun | `src/en/mangaonlinefun` | |
| 11 | Vortex Scans | `src/en/vortexscans` | |
| 12 | Weeb Central | `src/en/weebcentral` | |
| 13 | HDoujin | `src/all/hdoujin` | NSFW |
| 14 | Lunar Manga | `src/all/lunaranime` | |
| 15 | Manga18.me | `src/all/manga18me` | NSFW |
| 16 | Manga18fx | `src/all/manga18fx` | NSFW |
| 17 | MangaDNA | `src/all/mangadna` | |
| 18 | Eris Scans | `src/en/erisscans` | |
| 19 | Grim Scans | `src/en/grimscans` | |
| 20 | Hiperdex | `src/en/hiperdex` | |
| 21 | MadaraDex | `src/en/madaradex` | |
| 22 | MangaDex | `src/all/mangadex` | |
| 23 | MangaFire | `src/all/mangafire` | WebView + Cloudflare references |
| 24 | MangaFreak | `src/en/mangafreak` | |
| 25 | Manhuarm | `src/all/manhuarm` | |
| 26 | Toonily | `src/en/toonily` | |
| 27 | TopManhua | `src/en/topmanhuafan` or `src/en/topmanhuanet` | Two source dirs match. Confirm which one is installed. |

- [ ] Confirm the three ambiguous rows (1, 4, 27) with the user before the spike.
- [ ] Phase 0 spike: pick at least one from the set with no WebView (for example MangaKatana or Toonily) and one with WebView (MangaFire) to test the go / no-go criteria.
- [ ] Phase 0b: run the smoke test over these 27 first. Their result is the day-1 claim. The rest of the ~1,434 are tested after.
- [ ] Two in the set reference WebView and Cloudflare: allmanga and MangaFire. Expect them to need the Phase 4 capture flow.

### Kuroibara providers outside the day-1 set

Source: `kuroibara_providers.csv` (`/home/futs/Apps/kuroibara_providers.csv`). Rows already in the day-1 set are excluded. Integration status is Kuroibara's current status, not the status of a Keiyoushi extension. Most of these need a Keiyoushi extension to be checked for a match first. Nothing here is confirmed to exist in `extensions-source`.

- [ ] Map each row to a Keiyoushi extension (or mark as no extension) before Phase 0b. Matching is by name only so far.
- [ ] Drop `Example Provider`. It is a template row.
- [ ] `HiperDex` is a Kuroibara provider class (`backend/app/core/providers/hiperdex.py`) with no CSV row. It is in the day-1 set as `Hiperdex`.

| Provider | NSFW | Kuroibara status |
| --- | --- | --- |
| TAADD | yes | not integrated |
| MangaHub | yes | not integrated |
| MangaForest | yes | not integrated |
| TrueManga | yes | not integrated |
| MangaBuddy | no | Enhanced Integration (Disabled) |
| MangaKakalotFun | yes | not integrated |
| Tsumino | yes | Basic Integration |
| MangaHere | yes | not integrated |
| ReadComicsOnline.li (kisscomic) | yes | not integrated |
| ReadAllComics | yes | Basic Integration |
| MangaFoxFun | yes | not integrated |
| MangaHereFun | no | not integrated |
| HentaiNexus | yes | Basic Integration |
| MangaReader.to | yes | not integrated |
| AllPornComics | yes | not integrated |
| Kissmanga | yes | not integrated |
| MangaPlaza | yes | not integrated |
| MangaTown | yes | Basic Integration |
| NovelCool | no | not integrated |
| MangaGG | yes | not integrated |
| ReadComicsOnline.us | no | not integrated |
| ZinManga | yes | not integrated |
| WuxiaWorld | no | not integrated |
| S2Manga | yes | not integrated |
| MangaReaderSite | yes | not integrated |
| MangaOnlineTeam | yes | not integrated |
| WebComicsApp | yes | Enhanced Integration (Disabled) |
| MangaRockTeam | yes | Basic Integration |
| MangaPlanet | yes | not integrated |
| MangaRead | yes | Basic Integration |
| Manhuascan.us/Manga18.us | yes | not integrated |
| MangaFoxFull | yes | not integrated |
| MangaEffect | no | not integrated |
| MangaOwl.io | yes | not integrated |
| ComicK | yes | not integrated |
| Manga18.club | yes | not integrated |
| ManhwasMen | yes | not integrated |
| ManhwaHub | yes | Basic Integration |
| NitroManga | no | not integrated |
| ManhuaFast | no | Basic Integration |
| Tapas | no | not integrated |
| MangaforFree | yes | not integrated |
| MangaPill | yes | Basic Integration |
| MangaSail | no | Basic Integration |
| Toomics | yes | not integrated |
| MangaRead.co | yes | not integrated |
| Danke furs Lesen | yes | not integrated |
| Comikey | no | not integrated |
| ManhuaGold | no | not integrated |
| ToonilyMe | yes | not integrated |
| ResetsScans | no | not integrated |
| OmegaScans | yes | Basic Integration |
| Milftoon Comics | yes | not integrated |
| MangaPlus | no | Fully Integrated |
| AniGliScans | no | Basic Integration |
| AnshScans | no | Basic Integration |
| ArcaneScans | no | Basic Integration |
| ColoredManga | no | Basic Integration |
| CrazyScans | no | Basic Integration |
| CulturedWorks | yes | Basic Integration |
| DeathTollScans | no | Basic Integration |
| DynastyScans | yes | Basic Integration |
| EightMuses | yes | Basic Integration |
| EightMusesXXX | yes | Basic Integration |
| Example Provider | no | Enhanced Integration |
| FirstKiss | no | Basic Integration |
| FreeManga | no | Basic Integration |
| HatigarmScans | no | Basic Integration |
| HentaiRead | yes | Basic Integration |
| HentaiWebtoon | yes | Basic Integration |
| IMHentai | yes | Basic Integration |
| KissComic | no | Basic Integration |
| KissmangaIN | no | Basic Integration |
| LewdManhwa | yes | Basic Integration |
| Manga3S | no | Basic Integration |
| MangaBat | no | Basic Integration |
| MangaEighteenUS | yes | Basic Integration |
| MangaFox | no | Basic Integration |
| MangaHasu | no | Basic Integration |
| MangaHentai | yes | Basic Integration |
| MangaHereToday | no | Basic Integration |
| MangaKisa | no | Basic Integration |
| MangaLife | no | Basic Integration |
| MangaNel | no | Basic Integration |
| Manganelos | no | Basic Integration |
| MangaNeloToday | no | Basic Integration |
| MangaOwlio | no | Basic Integration |
| MangaReaderTo | no | Enhanced Integration |
| Manhuaga | no | Basic Integration |
| ManhuaPlus | no | Basic Integration |
| ManhuaUs | no | Basic Integration |
| ManhuaZ | no | Basic Integration |
| ManhwaHentaiMe | yes | Basic Integration |
| ManyToonCOM | yes | Basic Integration |
| MonochromeScans | no | Basic Integration |
| MyAnimeListManga | no | Basic Integration |
| NovelCoolEN | no | Basic Integration |
| RadiantScans | no | Basic Integration |
| ReadM | no | Basic Integration |
| ReaperScans | no | Basic Integration |
| SectScans | no | Basic Integration |
| TapTrans | no | Basic Integration |
| TCBScans | no | Basic Integration |
| TenshiMoe | no | Basic Integration |
| TheGuildScans | no | Basic Integration |
| ViewComics | no | Basic Integration |
| VizShonenJump | no | Basic Integration |
| WebtoonTRCOM | no | Basic Integration |
| WhimSubs | no | Basic Integration |
| WoopRead | no | Basic Integration |
| WordExcerpt | no | Basic Integration |
| XlecX | yes | Basic Integration |
| XunScans | no | Basic Integration |

### Android shim inventory (from `extensions-source`)

Counts are files in `src/` that import the class.

| Area | Used by (files) | Shim effort |
| --- | --- | --- |
| `android.util.Log`, `android.util.Base64`, `android.os.Build`, `android.net.Uri`, `Color` | Base64 101, Log 10 | Trivial |
| `SharedPreferences`, `Context`, `Application` (Injekt `applicationContext`) | 92, 9 | Small: map-backed store per source id |
| `CookieManager` (in `core/Cookie.kt`) | 7 | Small: forward to the cookie jar |
| `android.graphics` `Bitmap`, `BitmapFactory`, `Canvas`, `Rect` | 61, 55, 54, 42 | Moderate: tile un-scrambling needs real decode, draw and encode. Use Java2D or ImageIO, and check output quality per site. |
| `android.webkit` `WebView`, `WebResourceResponse`, Chromium boundary classes | 18 | Heavy: this is a browser. Stub for Phase 0. Real support means headless Chromium over CDP. |
| `androidx.preference.*`, `android.widget.*`, `android.view.*`, `android.text.*`, `Toast`, `Activity` | 229 (preference), 25, 3, 30 | Stub-only. Needed so classes load. Settings UI comes from our own UI, not these classes. |

Cloudflare/JS-heavy sites are the costly part. Most extensions use only the trivial and small rows.

**Prior art:** Suwayomi-Server runs Tachiyomi/Keiyoushi extensions on the JVM with an Android compatibility layer. Read its compat module before writing ours. (From memory, not verified in this repo.)

## Phase 1: Extension host service

Location: `extension-host/` (new, top-level).

**Status (2026-10-17):** step 1 done. `extension-host/` is a Gradle project (runtime + Android shims + HostRegistry) that builds to `build/libs/extension-host.jar` with JDK 21. Copied from `phase0-spike/runtime`. Not committed. Debt: `build.gradle.kts` still points `compileOnly` at a Gradle cache path for the androidx.preference stubs. Replace with source stubs before merge.

**Status, step 2 (2026-10-17): per-extension class loaders done.** `ExtensionClassLoader` (child-first for extension, theme and resources; host API classes always from the parent) and `ExtensionLoader` (instantiates `keiyoushi.source.Generated`, handles `createSources`). `HostRuntime.init()` registers Injekt singletons once per JVM. Verified: MangaKatana, Toonily (Madara theme) and MangaFire (multi-source) load and run search, details, chapters and pages in one JVM. Each extension has its own loader, so the shared `Generated` class name does not clash. Dev harness: `eu.kanade.tachiyomi.host.HostSmokeKt`.

**Blocker found for step 2 (install path):** the publish script (`extensions-source/.github/scripts/publish-repo.py`) publishes APKs, not JARs. APKs contain DEX bytecode, which a JVM cannot load. Install needs one of: (a) DEX to JVM class conversion (dex2jar-style), with the usual fidelity risk; (b) build each extension from source to a JAR in our own CI, as the spike does. (b) is more reliable and matches the Phase 0 method. Decide before the catalog install step.

**Decision: (b), build from source.** Done (2026-10-17): `extension-host/tools/build-jars.py`.

- Compiles the module and its theme and lib deps with Gradle (JDK 21, Android SDK). Packs the classes into `<module>.jar`, leaving out host-provided packages (Mihon source API, network, core utils, androidx). Copies theme assets under `assets/`.
- Reads name, lang, id and baseUrl from the KSP `Generated.kt` (two shapes handled; runtime-computed baseUrls recorded as `dynamic`).
- Writes `data/jars/index.json`, pinned to the `extensions-source` commit it was built from.
- Incremental: rebuilds a module only when its source tree hash changes (or with `--all`).
- Result: 27 of 27 day-1 modules built, 138 sources in total. Three JARs (MangaKatana, Toonily, MangaFire) load and run search, details, chapters and pages in one JVM. AllManga fails on WebView, as before.

**Status, step 3 (2026-10-17): catalog, install state and HTTP API done.** Verified by hand with curl against a running host.

- `catalog/Catalog.kt` reads `data/jars/index.json` (read-only, reloads on change). Lists modules, versions, and sources.
- `state/InstallStore.kt` keeps installs in `data/state.json`: module, version_code, hash, JAR, enabled flag, install time, last health.
- `Probe.kt` runs search, details, chapters and pages through the per-extension loader. Maps failures to the Phase 0b buckets (blocked, timeout, 401, shim-gap, webview-needed). Results are display only (D6).
- `api/Server.kt` on `com.sun.net.httpserver`. Bearer token from `HOST_TOKEN` (required). Routes: `/health`, `GET /catalog`, `GET /extensions`, `POST /extensions/{module}/install[?version_code=&hash=]`, `enable`, `disable`, `test?q=`, `GET health`, `DELETE /extensions/{module}`.
- Checked: MangaKatana install, test (all four steps ok), disable, enable. Toonily test ok. AllManga test gives `webview-needed`. Uninstall works. Unknown module gives 404. No token gives 401.
**Status, step 7 and packaging (2026-10-17).**
- Contract tests: `extension-host/src/test/.../ServerContractTest.kt`, 10 tests, all pass (`./gradlew test`). They cover auth, catalog, install, pinned versions, enable/disable, uninstall, persistence across restart, missing JAR, and 404s. They use a fake index and empty JARs, so no network is needed.
- Packaging: `tools/vendor.sh` builds `vendor/keiyoushi-core.jar` (compiled Keiyoushi core from extensions-source) and `vendor/androidx-preference-stubs.jar`. Both are on the host's runtime classpath and gitignored. Verified: the host runs with only its own jars and an extension test passes.
- Tried vendoring Keiyoushi core as source: 465 compile errors (Android UI and resources, plus a lib-version mismatch in related-manga overrides). Rejected in favour of the compiled jar.
- Integration tests: `extension-host/src/test/.../IntegrationTest.kt`, 5 tests, gated by `HOST_IT=1` (skipped otherwise, and the skip is reported). They work on a copy of the build output, so the real `state.json` is never touched. Passing from this network: MangaKatana, Toonily (Madara), MangaFire (multi-source), each with all four steps. AllManga reports `webview-needed` as expected. Mangakakalot records its result whatever happens (D6). `HOST_IT` is a Gradle test input, so a cached skip can't be reused.
**Status, container (2026-10-17).** `extension-host/Dockerfile` (JDK 21 build, JRE runtime, non-root uid 10001). Compose service `extension-host` in both files: internal network only, no published port, `EXTENSION_HOST_TOKEN` required (in `.env.example`), data in the `extension_host_data` volume. Built locally with compose. Seed the volume with `extension-host/tools/seed-container.sh`, which also chowns it to uid 10001; without that, installs fail to write. Verified from inside the compose network: health, auth (401 without token), 27-module catalog, upstream install, and MangaKatana and Toonily tests all pass. Requires `tools/vendor.sh` before building (vendor JARs are not in git).

**Status, upstream catalog (2026-10-17).**
- `tools/fetch-upstream.py` decodes upstream `index.pb` (schema from `extensions-source/.github/scripts/index_pb2.py`) into `data/upstream/index.json`: 1434 extensions. The host serves it at `GET /upstream`, with flags `in_local_build`, `local_module` and `installed`. Matching is by upstream package name, not by directory name.
- Finding: upstream renamed some packages. Hive Scans is `en.infernalvoidscans` and Vortex Scans is `en.arvenscans`, though their source dirs are `hivescans` and `vortexscans`. Matching by directory name would have missed them. The build now records each module's package (from `pkgName`, or `<lang>.<dir>` by default). All 27 day-1 modules match an upstream package.
- Finding: upstream also publishes a JAR per extension (`jarUrl`, release assets). I downloaded `tachiyomi-en.mangakatana` from upstream, and the host loads it and runs search, details, chapters and pages. So an install from upstream JARs works too.
- Correction: `signingKeyFingerprint` in `repo.json` is the APK signing key. It is not a signature on the index, so checking it would not verify the index. It is recorded for display only. Nothing is verified against it, because installs come from the local build.
- Tests: 12 contract tests (including `/upstream`) and 5 gated integration tests pass.
- **Decided: install source = upstream (option 2).** Default install downloads the Keiyoushi release JAR. Each download is checked against the SHA-256 that GitHub publishes for the release asset (release digest API). Fails closed: a missing digest or a mismatch refuses the install (HTTP 502). Verified JARs are stored under `data/jars/upstream/`. The local build stays as `?source=local` for unreleased work.
- Install records carry `source` and `package`. `update_available` compares against the upstream catalog for upstream installs.
- Tests: 12 contract, 5 upstream-install (offline, fake GitHub: good digest, wrong digest, missing digest, reuse, local path), 5 integration (`HOST_IT=1`, live). All pass.
- CI (later) now needs no Android SDK: it refreshes `data/upstream/index.json` on a schedule and runs the tests. The local JAR build is only for unreleased work.


**Version history (2026-10-17).** `index.json` keeps one `versions` list per module. Each record holds `version_code`, source hash, JAR name, sources, build time and the `extensions-source` commit. JARs are named `<module>@<version_code>-<hash8>.jar`, so older builds stay on disk for rollback. A new record is added only when the version_code or source hash changes. Verified: rebuilding unchanged source does not duplicate a record. Migrated the old flat index in place.

**CI (decided, later).** Automation will run as a GitHub Action, after all of Phase 1 to 6 is built and tested. Trigger: upstream `extensions-source` changes. Steps: pull, run `build-jars.py`, publish `index.json` and the JARs.

**Updates (not automatic yet).** Nothing pulls upstream or rebuilds on its own. Today the flow is manual: `git pull` in `extensions-source`, then `build-jars.py`. Only changed modules rebuild. To automate: a scheduled job (systemd timer or CI) that pulls, runs the build, and publishes the index. Its gaps: the build machine needs JDK 21 and the Android SDK, and the host needs to swap in a new JAR while keeping the old one as rollback. The index records each module's `version_code`, so the host can show "update available". Keep the old JAR until the new one passes a health check.

- [ ] Gradle project, JVM. Loads the extension JARs against the shim module and the Keiyoushi lib.
- [ ] Catalog: fetch `repo.json` and the index from the Keiyoushi repo. Verify the `signingKeyFingerprint` from `repo.json` before trusting an index. The index is produced by `.github/scripts/publish-repo.py` in `extensions-source` and published to the `repo` branch of `keiyoushi/extensions`. The local `/home/futs/Apps/extensions` clone only has a 2-entry shim index. The full index is `index.pb` on GitHub (about 1,400 packages).
- [ ] Install, update and uninstall extensions. Store JARs under a data dir.
- [ ] HTTP API (localhost only, internal auth token):
  - `GET /extensions` (installed), `GET /catalog` (available)
  - `POST /extensions/{pkg}/install`, `DELETE /extensions/{pkg}` (uninstall)
  - `POST /extensions/{pkg}/enable`, `POST /extensions/{pkg}/disable` (keeps the install, skips it in search)
  - `GET /extensions/{pkg}/health` (last check, error class, message). Written by search, details and pages calls, and by a manual "test" action.
  - `POST /search` with `{query, sources[]}`
  - `GET /series/{source}/{id}`, `GET /series/{source}/{id}/chapters`, `GET /chapters/{source}/{id}/pages`
- [ ] Per-extension timeout and error isolation. A crashing extension must not take down the host.
- [x] Own container in the stack (done 2026-10-17): a new service in `docker-compose.yml` and `docker-compose.dev.yml`, alongside the backend, frontend, PostgreSQL and Valkey. Reachable only on the internal Docker network. Extension JARs live in a named volume.

## Phase 2: Kuroibara backend integration

**Status, slice 1 (2026-10-17).**
- Host browse routes added (needed by the backend): `POST /extensions/{module}/search?q=&page=`, `POST .../details` with `{"url"}`, `POST .../pages` with `{"url"}`. Live check: MangaKatana search returned results; details and pages were not checked end to end (see open issue below). Contract tests cover validation and install state (13 pass).
- Backend client `backend/app/sources/host_client.py` (async httpx, bearer token, typed errors). Covers health, catalog, upstream, installed, install (source, version pin), uninstall, enable, disable, test, health_of. 8 tests with a mock transport.
- Migration `018_add_extension_series.py` (additive): `series`, `series_source_links`, `series_metadata`. Checked: upgrade, downgrade, upgrade again on a scratch database.
- Models `app/models/extension_series.py`. Service `app/sources/series_service.py`: add a title from a details result (base and tagged current written once; duplicates by extension and URL return the existing series; NSFW from content warning), revert to provider (keeps base and the cached MangaUpdates entry). 6 database tests.
- Deviations from the plan above: no `installed_extensions` table. The host is the source of truth for installs, so Kuroibara does not keep a copy. `series_metadata` is one table with `base`, `current` and `mangaupdates` columns instead of separate tables.
- Config: `EXTENSION_HOST_URL` and `EXTENSION_HOST_TOKEN` in `app/core/config.py`.
- Compose: `EXTENSION_HOST_TOKEN` is no longer required for every compose command. The host itself refuses to start without a token.
- Open: the job-system integration for downloads (needs a look at the existing job runner). The FastAPI routes that expose add, revert and browse to the UI. The host's details and pages paths, end to end, with a real title.
**API routes (2026-10-17).** Mounted at `/api/v2` (`backend/app/api/api_v2/`).
- Sources (proxy to the host, auth required): `GET /sources/catalog`, `GET /sources/installed`, `POST /sources/{module}/install?source=upstream|local`, `DELETE /sources/{module}`, `POST .../enable`, `POST .../disable`, `POST .../test?q=`, `POST .../search?q=&page=`, `POST .../details` (`{"url"}`), `POST .../pages` (`{"url"}`). Module is a path parameter, so slashes work.
- Series: `POST /series` (body: module, source name and lang, source id, content warning, and the details `manga`). The package comes from the host's install record, not the client. Returns 201 new, 200 if the same extension and URL already exist. `GET /series` (paginated), `GET /series/{id}`, `POST /series/{id}/revert`.
- Host failures: unreachable is 503. Host 4xx passes through. Other host errors are 502.
- Tests: 11 API tests with a mocked host and the test database. With the other new tests, 25 pass (`VALKEY_HOST=localhost`, `DB_HOST=localhost`). Without Valkey running, each API test spends about 46 seconds in startup, because the lifespan waits on Redis.
- Not done: the job-backed download endpoints (waiting on your decision above), and the reader endpoints that stream pages.

**Download method: Mihon's, adopted (2026-10-17).** Decided by you. Answers recorded here:
- Hand-off: pages go into `<chapter>_tmp/`. The completeness check runs first, then ComicInfo.xml, then the CBZ is written as `<chapter>.cbz.tmp` and renamed to `<chapter>.cbz`, and the `_tmp` folder is deleted. Folder mode renames `_tmp` to `<chapter>`. Default is CBZ (`saveChaptersAsCBZ` = true).
- The waits (2s, 4s, 8s, three retries) are error backoff for a failed page. They are not rate limits.
- Rate limits: each extension sets its own (`rateLimit(permits, period)` from keiyoushi core, inside its HTTP client). The host runs that unchanged. Mihon's download path does not read 429 or Retry-After. Kuroibara does (`services/download.py`, around line 344), and that could be kept as an addition.
- Kuroibara's per-provider `page_delay` dict was a hand-tuned stand-in for rate limits. Under this method it goes away; the extension's own limit applies.

Implemented: `backend/app/sources/download_writer.py` (ChapterWriter, with_retries, safe_name) and 12 filesystem tests. Covers: pages in `_tmp`, partial pages with resume, finished-only counting, completeness refusal, folder and CBZ commit, the already-committed guard, and retry waits 2, 4, 8.

**Identity (answer to "where does the entry id come from", 2026-10-17).** `series.id` is a Kuroibara UUID (`uuid4` in `BaseModel`), not a provider id. The provider's identity is `(module, series_url)`, unique in the table. Each source's own IDs (like the Keiyoushi `source_id`) are stored for reference only. So two providers can use the same title id without clashing. Known risk: if a site changes its URL for a title, the same title can get a second entry. Mitigation later: a "re-link" action on the entry, or matching on the source id where the extension gives one.

**Deferred: reading state, activity and stats (decided 2026-10-17, to build after the download work).**
- Design basis: Mihon's per-chapter read state (read, bookmark, last read page) plus AudioSilo's per-user pages (progress per series per user).
- Reading state is per user per chapter: `reading_state(user_id, series_id, chapter_key, read, bookmark, page, updated_at)`. Chapters come from the source; the table stores only what the user did.
- Library membership must become per user too. `series.in_library` is global today, which is wrong once there is more than one user. Move it to `user_library(user_id, series_id, in_library, added_at)`.
- Activity: append-only `reading_events(user_id, series_id, chapter_key, kind, at)` for "read", "started", "finished". Daily totals are derived from it. A daily aggregate table can be added if queries get slow.
- Stats to show: latest read, chapters read today, this week, this month, this year. Heatmap of days with activity (git-style), plus totals per series.
- Migration (Mihon's) uses reading_state: copy read and bookmark by chapter number from the old entry to the new one, then mark the old entry as migrated. This is the step the migrate endpoint is waiting on.

**Status, Mihon model for library entries (2026-10-17). Replaces the one-series-many-sources design (D-series).**
- `series` = one library entry per title per source (`module`, `package`, `source_name`, `source_lang`, `source_id`, `series_url`, `title`, `cover_url`, `in_library`). Unique on (module, series_url). `series_source_links` is gone.
- `series_metadata` = one row per entry: `base` (provider snapshot, written once), `current` (shown values, each with origin), `mangaupdates` (cached comparison, Phase 2b). `series.title` and `cover_url` copy `current` for listing.
- Migration: `POST /api/v2/series/{id}/migrate`. Creates or reuses the target entry. `replace` (default true) takes the old entry out of the library. `carry_metadata` (default false) copies the values chosen from MangaUpdates or edited, keeping their origins, plus the MangaUpdates cache. Refuses the same title on the same source (409). Re-adding a removed title puts it back.
- Downloads stay with the old entry's folder. The target gets its own folder (new id).
- Not yet: read state and chapter bookkeeping. Mihon carries read state across a migration. Kuroibara has no chapter table for source entries yet, so that needs a `series_chapters` table first.
- Verified: 68 backend tests (service, migration, API, worker). Migrations 018 and 019 upgrade, downgrade to 017 and upgrade again on a scratch database.

**Status, separate worker and claims (2026-10-17).**
- Worker: `python -m app.sources.worker_main`, same image as the API, as its own compose service `source-worker` (one replica) in both compose files. Loop: claim a batch, download each chapter in its own session, wait `SOURCE_WORKER_POLL_SECONDS` when idle. SIGTERM finishes the batch. A hard stop leaves rows `downloading`, and the next start recovers them.
- Atomic claim: `claim_next()` uses `SELECT ... FOR UPDATE SKIP LOCKED`. Rows record `claimed_by` and `claimed_at`. Two workers or an API call can't take the same chapter.
- Startup recovery moved from the API lifespan to the worker. The API never resets rows, so it can't disturb a running worker.
- Folder naming: `<module>/<title> [<first 8 hex of series id>]/`. Two series with the same title never share a folder. The series id stays the same when its source changes, so migration does not move files.
- Verified: 56 backend tests pass (claims across two real sessions, orphan recovery, batch run, graceful stop, folder uniqueness). Live, on a scratch database: the worker claimed two MangaKatana chapters (`worker-<host>`) and wrote them as CBZ into `One Piece [6962ca81]/`.
- Setup note: `EXTENSION_HOST_TOKEN` must be in `.env`, because the API and the worker both read it there. It is not in `.env` yet; I did not add a token to your file.

**Status, download pipeline (2026-10-17). Done, steps 1 to 5 of the list above:**
1. Persisted queue: migration `019_add_source_downloads.py`, model `SourceDownload`, worker `app/sources/download_worker.py`. `recover_queue()` runs at startup (in the lifespan), so interrupted rows go back to queued.
2. Parallel pages: 5 per chapter (`parallel_pages`), with a per-chapter semaphore. Per-source parallelism is the `limit` on each run.
3. Host image endpoint: `POST /extensions/{module}/image` with `{url, image_url, index, offset}`. Returns the raw bytes with `X-Upstream-Status`. Uses the extension's `getImage`, so its headers, referer and rate limit apply. Verified live: a real MangaKatana page is a JPEG (388 KB), and 206 handling is in place.
4. ComicInfo.xml: written before commit and packed into the CBZ. Fields: Series, Title, Number, Writer, Genre, Summary, Web. Text is XML-escaped.
5. Wiring: `POST /api/v2/series/{id}/downloads` (empty body = every chapter from the source), `GET /api/v2/series/{id}/downloads`, `POST /api/v2/series/downloads/process?limit=`.

Verified:
- Backend tests: 50 pass across the new files (download writer 12, worker 10, download API 4, plus earlier).
- Host: 14 contract, 5 upstream-install, 6 integration (live, `HOST_IT=1`).
- End to end, live, on a freshly migrated scratch database: added One Piece from MangaKatana, queued two chapters, downloaded them. Chapter 1 gave 52 pages and Chapter 2 gave 24, each a single CBZ with ComicInfo.xml and JPEG pages.

Deviations and open points:
- Resume is per page, not per byte. The worker writes whole responses. The host honours `offset` when the extension returns 206, so a byte-level resume is ready once the worker streams.
- Downloads run only when `process` is called. No background loop yet. The loop needs a decision (interval, and whether it runs in the API process or a separate one).
- Two concurrent `process` calls could pick the same queued row. A row-level lock (`SELECT ... FOR UPDATE SKIP LOCKED`) fixes that. Not done.
- Migrations 018 and 019 were checked upgrade, downgrade and upgrade on scratch databases. The `series_metadata` model was wrong (it inherited a second primary key) and is fixed to match migration 018.


**Download design (confirmed 2026-10-17, before the Phase 2 job work).**

How Mihon does it (`app/src/main/java/eu/kanade/tachiyomi/data/download/`):
- Queue is persisted (`DownloadStore`) and restored at startup. Runs in a `DownloadWorker` (WorkManager, `ExistingWorkPolicy.REPLACE`).
- Parallel: up to 5 sources (`parallelSourceLimit`) and 5 pages per chapter (`parallelPageLimit`), both user settings.
- Page list is fetched once and stored on the download, so a resume does not refetch it.
- Each chapter is written to a `.tmp` folder, then renamed to its final name only when every page is in. A partial chapter is never shown as downloaded.
- Each page is retried 3 times with 2, 4 and 8 second waits. A partial file resumes with HTTP Range (206). A 416 deletes the partial and starts over.
- Completeness check before commit: page count matches, no `.tmp` left, split pages counted once.
- Folders are human-readable (source, manga, chapter), and CBZ is optional.

What Kuroibara does (`backend/app/core/services/download.py`, `jobs/queue_manager.py`):
- Queue lives in memory (`_jobs`, `_priority_queues`). A restart loses every queued and running download.
- Pages are written straight into the final chapter folder. No temp folder, no rename, no completeness check.
- A chapter with any page downloaded is marked `downloaded`. Only `download_error` records the missing pages. Example: 1 page of 50 gives `downloaded`.
- Pages download one at a time, with per-provider delays hardcoded in a dict.
- Page list is refetched on each retry. Nothing persists between attempts.
- Concurrency: 3 downloads total (`max_concurrent_downloads`).
- Storage path is keyed by database UUIDs, so folders are not readable.

Proposed for the extension path (Phase 2 job integration):
1. A persisted queue table (`download_queue`). Survives restarts.
2. A chapter is `downloaded` only when all pages are in. Otherwise `error`, with the page list kept for retry.
3. Temp folder plus atomic rename, as in Mihon.
4. Parallel pages with a limit, and per-source delays from the extension (not a hardcoded dict).
5. Resume with Range, and reuse the stored page list.
6. Human-readable layout: `<root>/<source>/<series>/<chapter>`.

Decision needed: the TODO said to reuse the existing job runner. Reusing it would inherit the in-memory queue and the partial-chapter behaviour. My recommendation is a separate, persisted download pipeline for source-backed series, with the existing runner unchanged. Confirm before I write the job code.

- Open issue found: MangaKatana search returned 5 results on one request and 0 on the next, from the same host. Plain curl gets results every time. Not yet explained. Health should flag empty search results as a warning.


- [ ] Client module `backend/app/sources/` that talks to the host.
- [ ] Alembic migration (additive only): `installed_extensions`, `series`, `series_source_links`. Keep existing tables untouched.
- [ ] Adding a title from an extension result writes `series_metadata_base` and `series_metadata_current` (both provider values). See Phase 2b.
- [ ] Job-system integration for downloads, reusing the existing job runner. Do not create a second queue.
- [ ] Tests: client against a fake host; migration up and down on a copy of the dev DB.

## Phase 2b: Metadata from the provider, optional MangaUpdates overwrite

Model: AudioSilo's admin console, which shows where each value came from and lets you pick and revert.

Flow:

1. User selects a title from a provider. The series is added to the library with the provider's metadata, so it loads straight away.
2. If the name is wrong or authors are missing, the user clicks **Update Metadata from MangaUpdates** on the series page.
3. A comparison view opens: provider value and MangaUpdates value side by side, with a choice per field. The user picks which to keep and applies.
4. **Revert to provider** restores the base record from step 1.

Data model:

- [ ] `series_metadata_base`: the provider snapshot taken when the title is added. Never edited.
- [ ] `series_metadata_current`: the values shown in the library, each tagged `provider`, `mangaupdates` or `edited`.
- [ ] `mangaupdates_snapshot`: cached MangaUpdates response for the matched entry. Stored so the comparison works offline after the first fetch.
- [ ] Fields: title, alternative titles, description, cover, authors, genres, status, type, year, NSFW.

Behaviour:

- [ ] **Update Metadata from MangaUpdates:** matches the series to a MangaUpdates entry (title and year), shows candidates, requires the user to confirm the match. Never auto-applies.
- [ ] **Compare view:** per-field choice, provider as default. Apply writes `series_metadata_current`.
- [ ] **Revert to provider:** resets `series_metadata_current` to `series_metadata_base`.
- [ ] A provider refresh updates `series_metadata_base` only. It does not overwrite fields tagged `mangaupdates` or `edited`.
- [ ] Tests: base snapshot is immutable, revert restores exactly the base, a field chosen from MangaUpdates survives a provider refresh.

## Phase 2c: Extension import (D5)

- [ ] Settings page: add a catalog URL (Keiyoushi by default, left as the user's choice) or upload local JAR files.
- [ ] Validate each JAR before install: manifest, source list, and signature where the catalog provides one.
- [ ] Installed extensions show version, languages and NSFW flag. Remove and update actions.
- [ ] Fresh install starts with zero extensions. Global search says so and links to the catalog.

## Phase 2d: Migrate a series to another source (Mihon behaviour)

When a source stops responding or its extension needs an update, the user can move a series to another source. Reading progress and metadata are kept. Only the place it is read or downloaded from changes.

- [ ] Action on the series page: **Migrate**. Pick a target source (installed extensions only), then search it using the current title.
- [ ] Show candidates from the target source. The user confirms the match. Never auto-matches.
- [ ] Carry over: read state per chapter, mapped by chapter number (with a fallback to the closest number and a list of unmapped chapters), reading position, and categories or library membership.
- [ ] Metadata: the user chooses whether to keep the current metadata or take the target source's. Default is keep.
- [ ] Downloads: already-downloaded chapters stay on disk. Option to re-download from the new source.
- [ ] Keep the old source link in `series_source_links` as a disabled entry, so the user can switch back.
- [ ] Existing fields to build on: `manga.provider` / `manga.external_id` (single source only, replaced by `series_source_links`) and `chapter.provider_external_ids` / `chapter.fallback_providers` (already present, currently unused by a UI path).
- [ ] Health indicator: a series whose source is failing or needs an update shows a warning and a Migrate button. Source health is recorded per extension by the host (last success, last error).
- [ ] Tests: chapter mapping (exact, renumbered, missing), progress preserved after migrate, metadata choice respected, switch back restores the old link.

## Phase 3: Global search (Mihon behaviour)

- [ ] `GET /api/v2/search?q=` fans out to all installed extensions in parallel with per-source timeouts.
- [ ] Results are grouped by normalised title. Each group lists the sources that have it, for example `Found in: MangaDex, ComicK`.
- [ ] Partial results stream to the UI (existing WebSocket is fine).
- [ ] Tests: grouping, timeout behaviour, one failing source does not fail the request.

## Phase 4: Cloudflare capture

- [ ] Endpoint to start a capture for an extension's base URL. The UI opens the site in a new tab. The user solves the challenge.
- [ ] Capture cookies and user agent. Store them in the host cookie jar for that extension only.
- [ ] Keep FlareSolverr as the first attempt. Show the manual capture option when it fails.

### Phase 4a: FlareSolverr-first (decided)

**Status (2026-10-17):**

- [x] Solver endpoint at `http://172.16.40.12:8191` reachable. Responses have the fields the interceptor reads (`status`, `solution.userAgent`, `solution.cookies[name,value]`).
- [x] Interceptor implemented in the spike runtime (`phase0-spike/runtime/.../CloudflareInterceptor.kt`). Detects `cf-mitigated: challenge` or 403/503 from Cloudflare, solves, caches per host, retries with cookies and UA. Off when `FLARESOLVERR_URL` is unset.
- [x] Mock test: challenge, solve, retry (200), then cache hit (200). With no solver, the 403 surfaces. Run in `phase0-spike/cf-test/`.
- [ ] Live test not done: allmanga and MangaFire serve no challenge from this network right now, so the solve path never fires there. Need a challenged site to test live.
- [x] Compose: `flaresolverr` service added to `docker-compose.yml` and `docker-compose.dev.yml` under profile `flaresolverr`. Not started by default. Enable with `--profile flaresolverr`, or set `FLARESOLVERR_URL` to an existing instance.
- [ ] GET only. POST challenges are not solved yet.

Kuroibara already talks to FlareSolverr (`backend/flaresolverr_integration.py`: sessions, `request.get`). Reuse that approach in the extension host.

- [ ] Replace the Phase 0 pass-through `CloudflareInterceptor` with a real one. Detect `cf-mitigated: challenge` (and 403/503 from a Cloudflare server) on the response.
- [ ] On detection, call FlareSolverr `POST /v1` with `cmd: request.get` (or `request.post` for POST requests), the same URL, and a session per host.
- [ ] From the solution, take the cookies and the `userAgent`. Store the cookies in the host cookie jar for that host. Use that UA for later requests to the host. `cf_clearance` is bound to UA and IP.
- [ ] Retry the original request with the new cookies and UA. Do not return FlareSolverr's body as the response. This keeps headers and method intact.
- [ ] Cache clearance per host until it expires, so each request does not trigger a solve.
- [ ] Implement a real `CookieManager` shim (Phase 0 is a stub) so extensions read and write cookies through the same jar.
- [ ] Add a `flaresolverr` service to `docker-compose.yml` and `docker-compose.dev.yml`. Host config: `FLARESOLVERR_URL`. Build locally per the dev.sh note.
- [ ] Fallback: if FlareSolverr fails or the challenge is unsolved (Turnstile, for example), show the Phase 4 manual capture.
- [ ] Known limit: extensions that run JS in an Android WebView (MangaFire references WebView 24 times) need more than cookies. FlareSolverr does not cover that. Track those per extension in Phase 0b.
- [ ] Test on the day-1 Cloudflare-flagged extensions (allmanga, MangaFire) against a local FlareSolverr container.

## Phase 5: Backend API for the UI

Built on this branch so the UI branch has a stable contract.

- [ ] Document `/api/v2` endpoints in `docs/API_V2.md`.
- [ ] Generate or hand-write TypeScript types for the React app.

## UI work (branch `feat/ui-react-shadcn`)

Separate branch, based on `dev`. Built against the `/api/v2` contract.

- [ ] Port Kuroibara's Vue frontend to React + shadcn/ui + Tailwind v4, page by page. Decide per page whether to rewrite or keep until cutover.
- [ ] Take AudioSilo's tokens from `audiosilo-server/admin-ui/src/styles/` and `STYLEGUIDE.md` (type scale, spacing, radius, hairline borders, shadows only on floating layers). Map them to Kuroibara's current palette, keeping Kuroibara's colours.
- [ ] Layout: top bar, sub bar with segmented sections, covers-first grids.
- [ ] Extensions page: catalog, language and NSFW filters, install and uninstall, version and status.
- [ ] Global search page: result cards with source badges.
- [ ] Series page: metadata with a source label on each field, the MangaUpdates compare view, chapter list, download button.
- [ ] Mobile layout under 720px.

## Phase 6: Cutover

- [ ] Parity checklist: each feature used in `dev` works on the new path. Record gaps.
- [ ] Switch default search and add flow to the new path behind a setting.
- [ ] Mark old providers deprecated in `PROVIDER_STATUS.md`. Remove them in a separate PR after one release.

## Phase 6b: Move native providers onto Keiyoushi extensions

Goal: where a native Kuroibara provider has a Keiyoushi extension for the same site, use the extension. Speed is a hypothesis, not a result. Measure it before claiming it.

- [ ] Map each native provider (`backend/app/core/providers/*.py` and the CSV rows) to a Keiyoushi extension package, or record "no extension". Start with the day-1 set and the rows marked `Basic Integration` or `Fully Integrated`.
- [ ] Benchmark per site, native vs extension: search latency, chapter-list latency, page-fetch latency, and error rate over the same test title. Record the results in the TODO.
- [ ] Switch a site to its extension only when it matches or beats the native provider on the benchmark and passes the Phase 0b checks for that site.
- [ ] Keep the native provider installed as a fallback until the extension has been stable for one release. Use the fallback mechanism in Phase 2d.
- [ ] Native providers with no extension stay on the native path. Decide per provider whether to keep it, or to write a Keiyoushi extension for it. Writing one means working in `extensions-source` under its `CONTRIBUTING.md` rules, so do it as a separate upstream contribution.
- [ ] Record the mapping table (native provider, extension package, benchmark result, decision) in `PROVIDER_STATUS.md`.

## Risks

- Android shim fidelity: extensions may call APIs we stub wrongly, and failures are silent (wrong return values). Mitigation: Phase 0 spike and per-extension tests.
- Bitmap and WebView shims: image descrambling and Cloudflare are the costly parts. Mitigation: treat them as their own work items.
- Extension churn: Keiyoushi updates often. Mitigation: pin versions per install, update on demand.
- Scope: several weeks of work. Each phase is shippable on its own behind the flag.

## Open questions for the user

- Which extensions must work on day one? (Your current providers, or a fixed list.)
- Keep the dependency bump commit (`0796388`) on this branch, or drop it?
- Should the extension catalog come from the Keiyoushi URL by default, with local JAR import as an option?
