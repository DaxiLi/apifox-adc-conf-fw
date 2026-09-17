#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download the authoritative Apache APISIX + ADC official documentation
into this directory (docs/official/) as a local, offline reference library.

Sources
  - ADC (API7):      https://github.com/api7/adc  (main branch, docs/ + schema.json)
  - ADC archived:    https://github.com/api7/docs (enterprise 3.9.x, matches adc v0.30.x era)
  - Apache APISIX:   https://github.com/apache/apisix (release/3.18 branch, docs/en/latest)

Usage
  python download_official_docs.py

Requires outbound network access (Python stdlib only, no third-party deps).
On completion it writes MANIFEST.json with (source URL, local path, size, status).
"""

import json
import pathlib
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent

ADC = "https://raw.githubusercontent.com/api7/adc/main"
ADC_DOCS_ARCHIVE = "https://raw.githubusercontent.com/api7/docs/main/enterprise_versioned_docs/version-3.9.x"
APISIX = "https://raw.githubusercontent.com/apache/apisix/release/3.18"
APISIX_DOC = f"{APISIX}/docs/en/latest"

# (url, local relative path)
FILES = [
    # ---- ADC (api7/adc, main) ----
    (f"{ADC}/README.md", "adc/README.md"),
    (f"{ADC}/docs/README.md", "adc/docs-README.md"),
    (f"{ADC}/docs/reference/configuration.md", "adc/configuration.md"),
    (f"{ADC}/docs/reference/cli.md", "adc/cli.md"),
    (f"{ADC}/docs/reference/openapi-converter.md", "adc/openapi-converter.md"),
    (f"{ADC}/docs/guides/workflow.md", "adc/workflow.md"),
    (f"{ADC}/docs/guides/resource-ids.md", "adc/resource-ids.md"),
    (f"{ADC}/docs/guides/label-selector.md", "adc/label-selector.md"),
    (f"{ADC}/libs/backend-apisix/README.md", "adc/backend-apisix.md"),
    (f"{ADC}/schema.json", "adc/schema.json"),
    # Note: the archived ADC pages (docs.api7.ai/enterprise/reference/*, 3.9.x era) live in
    # the api7/docs repo, which is no longer publicly accessible (404). The live docs
    # above (api7/adc main branch) are the authoritative, maintained source instead.
    # ---- Apache APISIX core docs (release/3.18) ----
    (f"{APISIX_DOC}/admin-api.md", "apisix/admin-api.md"),
    (f"{APISIX_DOC}/getting-started/README.md", "apisix/getting-started.md"),
    (f"{APISIX_DOC}/getting-started/configure-routes.md", "apisix/configure-routes.md"),
    (f"{APISIX_DOC}/getting-started/load-balancing.md", "apisix/load-balancing.md"),
    (f"{APISIX_DOC}/getting-started/key-authentication.md", "apisix/key-authentication.md"),
    (f"{APISIX_DOC}/getting-started/rate-limiting.md", "apisix/rate-limiting.md"),
    (f"{APISIX_DOC}/deployment-modes.md", "apisix/deployment-modes.md"),
    (f"{APISIX_DOC}/profile.md", "apisix/profile.md"),
    (f"{APISIX_DOC}/customize-nginx-configuration.md", "apisix/customize-nginx-configuration.md"),
    (f"{APISIX_DOC}/certificate.md", "apisix/certificate.md"),
    (f"{APISIX_DOC}/apisix-variable.md", "apisix/apisix-variable.md"),
    (f"{APISIX_DOC}/FAQ.md", "apisix/FAQ.md"),
    # ---- APISIX terminology ----
    *[
        (f"{APISIX_DOC}/terminology/{name}.md", f"apisix/terminology/{name}.md")
        for name in [
            "api-gateway", "consumer", "consumer-group", "credential",
            "global-rule", "plugin", "plugin-config", "plugin-metadata",
            "route", "router", "script", "secret", "service", "upstream",
        ]
    ],
    # ---- APISIX plugin docs (commonly used) ----
    *[
        (f"{APISIX_DOC}/plugins/{name}.md", f"apisix/plugins/{name}.md")
        for name in [
            "ai-proxy", "basic-auth", "consumer-restriction", "cors", "gzip", "hmac-auth",
            "http-logger", "ip-restriction", "jwt-auth", "key-auth", "limit-conn",
            "limit-count", "limit-req", "log-rotate", "prometheus", "proxy-cache",
            "proxy-rewrite", "response-rewrite", "server-info", "traffic-split",
        ]
    ],
    # ---- APISIX gateway-side config.yaml (repo conf/) ----
    (f"{APISIX}/conf/config.yaml", "apisix/conf/config.yaml"),
    (f"{APISIX}/conf/config.yaml.example", "apisix/conf/config.yaml.example"),
]

UA = {"User-Agent": "Mozilla/5.0 (docs-mirror; +https://apisix.apache.org/)"}


def fetch(url: str, timeout: int = 60) -> bytes:
    last_err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as err:  # noqa: BLE001 - report and retry
            last_err = err
            time.sleep(1.5 * (attempt + 1))
    raise last_err


def main() -> int:
    results = []
    failed = []
    for url, rel in FILES:
        dest = HERE / rel
        try:
            data = fetch(url)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            results.append({"url": url, "local": rel, "size": len(data), "status": "ok"})
            print(f"  ok   {rel:55s} {len(data):>8d} B")
        except Exception as err:  # noqa: BLE001
            results.append({"url": url, "local": rel, "size": 0, "status": "error"})
            failed.append((rel, str(err)))
            print(f"  FAIL {rel:55s} {err}", file=sys.stderr)

    manifest = {
        "description": "Local mirror of official Apache APISIX + ADC documentation.",
        "sources": {
            "adc": "https://github.com/api7/adc (main)",
            "apisix-3.18": "https://github.com/apache/apisix (release/3.18, docs/en/latest)",
        },
        "files": results,
    }
    (HERE / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"\n{ok}/{len(results)} files downloaded. Manifest -> {HERE / 'MANIFEST.json'}")
    if failed:
        print("Failures:")
        for rel, err in failed:
            print(f"  - {rel}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
