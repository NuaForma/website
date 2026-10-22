# Reviewed reference inputs

`runtime/manifest.json` binds exactly five public profile/notice files to the signed product source for release `0.2.0-alpha.2`, commit `833da8297d72c8fcdf20ae5231c4332cd99118bd`. Each checksum was compared with `git show <sourceCommit>:deployment/pdf-runtime/<path>` in the product repository; the profile/notice bytes remain unchanged from alpha.1. These are packaging inputs, not independently editable runtime policy. Preserve upstream notices and update only from a reviewed immutable product release.

`migration-files.json` retains every original public static path/checksum from product commit00e363fb3760a79c19c1e046bd42e2dcb48a62f5. Migration validation compares every byte and public path before/after the Pages ownership change. Future authorized content changes may differ, but must preserve existing URLs or explicit aliases. The website never fetches these source references at request time or accesses a sibling checkout implicitly.
