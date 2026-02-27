#!/usr/bin/env python3
"""Try POST requests on endpoints that returned 404 for GET.

This sends a harmless test payload and saves responses under work_files/explorer_output/post_trials
"""

import json
import logging
from pathlib import Path

from pathlib import Path as _Path
import importlib.util as _importlib_util

# Dynamically load jeep_api_direct module to avoid import path issues
_mod_path = _Path(__file__).parent / "jeep_api_direct.py"
spec = _importlib_util.spec_from_file_location("jeep_api_direct", str(_mod_path))
jeep_mod = _importlib_util.module_from_spec(spec)
spec.loader.exec_module(jeep_mod)
JeepAPIClient = jeep_mod.JeepAPIClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TRIALS = [
    ("location", "/v2/accounts/{uid}/vehicles/{vin}/location"),
    ("notifications", "/v2/accounts/{uid}/vehicles/{vin}/notifications"),
    ("commands", "/v2/accounts/{uid}/vehicles/{vin}/commands"),
    ("services_v4", "/v4/accounts/{uid}/vehicles/{vin}/services"),
]

TEST_PAYLOAD = {"test": True}


def run(username: str, password: str, vin: str, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    client = JeepAPIClient(username, password)
    if not client.authenticate():
        logger.error("Authentication failed")
        return

    results = {}
    for name, path in TRIALS:
        url = client.CHANNELS_BASE + path.format(uid=client.uid, vin=vin)
        logger.info(f"POST trial {name}: {url}")
        try:
            resp = client.session.post(
                url,
                headers=client._default_aws_headers() | {"content-type": "application/json"},
                auth=client.aws_auth,
                json=TEST_PAYLOAD,
                timeout=20,
            )
            try:
                body = resp.json()
            except Exception:
                body = resp.text

            results[name] = {"url": url, "status": resp.status_code, "body": body}
            # Save per-endpoint
            with open(outdir / f"post_{name}.json", "w", encoding="utf-8") as f:
                json.dump(results[name], f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {outdir / f'post_{name}.json'}")

        except Exception as e:
            logger.error(f"Error for {name}: {e}")
            results[name] = {"url": url, "error": str(e)}

    summary = outdir / "post_trials_summary.json"
    with open(summary, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"POST trials finished. Summary: {summary}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--vin", required=True)
    parser.add_argument("--outdir", default="work_files/explorer_output/post_trials")
    args = parser.parse_args()
    run(args.username, args.password, args.vin, Path(args.outdir))
