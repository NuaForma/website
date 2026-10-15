# NuaForma website

Source for [nuaforma.dev](https://nuaforma.dev), its public deployment kits and synthetic Word/JSON examples. This is a static GitHub Pages site, not a document-generation service. The [product repository](https://github.com/NuaForma/NuaForma) owns the Java/Kotlin engine, server, Playground, technical guides and releases.

## Workflow

`develop` is the default integration branch. Open feature PRs against develop; promote prepared site changes to main after the matching product release is available. Main deploys automatically only after `Website checks` succeeds. A small emergency correction may be pushed directly to main by a repository administrator, but it must be signed and brought back to develop through a PR. Signatures, no-force-push and no-deletion rules remain enforced even for administrators. Normal changes use PRs.

## Local checks

```sh
python3 -m http.server 8430 --bind 127.0.0.1 --directory site
python3 tools/site/check_site.py
python3 tools/site/check_reference.py
python3 -m unittest discover -s tools/site -p 'test_*.py'
node --check site/app.js
node --test tools/site/test_tabs.cjs
```

Compose configurations and their enforcing AppArmor overrides are checked without starting containers. Keep all files in each kit together. Package deployment downloads with `python3 tools/site/package_deployment_kits.py`; rebuild the all-in-one ZIP with `python3 tools/site/package_complete_kit.py`. The complete kit contains production and development Playground choices for AMD64/ARM64, Helm, Bruno, Postman and seven document scenarios. Never replace a published image tag or silently weaken its runtime policy.

`reference/runtime` pins reviewed profile inputs from an immutable product release, including notices/licenses. `reference/migration-files.json` records every original public path and checksum at extraction. All public website/download bytes were copied unchanged during migration; technical documentation links continue to point at the product repository. Preserve existing paths across future releases, using explicit compatibility aliases if necessary.

Document authoring uses optional python-docx/Pillow tooling; do not regenerate examples just to repackage them. Real container/example/client qualification stays in the product repository under `tools/site-qualification` and accepts this checkout explicitly, rather than requiring a hard-coded sibling directory. The old `site/README.md` is retained verbatim as a historical public file; this root guide owns current repository maintenance instructions.

## Releases and history

A product release is not fully delivered until the matching website update is deployed and live download hashes are verified. Prepare changes on develop, keep public main compatible with the released product, and explicitly coordinate the two PRs. Publication of libraries/images remains protected and main-only in the product repository; this repo has no product signing or registry credentials.

The migration retains original signed Git commits as unchanged ancestry instead of rewriting/re-signing old history. Historical product files are therefore visible in old commits, not in the current website tree. See [maintenance issue #88](https://github.com/NuaForma/NuaForma/issues/88).

NuaForma-authored code/examples are [Apache-2.0](LICENSE). Branding grants no trademark rights; runtime components/fonts keep their own terms. See the product's [notices](https://github.com/NuaForma/NuaForma/blob/main/THIRD_PARTY.md) before redistributing images.
