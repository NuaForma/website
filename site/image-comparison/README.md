# Image Comparison website section

This section introduces NuaForma's standalone Image Comparison library. The homepage feature and all three pages use the existing site themes and navigation. The version is **5.0.0**. Both artifacts' public Maven Central POMs, binary JARs, sources and documentation were independently checked on 2026-10-25 before website publication. Automatic cross-repository documentation updates remain future work.

The library's `main` at `4600f471631ad287b6d5e91ae1b3fce1fa5f4c09` is the information source for the Java 17 baseline, `dev.nuaforma` coordinates, Kotlin DSL, comparison contract, migration notes and original attribution. Complete technical guides remain in that repository. The getting-started page is an introductory example, not a separately maintained API specification.

## Actual engine-generated example

The synthetic images contain a deliberately changed date and two changed amounts. The Java engine produces three detected regions with no exclusions and two with the date rectangle excluded. `comparison.json` records the source commit, generator hash, measured percentages and PNG hashes. The public buttons switch between those precomputed results; no browser or server comparison service runs here, and no user images are collected.

The date exclusion is the inclusive rectangle `(435,128)-(610,166)`. Pixel tolerance is 0.1; the changed-pixel allowance remains zero. Three-pixel outlines make the detected regions visible at the site's reduced image size. The excluded region is outlined in green by the library itself, and detected changes are outlined in red. The percentage changes its denominator when the date is excluded; it is not an intensity score.

Reproduce candidates with a Java 17 installation and Python 3, without modifying the source repository or reading credentials:

```sh
python3 tools/site/build_image_comparison_demo.py \
  --source-repository /path/to/image-comparison \
  --source-ref 4600f471631ad287b6d5e91ae1b3fce1fa5f4c09 \
  --output build/image-comparison-review
```

The helper exports only Java source files from the specified commit into ignored build output and compiles the core plus `ImageComparisonDemo.java` for this fixed example. This is asset generation, not the library's release build. It never switches or changes that repository's branch and never replaces public assets. Review candidate output before copying its four PNGs and provenance JSON into this directory. Java logical-font rasterization can differ between environments; review visual differences rather than silently accepting new hashes.

## Publication boundary

This section is published through the website's normal checked PR promotion and main-only Pages workflow. Product/container downloads and their pinned runtime references remain unchanged. There is no current document-generation or Playground behavior change. A later, separately authorized library-release workflow may prepare a temporary website branch and PR carrying versioned documentation; the website repository remains the sole GitHub Pages publisher. Do not create a second Pages site or automatically publish changes from an image-comparison branch.
