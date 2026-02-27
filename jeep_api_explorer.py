#!/usr/bin/env python3
"""Jeep API Explorer

Attempts multiple API endpoints (beyond vehicles/status) and saves responses.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List

from JEEP_API_DIRECT import JeepAPIClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


DEFAULT_ENDPOINTS = [
    ("location", "/v2/accounts/{uid}/vehicles/{vin}/location"),
    ("notifications", "/v2/accounts/{uid}/vehicles/{vin}/notifications"),
    ("status_v2", "/v2/accounts/{uid}/vehicles/{vin}/status"),
    ("status_v1_remote", "/v1/accounts/{uid}/vehicles/{vin}/remote/status"),
    ("commands", "/v2/accounts/{uid}/vehicles/{vin}/commands"),
    ("services_v4", "/v4/accounts/{uid}/vehicles/{vin}/services"),
    ("vehicles_v4", "/v4/accounts/{uid}/vehicles"),
]


def safe_filename(s: str) -> str:
    return s.replace("/", "_").replace("?", "_").replace("=", "_")


def try_endpoints(client: JeepAPIClient, vin: str, endpoints: List[tuple], outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)

    results = {}
    for name, path_template in endpoints:
        url = client.CHANNELS_BASE + path_template.format(uid=client.uid, vin=vin)
        logger.info(f"Trying {name}: {url}")
        try:
            resp = client.session.get(
                url,
                headers=client._default_aws_headers() | {"content-type": "application/json"},
                auth=client.aws_auth,
                timeout=20,
            )
            status = resp.status_code
            text = resp.text
            try:
                data = resp.json()
            except Exception:
                data = None

            results[name] = {"url": url, "status": status, "json": data, "text_snippet": text[:1000]}

            # Save full response if JSON
            fname = outdir / f"explorer_{safe_filename(name)}.json"
            if data is not None:
                with open(fname, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved JSON to {fname}")
            else:
                fname = outdir / f"explorer_{safe_filename(name)}.txt"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(text)
                logger.info(f"Saved text to {fname}")

        except Exception as e:
            logger.error(f"Error calling {url}: {e}")
            results[name] = {"url": url, "error": str(e)}

    summary_file = outdir / "explorer_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Explorer finished. Summary: {summary_file}")


def main():
    parser = argparse.ArgumentParser(description="Jeep API Explorer")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--vin", required=True)
    parser.add_argument("--outdir", default="work_files/explorer_output")
    parser.add_argument("--endpoints", help="Comma-separated list of endpoint keys to try (overrides default)")
    args = parser.parse_args()

    client = JeepAPIClient(args.username, args.password)
    if not client.authenticate():
        logger.error("Auth failed")
        return

    endpoints = DEFAULT_ENDPOINTS
    if args.endpoints:
        keys = [k.strip() for k in args.endpoints.split(",")]
        endpoints = [e for e in DEFAULT_ENDPOINTS if e[0] in keys]
        if not endpoints:
            logger.error("No matching endpoints for provided keys")
            return

    try_endpoints(client, args.vin, endpoints, Path(args.outdir))


if __name__ == "__main__":
    main()
