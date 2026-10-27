# NuaForma website

Source for [nuaforma.dev](https://nuaforma.dev), its public deployment kits and synthetic Word/JSON examples. This is a static GitHub Pages site, not a document-generation service. The [product repository](https://github.com/NuaForma/NuaForma) owns the Java/Kotlin engine, server, Playground, technical guides and releases.

## Workflow

`develop` is the default integration branch. Open feature PRs against develop; promote prepared site changes to main after the matching product release is available. Main deploys automatically only after `Website checks` succeeds. A small emergency correction may be pushed directly to main by a repository administrator, but it must be signed and brought back to develop through a PR. Signatures, no-force-push and no-deletion rules remain enforced even for administrators. Normal changes use PRs.

## Native release coordination

The selected native product release is **`0.3.0-alpha.2`** (`v0.3.0-alpha.2`), tracked in [NuaForma/NuaForma#141](https://github.com/NuaForma/NuaForma/issues/141). Prepare matching changes on a feature branch and merge verified changes into develop; promote to main after the actual artifacts and matching source materials are public. The native engine removes LibreOffice and custom host-profile prerequisites, so deployment kits, immutable runtime references, supported example scenarios and download/version claims must be synchronized with its exact reviewed artifacts. Keep reference inputs and live downloads bound to their published release.

`tools/site/prepare_native_release.py` is the retained initial-migration helper for `0.3.0-alpha.1`. It stages that version into a fresh ignored build directory, taking an explicit product checkout and locally verified immutable source commit. Routine patch releases such as alpha.2 retain the existing document/scenario bytes, update the current version and immutable source/image references, and use package-only rebuilding under the product release procedure. It prepares all five deployment kits, RuntimeDefault Helm, matching client collections and a PDF/A-1b scenario without a requested watermark. It retains the current DOCX unless an explicitly reviewed `--template` is selected. Production and Playground digest placeholders plus `RELEASE-PREPARATION.txt` deliberately block publication. Example invocation:

```sh
python3 tools/site/prepare_native_release.py --product-repository /path/to/NuaForma --source-commit FULL_REVIEWED_COMMIT --output build/native-release-candidate
python3 tools/site/check_site.py --site-directory build/native-release-candidate/site --reference-directory build/native-release-candidate/reference --allow-preparation
```

The preparation-only check validates structure and archives, not release readiness. For the initial native migration, qualify every example against the final candidate. Subsequent releases follow the product's [single-final-approval procedure](https://github.com/NuaForma/NuaForma/blob/main/docs/release-process.md), reuse green CI for unchanged fixtures/runtime inputs, review the pages, bind both actually published image digests, replace the source snapshot with the selected release source if needed, remove the preparation marker and pass the ordinary publication checks. No site, registry or release is published by this tool.

The optional `build_native_example.py` authoring helper requires Pillow and lxml. It was used once to adapt the retained legacy template to the qualified native profile, preserving all text/markers, page geometry and table grid. It records explicit mode-15 print settings, table margins/borders, short-row policy, image paragraph heights and typography adjustments. The two JPEG images become opaque PNGs with identical decoded RGB pixels; unused preview/effects parts and editing metadata are removed. This is a deliberately authored example, not a general DOCX repair or importer extension. It refuses public-file replacement. Reproduce the adaptation only with `--source` pointing to the original template from Git history, such as website commit `e43470a50b1c86625afa122bbad295dd7fdd745a`; do not reapply it to the adapted template. Ordinary packaging retains the current reviewed native document bytes.

The reviewed candidate was qualified on product source `13dae18bd1655ddb3b9cb21355752c2fe7055682`: seven real HTTP scenarios and independent PDF-profile checks passed. Twelve page pairs were compared with genuine Word exports and visually inspected. All 6,547 body characters, their order, font faces and pagination agree; maximum measured text displacement is 0.265 pt horizontally and 0.220 pt vertically. The product issue #57 records the retained source, Word export provenance, renders and checksum-bound evidence. Existing protected engine golden files were not replaced. These measurements do not promise arbitrary DOCX compatibility or identical watermark glyph outlines.

The performance page retains its original measured source/version baseline; preparing 0.3 does not relabel historical measurements as new-engine benchmarks.

## Local checks

Image Comparison has a prominent homepage feature and a separate [project section](site/image-comparison/README.md) with a real engine-generated comparison, introductory Java/Kotlin examples, Maven/Gradle installation instructions and release status. Version 5.0.0's Java and Kotlin POMs, binaries, sources and documentation were independently checked on Maven Central before website publication. Future cross-repository release PR automation is not implemented by these pages.

The homepage introduces the product and deployment/download kits. [Template syntax](site/templates.html), [extension authoring](site/extensions.html), [fonts and operations](site/operations.html) and [short processing trials](site/performance.html) have separate guide pages with shared sticky navigation and light/dark themes. Performance figures describe a named source candidate and bounded experiments, not a sustained-capacity promise or an unchanged published image; keep request counts separate from isolated pipeline trials. Keep examples aligned with released product references; these guides do not change Playground behavior or downloadable scenarios.

```sh
python3 -m http.server 8430 --bind 127.0.0.1 --directory site
python3 tools/site/check_site.py
python3 tools/site/check_reference.py
python3 -m unittest discover -s tools/site -p 'test_*.py'
node --check site/app.js
node --test tools/site/test_tabs.cjs
```

Compose configurations and their immutable runtime references are checked without starting containers. Keep all files in each kit together. Package deployment downloads with `python3 tools/site/package_deployment_kits.py`; rebuild the all-in-one ZIP with `python3 tools/site/package_complete_kit.py`. The complete kit contains production and development Playground choices for AMD64/ARM64, Helm, Bruno, Postman and seven document scenarios. Never replace a published image tag or silently weaken its runtime policy.

`reference/runtime` pins reviewed profile inputs from an immutable product release, including notices/licenses. `reference/migration-files.json` records every original public path and checksum at extraction. All public website/download bytes were copied unchanged during migration; technical documentation links continue to point at the product repository. Preserve existing paths across future releases, using explicit compatibility aliases if necessary.

Document authoring uses optional python-docx/Pillow tooling; do not regenerate examples just to repackage them. Real container/example/client qualification stays in the product repository under `tools/site-qualification` and accepts this checkout explicitly, rather than requiring a hard-coded sibling directory. The public `site/README.md` points to this root guide for repository maintenance instructions.

## Releases and history

A product release is not fully delivered until the matching website update is deployed and live download hashes are verified. Prepare changes on develop, keep public main compatible with the released product, and explicitly coordinate the two PRs. Publication of libraries/images remains protected and main-only in the product repository; this repo has no product signing or registry credentials.

The migration retains original signed Git commits as unchanged ancestry instead of rewriting/re-signing old history. Historical product files are therefore visible in old commits, not in the current website tree. See [maintenance issue #88](https://github.com/NuaForma/NuaForma/issues/88).

NuaForma-authored code/examples are [Apache-2.0](LICENSE). Branding grants no trademark rights; runtime components/fonts keep their own terms. See the product's [notices](https://github.com/NuaForma/NuaForma/blob/main/THIRD_PARTY.md) before redistributing images.
