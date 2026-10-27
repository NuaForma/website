# Production service — arm64

Candidate `0.3.0-alpha.2` uses the native PDF engine. No LibreOffice, Bubblewrap, custom seccomp file or installed AppArmor profile is required. Keep the runtime's default security policies, non-root user, read-only root, dropped capabilities, no-new-privileges and supplied limits.

Create `custom-fonts` and `extensions`, then run `docker compose up -d`. The service binds to loopback port 8080. Inspect `/api/v1/capabilities` and `/health/ready`. Mount only appropriately licensed readable standalone TTF/OTF files and trusted extension JARs. Restart after changing fonts. Native Linux/arm64 is required; use the other kit for the other architecture.

There is no built-in authentication or TLS. Add your own authenticated TLS gateway before remote access. Do not use privileged or unconfined execution. With Podman, use VM-visible absolute font/extension paths and the native architecture; host policy remains enabled.

Standard PDF, PDF/A-2b and PDF/A-3b accept requested text watermarks. PDF/A-1b refuses every requested watermark, including opaque text. The native conversion profile rejects unsupported source constructs explicitly; it does not promise complete Word compatibility. See the [PDF guide](https://github.com/NuaForma/NuaForma/blob/main/nuaforma-docx-pdf/README.md).

Preserve NOTICE and LICENSE. Java, veraPDF and OS components retain their own terms; matching component sources/notices accompany the [release](https://github.com/NuaForma/NuaForma/releases/tag/v0.3.0-alpha.2). Stop with `docker compose down`.
